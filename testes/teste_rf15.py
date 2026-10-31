"""
Testes do RF15 - Sumarizacao, classificacao e extracao de entidades.

Cobre T03 (seis solicitacoes com gabarito: resumo fiel, categoria e
entidades avaliados). Usa LLM falso para rodar sem chamar API.
"""

import json
import unittest
from typing import Any

from src.nlp import (
    MAX_PALAVRAS_RESUMO,
    FichaCompreensao,
    avaliar_contra_gabarito,
    carregar_gabarito,
    carregar_solicitacao,
    classificar,
    extrair_entidades,
    gerar_ficha,
    resumir,
)
from src.schemas import Categoria, Entidade


class FakeLLM:
    """LLM falso: responde de forma deterministica por tipo de prompt."""

    def __init__(self, respostas: dict[str, str] | None = None):
        self.respostas = respostas or {}
        self.chamadas: list[str] = []

    def completar(self, prompt: str, **kwargs: Any) -> str:
        self.chamadas.append(prompt)
        if "Resuma" in prompt:
            return self.respostas.get(
                "resumo",
                "Cidadao solicita informacoes sobre inscricao no curso de Enfermagem da ETEC Cuiaba, cota L2, documentos e prazo.",
            )
        if "Classifique" in prompt:
            return self.respostas.get("categoria", "inscricao")
        return self.respostas.get(
            "entidades",
            '{"entidades": [{"tipo": "curso", "valor": "Tecnico em Enfermagem", "origem": "literal"}, '
            '{"tipo": "cota", "valor": "L2", "origem": "literal"}, '
            '{"tipo": "orgao", "valor": "ETEC Cuiaba", "origem": "literal"}], "ausentes": []}',
        )


class FakeLLMAmbiguo(FakeLLM):
    def completar(self, prompt: str, **kwargs: Any) -> str:
        self.chamadas.append(prompt)
        if "Resuma" in prompt:
            return "Cidadao pergunta se vale a pena se inscrever. Sem pedido claro."
        if "Classifique" in prompt:
            return "revisao"
        return '{"entidades": [], "ausentes": ["curso", "pedido_claro"]}'


class TestResumo(unittest.TestCase):
    def test_resumo_truncado_em_100_palavras(self):
        texto_longo = "palavra " * 300
        llm = FakeLLM({"resumo": texto_longo})
        r = resumir("x", llm, max_palavras=MAX_PALAVRAS_RESUMO)
        self.assertLessEqual(len(r.split()), MAX_PALAVRAS_RESUMO)

    def test_resumo_curto_nao_trunca(self):
        llm = FakeLLM({"resumo": "Resumo curto e fiel."})
        r = resumir("x", llm)
        self.assertEqual(r, "Resumo curto e fiel.")


class TestClassificacao(unittest.TestCase):
    def test_categoria_valida(self):
        llm = FakeLLM({"categoria": "matricula"})
        self.assertEqual(classificar("x", llm), "matricula")

    def test_categoria_fora_do_enum_vira_revisao(self):
        llm = FakeLLM({"categoria": "reclamacao_qualquer"})
        self.assertEqual(classificar("x", llm), Categoria.REVISAO.value)

    def test_categoria_com_pontuacao_normaliza(self):
        llm = FakeLLM({"categoria": "Inscricao."})
        self.assertEqual(classificar("x", llm), "inscricao")


class TestEntidades(unittest.TestCase):
    def test_extrai_entidades_com_origem(self):
        llm = FakeLLM()
        entidades, ausentes = extrair_entidades("x", llm)
        self.assertEqual(len(entidades), 3)
        self.assertEqual(entidades[0].tipo, "curso")
        self.assertEqual(entidades[0].origem, "literal")
        self.assertEqual(ausentes, [])

    def test_resposta_invalida_nao_quebra(self):
        llm = FakeLLM({"entidades": "isso nao e json"})
        entidades, ausentes = extrair_entidades("x", llm)
        self.assertEqual(entidades, [])
        self.assertIn("resposta_llm_invalida", ausentes)

    def test_campos_ausentes_acionam_revisao(self):
        llm = FakeLLMAmbiguo()
        ficha = gerar_ficha("x", llm)
        self.assertTrue(ficha.necessidade_revisao)
        self.assertIn("curso", ficha.campos_ausentes)


class TestFichaCompleta(unittest.TestCase):
    def test_pipeline_sol01(self):
        llm = FakeLLM()
        texto = carregar_solicitacao("sol01")
        ficha = gerar_ficha(texto, llm)
        self.assertEqual(ficha.categoria, "inscricao")
        self.assertFalse(ficha.necessidade_revisao)
        self.assertGreater(len(ficha.entidades), 0)
        self.assertEqual(len(llm.chamadas), 3)  # resumo, categoria, entidades

    def test_pipeline_sol06_ambigua(self):
        llm = FakeLLMAmbiguo()
        texto = carregar_solicitacao("sol06")
        ficha = gerar_ficha(texto, llm)
        self.assertEqual(ficha.categoria, "revisao")
        self.assertTrue(ficha.necessidade_revisao)


class TestAvaliacaoGabarito(unittest.TestCase):
    """T03: seis solicitacoes conferidas contra o gabarito."""

    def _fichas_perfeitas(self):
        """Fichas que reproduzem exatamente o gabarito (baseline)."""
        gab = carregar_gabarito()
        fichas: dict[str, FichaCompreensao] = {}
        for sol in gab["solicitacoes"]:
            entidades = []
            for tipo, valores in sol["entidades_esperadas"].items():
                for v in valores:
                    entidades.append(Entidade(tipo=tipo, valor=v, origem="literal"))
            fichas[sol["id"]] = FichaCompreensao(
                resumo=" ".join(sol["resumo_fatos_essenciais"]),
                categoria=sol["categoria_esperada"],
                entidades=entidades,
                campos_ausentes=list(sol["campos_ausentes_esperados"]),
                necessidade_revisao=sol["necessidade_revisao_esperada"],
            )
        return gab, fichas

    def test_gabarito_perfeito_acuracia_100(self):
        gab, fichas = self._fichas_perfeitas()
        res = avaliar_contra_gabarito(fichas, gab)
        self.assertEqual(res.total, 6)
        self.assertEqual(res.acertos_categoria, 6)
        self.assertEqual(res.acuracia_categoria, 1.0)
        self.assertEqual(res.omissoes_entidade, 0)
        self.assertEqual(res.entidades_incorretas, 0)
        self.assertEqual(res.fatos_sem_suporte, 0)

    def test_categoria_errada_reduz_acuracia(self):
        gab, fichas = self._fichas_perfeitas()
        fichas["sol01"].categoria = "revisao"
        res = avaliar_contra_gabarito(fichas, gab)
        self.assertEqual(res.acertos_categoria, 5)
        self.assertAlmostEqual(res.acuracia_categoria, 5 / 6, places=4)

    def test_entidade_omitida_e_contada(self):
        gab, fichas = self._fichas_perfeitas()
        fichas["sol01"].entidades = []
        res = avaliar_contra_gabarito(fichas, gab)
        self.assertGreater(res.omissoes_entidade, 0)

    def test_entidade_inventada_e_contada(self):
        gab, fichas = self._fichas_perfeitas()
        fichas["sol01"].entidades.append(
            Entidade(tipo="curso", valor="Curso Inventado", origem="literal")
        )
        res = avaliar_contra_gabarito(fichas, gab)
        self.assertGreater(res.entidades_incorretas, 0)

    def test_acuracia_zero_sem_fichas(self):
        gab = carregar_gabarito()
        res = avaliar_contra_gabarito({}, gab)
        self.assertEqual(res.total, 0)
        self.assertEqual(res.acuracia_categoria, 0.0)


if __name__ == "__main__":
    unittest.main()