"""T15: reexecuta entradas textuais e OCR anteriores no fluxo do Desafio 2.

Sem API externa e sem modificar resultados originais. A revisão é registrada
em diretório temporário e não representa aprovação humana real.
"""
import json
import tempfile
import unittest
from pathlib import Path

from src.embeddings import Indice
from src.fluxo_desafio2 import executar, revisar

RAIZ = Path(__file__).resolve().parents[1]


class TesteT15RegressaoIntegrada(unittest.TestCase):
    def test_texto_e_ocr_ate_minuta_e_revisao(self):
        entradas = {
            "texto": RAIZ / "dados/originais/entrada_texto.txt",
            "ocr": RAIZ / "dados/processados/rf08_texto_corrigido.txt",
        }
        for origem, arquivo in entradas.items():
            with self.subTest(origem=origem):
                self.assertTrue(arquivo.is_file(), f"Entrada ausente: {arquivo}")
                texto = arquivo.read_text(encoding="utf-8-sig")
                self.assertTrue(texto.strip())
                with tempfile.TemporaryDirectory() as pasta:
                    pasta = Path(pasta)
                    indice = Indice(str(pasta / "indice.json"))
                    indice.indexar(sorted((RAIZ / "dados/acervo").glob("*.txt")))
                    resultado = executar(texto, indice, str(pasta / "auditoria.jsonl"))
                    self.assertTrue(resultado["ficha"]["resumo"])
                    self.assertTrue(resultado["ficha"]["estrutura"]["pedido"])
                    self.assertIn(resultado["rag"]["status"], (
                        "fundamentada (extrativa)", "sem evidência suficiente",
                        "conflito de fontes", "revisar",
                    ))
                    self.assertTrue(resultado["rag"]["resposta"])
                    self.assertIn(resultado["status"], ("pendente", "revisar"))
                    self.assertFalse(resultado["envio_automatico"])
                    registro = revisar(resultado, "revisar", "Conferência manual necessária no teste de regressão", str(pasta / "revisoes.jsonl"))
                    self.assertEqual(registro["id"], resultado["id"])
                    self.assertEqual(registro["decisao"], "revisar")
                    auditoria = [json.loads(x) for x in (pasta / "auditoria.jsonl").read_text(encoding="utf-8").splitlines()]
                    self.assertEqual(auditoria[0]["id"], resultado["id"])
                    revisoes = [json.loads(x) for x in (pasta / "revisoes.jsonl").read_text(encoding="utf-8").splitlines()]
                    self.assertEqual(revisoes[0]["id"], resultado["id"])


if __name__ == "__main__":
    unittest.main()
