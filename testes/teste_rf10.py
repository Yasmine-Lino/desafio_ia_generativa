import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from src import image_generation as rf10


class TestesRF10(unittest.TestCase):

    def test_arquivo_inexistente(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "inexistente.png"

            with self.assertRaises(FileNotFoundError):
                rf10.validar_png(caminho)

    def test_extensao_invalida(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "imagem.jpg"
            caminho.write_bytes(b"arquivo de teste")

            with self.assertRaises(ValueError):
                rf10.validar_png(caminho)

    def test_assinatura_png_invalida(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "imagem.png"
            caminho.write_bytes(b"nao e png")

            with self.assertRaises(ValueError):
                rf10.validar_png(caminho)

    def test_assinatura_png_valida(self):
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "imagem.png"
            caminho.write_bytes(
                b"\x89PNG\r\n\x1a\n" + b"conteudo ficticio"
            )

            self.assertTrue(rf10.validar_png(caminho))

    def test_prompt_inexistente(self):
        with tempfile.TemporaryDirectory() as pasta:
            base = Path(pasta)
            original = base / "original.png"
            revisada = base / "revisada.png"
            prompt = base / "prompt_inexistente.txt"
            metadados = base / "proveniencia.json"

            assinatura = b"\x89PNG\r\n\x1a\n"
            original.write_bytes(assinatura)
            revisada.write_bytes(assinatura)

            with patch.object(rf10, "ORIGINAL", original), \
                 patch.object(rf10, "REVISADA", revisada), \
                 patch.object(rf10, "PROMPT", prompt), \
                 patch.object(rf10, "METADADOS", metadados):

                with self.assertRaises(FileNotFoundError):
                    rf10.registrar_proveniencia()

    def test_nao_sobrescrever_aprovacao(self):
        with tempfile.TemporaryDirectory() as pasta:
            base = Path(pasta)
            original = base / "original.png"
            revisada = base / "revisada.png"
            metadados = base / "proveniencia.json"

            assinatura = b"\x89PNG\r\n\x1a\n"
            original.write_bytes(assinatura)
            revisada.write_bytes(assinatura)

            conteudo = {"aprovado": True}
            metadados.write_text(
                json.dumps(conteudo),
                encoding="utf-8"
            )

            with patch.object(rf10, "ORIGINAL", original), \
                 patch.object(rf10, "REVISADA", revisada), \
                 patch.object(rf10, "METADADOS", metadados):

                with self.assertRaises(FileExistsError):
                    rf10.registrar_proveniencia()

            resultado = json.loads(
                metadados.read_text(encoding="utf-8")
            )

            self.assertTrue(resultado["aprovado"])


if __name__ == "__main__":
    unittest.main()
