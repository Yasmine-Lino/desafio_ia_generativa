import unittest

from src.sintese_voz import preparar_texto


class TestesRF07(unittest.TestCase):

    def test_minuta_sem_aprovacao(self):
        with self.assertRaises(ValueError):
            preparar_texto("Resposta institucional.", False)

    def test_minuta_vazia(self):
        with self.assertRaises(ValueError):
            preparar_texto("   ", True)

    def test_minuta_aprovada(self):
        texto = "Sua solicitação foi recebida."
        resultado = preparar_texto(texto, True)
        self.assertEqual(resultado, texto)

    def test_campo_nao_localizado(self):
        texto = "Prazo: não localizado."
        resultado = preparar_texto(texto, True)

        self.assertIn("Atenção:", resultado)
        self.assertIn(texto, resultado)

    def test_sem_aviso_desnecessario(self):
        texto = "O documento está disponível."
        resultado = preparar_texto(texto, True)

        self.assertNotIn("Atenção:", resultado)


if __name__ == "__main__":
    unittest.main()
