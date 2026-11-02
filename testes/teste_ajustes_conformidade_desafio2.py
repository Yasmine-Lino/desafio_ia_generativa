"""Regressões para limites de API, conflito real de fontes e auditoria."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

from src.embeddings import Indice
from src.rag import responder
from src.llm_client import consultar_llm, ErroLLM
from src.fluxo_desafio2 import executar


class AjustesConformidade(unittest.TestCase):
    def test_apenas_uma_repeticao_transitoria(self):
        resposta = Mock(status_code=503)
        with patch.dict(os.environ, {"GEMINI_API_KEY": "chave_ficticia"}), \
             patch("src.llm_client.requests.post", return_value=resposta) as post, \
             patch("src.llm_client.time.sleep"):
            with self.assertRaises(ErroLLM):
                consultar_llm([{"role": "user", "content": "Teste"}])
        self.assertEqual(post.call_count, 2)

    def test_conflito_q08_usa_documentos_reais(self):
        with tempfile.TemporaryDirectory() as pasta:
            indice = Indice(str(Path(pasta) / "indice.json"))
            indice.indexar(sorted(Path("dados/acervo").glob("*.txt")))
            resultado = responder("Qual prazo prevalece entre orientações contraditórias?", indice)
        self.assertEqual(resultado["status"], "conflito de fontes")
        self.assertEqual({x["documento"] for x in resultado["fontes"]},
                         {"prazo_matricula_v1.txt", "prazo_matricula_v2.txt"})

    def test_auditoria_tem_latencia_e_identificador(self):
        with tempfile.TemporaryDirectory() as pasta:
            indice = Indice(str(Path(pasta) / "indice.json"))
            indice.indexar(sorted(Path("dados/acervo").glob("*.txt")))
            log = Path(pasta) / "auditoria.jsonl"
            resultado = executar("Solicito matrícula, protocolo 2026-000142.", indice, str(log))
            registro = json.loads(log.read_text(encoding="utf-8").splitlines()[0])
        self.assertEqual(registro["id"], resultado["id"])
        self.assertGreaterEqual(registro["latencia_segundos"], 0)
        self.assertIn("modelo_indice", registro)


if __name__ == "__main__":
    unittest.main()
