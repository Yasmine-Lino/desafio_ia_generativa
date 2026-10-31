"""
Testes do RF21 - Provedor configuravel e auditoria.
"""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src.audit import mascarar, registrar_evento
from src.llm_client import (
    LLMAdaptadorGemini,
    LLMAdaptadorMock,
    criar_llm,
)


class TestFabricaProvedor(unittest.TestCase):
    def test_fabrica_mock(self):
        llm = criar_llm("mock")
        self.assertIsInstance(llm, LLMAdaptadorMock)

    def test_fabrica_gemini_sem_chave_falha(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError):
                criar_llm("gemini")

    def test_fabrica_provedor_invalido(self):
        with self.assertRaises(ValueError):
            criar_llm("openai_qualquer")


class TestAuditoriaMascaramento(unittest.TestCase):
    def test_mascarar_chaves(self):
        texto = "GEMINI_API_KEY=abc123 GEMINI_API_KEY=def456"
        mascarado = mascarar(texto)
        self.assertNotIn("abc123", mascarado)
        self.assertNotIn("def456", mascarado)
        self.assertIn("***", mascarado)

    def test_mascarar_cpf(self):
        mascarado = mascarar("CPF: 123.456.789-10")
        self.assertNotIn("123.456.789-10", mascarado)
        self.assertIn("***CPF***", mascarado)

    def test_registrar_evento_cria_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "teste_auditoria.jsonl"
            import src.audit as audit_mod
            original = audit_mod.DIR_LOGS
            audit_mod.DIR_LOGS = Path(tmp)
            try:
                id1 = registrar_evento("teste", {"texto": "texto limpo"}, arquivo_log="teste_auditoria.jsonl")
                self.assertTrue(id1)
                self.assertTrue(log_path.exists())
                linha = log_path.read_text(encoding="utf-8").strip()
                evento = json.loads(linha)
                self.assertEqual(evento["tipo"], "teste")
                self.assertEqual(evento["dados"]["texto"], "texto limpo")
            finally:
                audit_mod.DIR_LOGS = original

    def test_registrar_evento_mascara_segredo(self):
        with tempfile.TemporaryDirectory() as tmp:
            import src.audit as audit_mod
            original = audit_mod.DIR_LOGS
            audit_mod.DIR_LOGS = Path(tmp)
            try:
                registrar_evento("teste", {"texto": "GEMINI_API_KEY=chave_super_secreta_123"}, arquivo_log="mask.jsonl")
                linha = (Path(tmp) / "mask.jsonl").read_text(encoding="utf-8")
                self.assertNotIn("chave_super_secreta_123", linha)
                self.assertIn("***", linha)
            finally:
                audit_mod.DIR_LOGS = original


class TestT12TrocaProvedor(unittest.TestCase):
    def test_llm_mock_nao_mexe_no_indice(self):
        from src.embeddings import IndiceVetorial
        import uuid
        tmp = Path("indice/testes_tmp") / f"t12_{uuid.uuid4().hex[:6]}"
        tmp.mkdir(parents=True, exist_ok=True)
        idx = IndiceVetorial(dir_indice=tmp)
        n_antes = idx.contar()
        llm1 = criar_llm("mock")
        llm2 = criar_llm("mock")
        llm1.completar("Classifique")
        llm2.completar("Resuma")
        n_depois = idx.contar()
        self.assertEqual(n_antes, n_depois)

    def test_gemini_levanta_not_implemented_sem_rede(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": "fake"}):
            llm = criar_llm("gemini")
            self.assertIsInstance(llm, LLMAdaptadorGemini)
            with self.assertRaises(NotImplementedError):
                llm.completar("teste")

if __name__ == "__main__":
    unittest.main()