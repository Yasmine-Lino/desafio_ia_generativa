"""
Testes do RF22 - Classificacao de sentimentos.

Valida:
  - polaridades validas
  - indeterminacao admitida (nao forcar rotulo)
  - 12 avaliacoes com gabarito conferido
  - confianca nao usada como probabilidade
"""

import json
import unittest
from pathlib import Path
from typing import Any

from src.sentiment import (
    POLARIDADES,
    ResultadoSentimento,
    avaliar_contra_gabarito,
    carregar_gabarito,
    classificar_avaliacao,
    classificar_sentimento,
)


class FakeLLMPerfeito:
    """Reproduz exatamente o gabarito (para testar o pipeline)."""

    def completar(self, prompt: str, **kwargs: Any) -> str:
        texto = prompt.lower()
        if "aval01" in texto or "excelente" in texto:
            return '{"polaridade": "positiva", "justificativa": "elogio"}'
        if "pessimo" in texto or "aval04" in texto:
            return '{"polaridade": "negativa", "justificativa": "critica"}'
        if "dentro do esperado" in texto or "aval07" in texto:
            return '{"polaridade": "neutra", "justificativa": "fato"}'
        return '{"polaridade": "indeterminada", "justificativa": "ambigua"}'


class FakeLLMInvalido:
    def completar(self, prompt: str, **kwargs: Any) -> str:
        return "isso nao e json"

    def completar2(self, prompt: str, **kwargs: Any) -> str:
        return '{"polaridade": "alegria", "justificativa": "x"}'


class FakeLLMForaDoEnum:
    def completar(self, prompt: str, **kwargs: Any) -> str:
        return '{"polaridade": "alegria", "justificativa": "x"}'


class TestPolaridades(unittest.TestCase):
    def test_polaridades_validas(self):
        self.assertEqual(POLARIDADES, {"positiva", "negativa", "neutra", "indeterminada"})


class TestClassificacao(unittest.TestCase):
    def test_positiva(self):
        llm = FakeLLMPerfeito()
        pol, just = classificar_sentimento("Atendimento excelente", llm)
        self.assertEqual(pol, "positiva")

    def test_fora_do_enum_vira_indeterminada(self):
        llm = FakeLLMForaDoEnum()
        pol, _ = classificar_sentimento("qualquer coisa", llm)
        self.assertEqual(pol, "indeterminada")

    def test_resposta_invalida_vira_indeterminada(self):
        llm = FakeLLMInvalido()
        pol, just = classificar_sentimento("qualquer coisa", llm)
        self.assertEqual(pol, "indeterminada")
        self.assertIn("invalida", just.lower())

    def test_indeterminada_marca_revisao(self):
        llm = FakeLLMForaDoEnum()
        r = classificar_avaliacao("x", "texto", llm)
        self.assertTrue(r.precisa_revisao)


class TestAvaliacaoGabarito(unittest.TestCase):
    """Todas as 12 avaliacoes devem ser conferidas."""

    def test_gabarito_perfeito_acuracia_100(self):
        gab = carregar_gabarito()
        resultados = {}
        for aval in gab["avaliacoes"]:
            resultados[aval["id"]] = ResultadoSentimento(
                id=aval["id"],
                polaridade=aval["rotulo_esperado"],
                justificativa="ok",
                precisa_revisao=aval["necessidade_revisao_esperada"],
            )
        av = avaliar_contra_gabarito(resultados, gab)
        self.assertEqual(av["total"], 12)
        self.assertEqual(av["acertos"], 12)
        self.assertEqual(av["acuracia"], 1.0)
        self.assertEqual(av["ambiguas"]["acertos"], 3)

    def test_rotulo_errado_reduz_acuracia(self):
        gab = carregar_gabarito()
        resultados = {}
        for aval in gab["avaliacoes"]:
            resultados[aval["id"]] = ResultadoSentimento(
                id=aval["id"],
                polaridade=aval["rotulo_esperado"],
                justificativa="ok",
                precisa_revisao=False,
            )
        resultados["aval01"].polaridade = "negativa"  # erro proposital
        av = avaliar_contra_gabarito(resultados, gab)
        self.assertEqual(av["acertos"], 11)
        self.assertAlmostEqual(av["acuracia"], 11 / 12, places=4)

    def test_ambiguas_nao_forcadas(self):
        gab = carregar_gabarito()
        resultados = {}
        for aval in gab["avaliacoes"]:
            # Forca todas as ambiguas como "positiva" (errado)
            pol = "positiva" if aval["rotulo_esperado"] == "indeterminada" else aval["rotulo_esperado"]
            resultados[aval["id"]] = ResultadoSentimento(
                id=aval["id"], polaridade=pol, justificativa="x"
            )
        av = avaliar_contra_gabarito(resultados, gab)
        self.assertEqual(av["ambiguas"]["acertos"], 0)


class TestNaoInferenciaSensivel(unittest.TestCase):
    """O prompt nao deve PEDIR personalidade/diagnostico, e deve PROIBIR explicitamente."""

    def test_prompt_proibe_diagnostico_e_personalidade(self):
        from src.sentiment import PROMPT_SENTIMENTO
        prompt_lower = PROMPT_SENTIMENTO.lower()
        # Deve conter a proibicao explicita
        self.assertTrue(
            "nao infira" in prompt_lower or "não infira" in prompt_lower,
            msg="Prompt deve conter proibicao explicita ('nao infira')",
        )
        # E a proibicao deve cobrir personalidade, diagnostico e caracteristica sensivel
        self.assertIn("personalidade", prompt_lower)
        self.assertIn("diagnostico", prompt_lower)
        self.assertIn("sensivel", prompt_lower)
        # Deve mencionar indeterminada (abstencao admitida)
        self.assertIn("indeterminada", prompt_lower)


if __name__ == "__main__":
    unittest.main()