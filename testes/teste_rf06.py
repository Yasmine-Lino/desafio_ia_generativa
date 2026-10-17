import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from src.audio import transcrever_audio


class TestesRF06(unittest.TestCase):

    def test_chave_ausente(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": ""}):
            with self.assertRaisesRegex(ValueError, "não encontrada"):
                transcrever_audio("arquivo.mp3")

    def test_arquivo_inexistente(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "teste"}):
            with self.assertRaises(FileNotFoundError):
                transcrever_audio("arquivo_inexistente.mp3")

    def test_formato_invalido(self):
        with TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "teste.txt"
            arquivo.write_text("teste", encoding="utf-8")

            with patch.dict(os.environ, {"GEMINI_API_KEY": "teste"}):
                with self.assertRaisesRegex(ValueError, "formato MP3"):
                    transcrever_audio(arquivo)

    @patch("src.audio.requests.post")
    def test_transcricao_valida(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": "Solicito informações sobre matrícula."}]
                    }
                }
            ],
            "usageMetadata": {
                "promptTokenCount": 50,
                "candidatesTokenCount": 10,
                "totalTokenCount": 60
            }
        }

        with TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "teste.mp3"
            arquivo.write_bytes(b"audio ficticio")

            with patch.dict(os.environ, {"GEMINI_API_KEY": "teste"}):
                resultado = transcrever_audio(arquivo)

        self.assertEqual(
            resultado["transcricao"],
            "Solicito informações sobre matrícula."
        )
        self.assertEqual(resultado["tokens_total"], 60)
        self.assertTrue(resultado["revisao_humana"])

    @patch("src.audio.requests.post")
    def test_resposta_vazia(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "candidates": []
        }

        with TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "teste.mp3"
            arquivo.write_bytes(b"audio ficticio")

            with patch.dict(os.environ, {"GEMINI_API_KEY": "teste"}):
                with self.assertRaisesRegex(RuntimeError, "não retornou"):
                    transcrever_audio(arquivo)


    @patch("src.audio.requests.post")
    def test_resposta_audio_transcription(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "audioTranscription": {
                                    "text": "Gostaria de informações sobre matrícula."
                                }
                            }
                        ]
                    },
                    "finishReason": "STOP"
                }
            ]
        }

        with TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "teste.mp3"
            arquivo.write_bytes(b"audio ficticio")

            with patch.dict(os.environ, {"GEMINI_API_KEY": "teste"}):
                resultado = transcrever_audio(arquivo)

        self.assertEqual(
            resultado["transcricao"],
            "Gostaria de informações sobre matrícula."
        )

if __name__ == "__main__":
    unittest.main()
