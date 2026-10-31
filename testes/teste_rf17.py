"""
Testes do RF17 - Embeddings e indice vetorial.

Cobre T06 (reinicio e reindexacao do mesmo acervo: indice reutilizado,
sem duplicacao) e valida metadados completos por vetor.

Nota Windows: o Chroma mantem arquivos do indice abertos; por isso os
testes usam pastas temporarias manuais em indice/testes_tmp/ (ignoradas
pelo git) em vez de TemporaryDirectory, que falharia no cleanup.
"""

import shutil
import unittest
import uuid
from pathlib import Path

from src.embeddings import IndiceVetorial, MotorEmbedding
from src.ingestion import indexar_acervo, preparar_chunks

DIR_TMP_BASE = Path("indice/testes_tmp")


def _tmp_dir() -> Path:
    """Cria pasta temporaria unica em indice/testes_tmp/ (nao apagada pelo SO)."""
    DIR_TMP_BASE.mkdir(parents=True, exist_ok=True)
    d = DIR_TMP_BASE / f"t_{uuid.uuid4().hex[:8]}"
    d.mkdir()
    return d


class TestModeloEmbedding(unittest.TestCase):
    def test_modelo_tem_dimensao(self):
        motor = MotorEmbedding.obter()
        self.assertEqual(motor.dimensao, 384)
        self.assertIn("multilingual", motor.modelo_nome)

    def test_embeddings_normalizados(self):
        motor = MotorEmbedding.obter()
        vetores = motor.gerar(["teste a", "teste b"])
        self.assertEqual(len(vetores), 2)
        self.assertEqual(len(vetores[0]), 384)


class TestChunkingMetadados(unittest.TestCase):
    def test_chunk_id_unico_entre_txt_e_pdf(self):
        """txt e pdf do mesmo doc nao podem colidir (bug que corrigimos)."""
        arq_txt = Path("dados/acervo/doc01_edital_006_2026.txt")
        arq_pdf = Path("dados/acervo/doc01_edital_006_2026.pdf")
        if not arq_pdf.exists():
            self.skipTest("PDF nao encontrado")
        chunks_txt = preparar_chunks(arq_txt)
        chunks_pdf = preparar_chunks(arq_pdf)
        ids_txt = {c["id"] for c in chunks_txt}
        ids_pdf = {c["id"] for c in chunks_pdf}
        self.assertEqual(ids_txt & ids_pdf, set(), "chunk_ids colidiram entre txt e pdf")
        self.assertTrue(all("::txt::" in i for i in ids_txt))
        self.assertTrue(all("::pdf::" in i for i in ids_pdf))

    def test_metadados_completos_por_chunk(self):
        chunks = preparar_chunks(Path("dados/acervo/doc05_orientacao_cotas.txt"))
        self.assertGreater(len(chunks), 0)
        meta = chunks[0]["metadados"]
        for campo in ["doc_id", "titulo", "versao", "arquivo", "formato",
                      "hash_arquivo", "chunk_id", "hash_chunk", "secao"]:
            self.assertIn(campo, meta, msg=f"campo ausente: {campo}")
        self.assertEqual(meta["doc_id"], "DOC05")
        self.assertEqual(meta["formato"], "txt")

    def test_chunkar_respeita_tamanho(self):
        from src.ingestion import chunkar
        texto = "paragrafo " * 500
        pedacos = chunkar(texto, tamanho=200, sobreposicao=50)
        for p in pedacos:
            self.assertLessEqual(len(p), 200 + 5)

    def test_sobreposicao_maior_que_tamanho_falha(self):
        from src.ingestion import chunkar
        with self.assertRaises(ValueError):
            chunkar("texto", tamanho=100, sobreposicao=200)


class TestT06ReinicioEReindexacao(unittest.TestCase):
    """T06: indice reutilizado apos reinicio e sem duplicacao."""

    def test_t06_reindexar_sem_duplicar(self):
        tmp = _tmp_dir()
        dir_indice = tmp / "indice"
        # Primeira indexacao
        idx1 = IndiceVetorial(dir_indice=dir_indice)
        r1 = indexar_acervo(indice=idx1)
        self.assertGreater(r1["total_chunks"], 0)
        self.assertEqual(r1["inseridos"], r1["total_chunks"])
        self.assertEqual(r1["ignorados"], 0)
        n1 = idx1.contar()

        # Segunda indexacao (simula reinicio: novo IndiceVetorial)
        idx2 = IndiceVetorial(dir_indice=dir_indice)
        self.assertEqual(idx2.contar(), n1, "indice nao foi reutilizado")
        r2 = indexar_acervo(indice=idx2)
        self.assertEqual(r2["inseridos"], 0)
        self.assertEqual(r2["ignorados"], r1["total_chunks"])
        self.assertEqual(idx2.contar(), n1, "duplicacao detectada")

    def test_busca_retorna_metadados_rastreaveis(self):
        tmp = _tmp_dir()
        idx = IndiceVetorial(dir_indice=tmp / "indice")
        indexar_acervo(indice=idx)
        resultados = idx.buscar("prazo de inscricao", top_k=3)
        self.assertEqual(len(resultados), 3)
        for r in resultados:
            self.assertIn("chunk_id", r)
            self.assertIn("doc_id", r["metadados"])
            self.assertIn("versao", r["metadados"])
            self.assertIn("hash_arquivo", r["metadados"])
            self.assertIn("distancia", r)
            self.assertIn("similaridade", r)
            self.assertIn("sentido", r)


class TestRemocaoDocumento(unittest.TestCase):
    """Base para RF24: remover documento deve retirar seus chunks."""

    def test_remover_doc_retira_chunks(self):
        tmp = _tmp_dir()
        idx = IndiceVetorial(dir_indice=tmp / "indice")
        indexar_acervo(indice=idx)
        antes = idx.contar()
        removidos = idx.remover_documento("DOC05")
        self.assertGreater(removidos, 0)
        self.assertLess(idx.contar(), antes)
        resultados = idx.buscar("heteroidentificacao cota L1", top_k=10)
        for r in resultados:
            self.assertNotEqual(r["metadados"]["doc_id"], "DOC05")


if __name__ == "__main__":
    unittest.main()