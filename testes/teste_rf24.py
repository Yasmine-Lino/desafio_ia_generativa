"""
Testes do RF24 - Privacidade e revisao humana.

Cobre T11 (aprovacao/rejeicao) e T14 (exclusao de documento).
"""

import json
import unittest
from pathlib import Path

from src.audit import DIR_LOGS
from src.privacidade import excluir_documento, registrar_revisao_humana
from src.embeddings import IndiceVetorial


class TestT14Exclusao(unittest.TestCase):
    def test_excluir_documento_remove_do_indice(self):
        import uuid

        tmp = Path("indice/testes_tmp") / f"t14_{uuid.uuid4().hex[:6]}"
        tmp.mkdir(parents=True, exist_ok=True)
        idx = IndiceVetorial(dir_indice=tmp)
        
        # Indexa um pequeno chunk falso
        idx.indexar_chunks([
            {"id": "DOC99::txt::1", "texto": "Teste", "metadados": {"doc_id": "DOC99"}}
        ])
        
        self.assertEqual(idx.contar(), 1)
        
        # Exclui e verifica
        res = excluir_documento("DOC99", idx)
        self.assertEqual(res["doc_id"], "DOC99")
        self.assertEqual(res["chunks_removidos"], 1)
        self.assertEqual(idx.contar(), 0)

    def test_exclusao_registra_auditoria(self):
        import uuid
        tmp = Path("indice/testes_tmp") / f"t14_log_{uuid.uuid4().hex[:6]}"
        tmp.mkdir(parents=True, exist_ok=True)
        idx = IndiceVetorial(dir_indice=tmp)
        
        log_path = DIR_LOGS / "revisoes.jsonl"
        excluir_documento("DOC99", idx)
        self.assertTrue(log_path.exists())


class TestT11RevisaoHumana(unittest.TestCase):
    def test_registrar_aprovacao(self):
        id_log = registrar_revisao_humana(
            texto_solicitacao="Solicito inscricao no curso de Enfermagem",
            status="aprovada",
            justificativa="Dados conferidos",
            participacao_ia=True,
        )
        self.assertTrue(id_log)
        
        log_path = DIR_LOGS / "revisoes.jsonl"
        self.assertTrue(log_path.exists())
        
        # Verifica o ultimo evento gravado
        linhas = log_path.read_text(encoding="utf-8").strip().split("\n")
        ultimo = json.loads(linhas[-1])
        self.assertEqual(ultimo["dados"]["status"], "aprovada")
        self.assertTrue(ultimo["dados"]["participacao_ia"])

    def test_registrar_rejeicao_exige_justificativa(self):
        with self.assertRaises(ValueError):
            registrar_revisao_humana("Texto", "rejeitada", justificativa="")

    def test_registrar_revisao_exige_justificativa(self):
        with self.assertRaises(ValueError):
            registrar_revisao_humana("Texto", "revisao", justificativa="")

    def test_registrar_rejeicao_valida(self):
        id_log = registrar_revisao_humana(
            texto_solicitacao="Texto",
            status="rejeitada",
            justificativa="Informacao incorreta",
        )
        self.assertTrue(id_log)

if __name__ == "__main__":
    unittest.main()