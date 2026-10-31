"""
Testes do RF19 - RAG com abstencao e conflito.

Cobre T08 (respondiveis), T09 (sem resposta) e T10 (contraditoria).
"""

import unittest

from src.rag import StatusResposta, avaliar_rag


class TestRF19RAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resultado = avaliar_rag()

    def test_t08_respondiveis_tem_evidencia(self):
        r = self.resultado["respondiveis"]
        self.assertEqual(r["total"], 5)
        # exigimos pelo menos 4 de 5 (limite do modelo de embedding local)
        self.assertGreaterEqual(r["acertos"], 4)

    def test_t09_abstencao_nas_sem_resposta(self):
        r = self.resultado["sem_resposta"]
        self.assertEqual(r["total"], 2)
        self.assertEqual(r["abstencoes_corretas"], 2)

    def test_t10_conflito_apresentado(self):
        self.assertTrue(self.resultado["contraditoria"]["conflito_apresentado"])

    def test_detalhes_por_pergunta(self):
        self.assertEqual(len(self.resultado["detalhes"]), 8)
        for d in self.resultado["detalhes"]:
            self.assertIn("status", d)
            self.assertIn(d["status"], {
                StatusResposta.FUNDAMENTADA,
                StatusResposta.SEM_EVIDENCIA,
                StatusResposta.CONFLITO,
            })


if __name__ == "__main__":
    unittest.main()