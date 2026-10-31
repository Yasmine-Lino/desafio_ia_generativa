"""
Testes do RF18 - Chunking comparado.
"""

import unittest

from src.rag import comparar_chunkings


class TestRF18Chunking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resultado = comparar_chunkings(top_k=5)

    def test_duas_configuracoes_avaliadas(self):
        self.assertEqual(len(self.resultado["resultados"]), 2)
        configs = {tuple(r["config"].items()) for r in self.resultado["resultados"]}
        self.assertEqual(len(configs), 2)

    def test_cinco_perguntas_por_config(self):
        for r in self.resultado["resultados"]:
            self.assertEqual(r["total"], 5)

    def test_taxa_acerto_valida(self):
        for r in self.resultado["resultados"]:
            self.assertGreaterEqual(r["taxa_acerto"], 0.0)
            self.assertLessEqual(r["taxa_acerto"], 1.0)

    def test_configuracao_escolhida_justificada(self):
        self.assertIn("escolhida", self.resultado)
        self.assertIn("justificativa", self.resultado)
        self.assertTrue(self.resultado["justificativa"])

    def test_detalhes_por_pergunta(self):
        for d in self.resultado["detalhes_por_config"]:
            self.assertEqual(len(d["detalhes"]), 5)
            for item in d["detalhes"]:
                self.assertIn("acertou", item)
                self.assertIn("top_k_ids", item)


if __name__ == "__main__":
    unittest.main()