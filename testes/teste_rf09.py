import unittest
from unittest.mock import patch

from src.minuta import preparar_dados, gerar_minuta


class TestesRF09(unittest.TestCase):

    def test_preparar_dados_remove_informacoes_pessoais(self):
        dados = {
            "protocolo": "2026-000142",
            "assunto": "Matrícula",
            "cpf": "123.456.789-00",
            "rg": "1234567-8",
            "texto_original": "Texto com dados pessoais"
        }

        resultado = preparar_dados(dados)

        self.assertEqual(resultado["protocolo"], "2026-000142")
        self.assertNotIn("cpf", resultado)
        self.assertNotIn("rg", resultado)
        self.assertNotIn("texto_original", resultado)

    def test_documentos_pendentes_nao_localizados(self):
        resultado = preparar_dados({
            "protocolo": "2026-000142"
        })

        self.assertEqual(
            resultado["documentos_pendentes"],
            "não localizado"
        )

    def test_dados_invalidos(self):
        with self.assertRaises(ValueError):
            gerar_minuta("texto inválido", "Prompt válido")

    def test_prompt_vazio(self):
        with self.assertRaises(ValueError):
            gerar_minuta({"assunto": "Matrícula"}, "")

    @patch("src.minuta.consultar_llm")
    def test_geracao_valida(self, mock_llm):
        mock_llm.return_value = {
            "resposta": "MINUTA — PENDENTE DE REVISÃO HUMANA",
            "modelo": "modelo-teste",
            "provedor": "gemini",
            "tempo_segundos": 0.1,
            "tokens_total": 20
        }

        texto, resposta = gerar_minuta(
            {"assunto": "Matrícula"},
            "Elabore uma minuta institucional."
        )

        self.assertIn("MINUTA", texto)
        self.assertEqual(resposta["modelo"], "modelo-teste")
        mock_llm.assert_called_once()

    @patch("src.minuta.consultar_llm")
    def test_resposta_vazia(self, mock_llm):
        mock_llm.return_value = {"resposta": "   "}

        with self.assertRaises(ValueError):
            gerar_minuta(
                {"assunto": "Matrícula"},
                "Elabore uma minuta."
            )


if __name__ == "__main__":
    unittest.main()
