import os
import unittest
from unittest.mock import patch, Mock

from src.llm_client import consultar_llm, ErroLLM


MENSAGENS = [
    {"role": "system", "content": "Responda de forma objetiva."},
    {"role": "user", "content": "O que é um protocolo?"}
]


class TestesRF04(unittest.TestCase):

    def test_chave_ausente(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            with self.assertRaisesRegex(
                ErroLLM, "não encontrada"
            ):
                consultar_llm(MENSAGENS)

    @patch("src.llm_client.requests.post")
    def test_autenticacao_invalida(self, mock_post):
        mock_post.return_value.status_code = 401

        with patch.dict(
            os.environ, {"GEMINI_API_KEY": "chave_ficticia"}
        ):
            with self.assertRaisesRegex(
                ErroLLM, "Autenticação inválida"
            ):
                consultar_llm(MENSAGENS)

    @patch("src.llm_client.requests.post")
    def test_limite_requisicoes(self, mock_post):
        mock_post.return_value.status_code = 429

        with patch.dict(
            os.environ, {"GEMINI_API_KEY": "chave_ficticia"}
        ):
            with self.assertRaisesRegex(
                ErroLLM, "Limite de requisições"
            ):
                consultar_llm(MENSAGENS)

    @patch("src.llm_client.requests.post")
    def test_servico_indisponivel(self, mock_post):
        mock_post.return_value.status_code = 503

        with patch.dict(
            os.environ, {"GEMINI_API_KEY": "chave_ficticia"}
        ):
            with self.assertRaisesRegex(
                ErroLLM, "indisponível"
            ):
                consultar_llm(MENSAGENS)

    @patch("src.llm_client.requests.post")
    def test_resposta_vazia(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "candidates": []
        }

        with patch.dict(
            os.environ, {"GEMINI_API_KEY": "chave_ficticia"}
        ):
            with self.assertRaisesRegex(
                ErroLLM, "não retornou"
            ):
                consultar_llm(MENSAGENS)

    @patch("src.llm_client.requests.post")
    def test_resposta_valida(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "É um número de registro."}
                        ]
                    }
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 20,
                "candidatesTokenCount": 10,
                "totalTokenCount": 35
            }
        }

        with patch.dict(
            os.environ, {"GEMINI_API_KEY": "chave_ficticia"}
        ):
            resultado = consultar_llm(MENSAGENS)

        self.assertEqual(
            resultado["resposta"],
            "É um número de registro."
        )
        self.assertEqual(resultado["tokens_entrada"], 20)
        self.assertEqual(resultado["tokens_saida"], 10)
        self.assertEqual(resultado["tokens_total"], 35)
        self.assertIsNone(resultado["custo_estimado_usd"])


if __name__ == "__main__":
    unittest.main()
