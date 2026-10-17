import tempfile
import unittest
from pathlib import Path

from src.vision import extrair_documento


class TestesRF08(unittest.TestCase):

    def test_arquivo_inexistente(self):
        with self.assertRaises(FileNotFoundError):
            extrair_documento("arquivo_inexistente.pdf")

    def test_formato_invalido(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "documento.txt"
            arquivo.write_text("Teste", encoding="utf-8")

            with self.assertRaises(ValueError):
                extrair_documento(arquivo)

    def test_arquivo_sem_extensao_pdf(self):
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "documento.png"
            arquivo.write_bytes(b"imagem de teste")

            with self.assertRaises(ValueError):
                extrair_documento(arquivo)


if __name__ == "__main__":
    unittest.main()
