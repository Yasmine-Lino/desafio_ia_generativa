"""
Testes do RF14 - Extracao estruturada e validacao.

Cobre T01 (JSON valido com tipo incorreto e campo ausente) e
T02 (data impossivel ou dado nao presente no original).
"""

import json
import unittest
from datetime import date

from src.schemas import (
    Categoria,
    SolicitacaoContrato,
    TipoFalha,
    json_schema_versionado,
    validar_json_bruto,
    validar_pipeline,
    validar_regra_negocio,
)


class TestRF14Sintaxe(unittest.TestCase):
    """Camada 1: JSON sintaticamente valido."""

    def test_json_invalido_e_sintatico(self):
        r = validar_json_bruto('{"pedido": "x", }')
        self.assertFalse(r.ok)
        self.assertEqual(r.tipo_falha, TipoFalha.SINTATICA)

    def test_json_valido_e_ok(self):
        r = validar_json_bruto('{"pedido": "Quero informacoes sobre inscricao"}')
        self.assertTrue(r.ok)
        self.assertEqual(r.tipo_falha, TipoFalha.NENHUMA)


class TestRF14Esquema(unittest.TestCase):
    """Camada 2: conformidade ao esquema (T01)."""

    def _base(self):
        return {
            "pedido": "Solicito informacoes sobre inscricao no curso de Enfermagem",
            "protocolo": "2026-000142",
            "data": "2026-04-12",
            "solicitante": "Maria Fernanda Souza",
        }

    def test_t01_chave_extra_bloqueia(self):
        dados = self._base()
        dados["campo_inventado"] = True
        r = validar_pipeline(json.dumps(dados), json.dumps(dados))
        self.assertFalse(r.ok)
        self.assertEqual(r.tipo_falha, TipoFalha.ESQUEMA)
        self.assertIn("chave_extra", " ".join(r.detalhes))

    def test_t01_tipo_incorreto_bloqueia(self):
        dados = self._base()
        dados["protocolo"] = 2026000142  # int em vez de str
        r = validar_pipeline(json.dumps(dados), json.dumps(dados))
        self.assertFalse(r.ok)
        self.assertEqual(r.tipo_falha, TipoFalha.ESQUEMA)

    def test_t01_campo_ausente_bloqueia(self):
        dados = self._base()
        del dados["pedido"]  # obrigatorio
        r = validar_pipeline(json.dumps(dados), json.dumps(dados))
        self.assertFalse(r.ok)
        self.assertEqual(r.tipo_falha, TipoFalha.ESQUEMA)
        self.assertIn("campo_ausente", " ".join(r.detalhes))

    def test_protocolo_formato_invalido(self):
        dados = self._base()
        dados["protocolo"] = "ABC-123"
        r = validar_pipeline(json.dumps(dados), json.dumps(dados))
        self.assertFalse(r.ok)
        self.assertEqual(r.tipo_falha, TipoFalha.ESQUEMA)


class TestRF14RegraNegocio(unittest.TestCase):
    """Camada 3: coerencia com o original (T02)."""

    def test_t02_data_no_futuro_bloqueia(self):
        dados = {
            "pedido": "Solicito informacoes sobre inscricao no curso de Enfermagem",
            "protocolo": "2026-000142",
            "data": "2099-12-31",
            "solicitante": "Maria",
        }
        with self.assertRaises(Exception):
            SolicitacaoContrato(**dados)

    def test_t02_protocolo_nao_presente_no_original(self):
        obj = {
            "pedido": "Quero informacoes",
            "protocolo": "2026-999999",
            "data": "2026-04-12",
            "solicitante": "Maria",
        }
        original = "Solicito informacoes sobre inscricao. Protocolo 2026-000142."
        r = validar_regra_negocio(obj, original)
        self.assertFalse(r.ok)
        self.assertEqual(r.tipo_falha, TipoFalha.REGRA_NEGOCIO)
        self.assertTrue(any("protocolo_nao_encontrado" in d for d in r.detalhes))

    def test_t02_data_nao_presente_no_original(self):
        obj = {
            "pedido": "Quero informacoes",
            "protocolo": "2026-000142",
            "data": "2026-04-12",
            "solicitante": "Maria",
        }
        original = "Solicito informacoes. Protocolo 2026-000142. Sem data informada."
        r = validar_regra_negocio(obj, original)
        self.assertFalse(r.ok)
        self.assertTrue(any("data_nao_encontrada" in d for d in r.detalhes))

    def test_caso_valido_passa_todas_as_camadas(self):
        dados = {
            "pedido": "Solicito informacoes sobre inscricao no curso de Enfermagem da ETEC Cuiaba",
            "protocolo": "2026-000142",
            "data": "2026-04-12",
            "solicitante": "Maria Fernanda Souza",
            "categoria": "inscricao",
        }
        original = (
            "Protocolo: 2026-000142\nData: 12/04/2026\nSolicitante: Maria Fernanda Souza\n"
            "Solicito informacoes sobre inscricao no curso de Enfermagem da ETEC Cuiaba."
        )
        r = validar_pipeline(json.dumps(dados), original)
        self.assertTrue(r.ok, msg=r.mensagem)


class TestRF14SchemaVersionado(unittest.TestCase):
    """O contrato deve ser versionado e exportavel."""

    def test_schema_tem_versao(self):
        schema = json_schema_versionado()
        self.assertIn("versao", schema)
        self.assertIn("$id", schema)
        self.assertEqual(schema["versao"], "1.0.0")

    def test_campos_ausentes_representados_como_none(self):
        obj = SolicitacaoContrato(
            pedido="Quero informacoes sobre inscricao no curso de Enfermagem",
            protocolo=None,
            data=None,
            solicitante=None,
            campos_ausentes=["protocolo", "data", "solicitante"],
            necessidade_revisao=True,
        )
        self.assertIsNone(obj.protocolo)
        self.assertIsNone(obj.data)
        self.assertTrue(obj.necessidade_revisao)
        self.assertIn("protocolo", obj.campos_ausentes)


class TestRF14Gabarito(unittest.TestCase):
    """Compara com o gabarito real das 6 solicitacoes."""

    def test_sol05_incompleta_tem_campos_ausentes(self):
        with open("dados/gabaritos/solicitacoes.json", encoding="utf-8") as f:
            gab = json.load(f)
        sol05 = next(s for s in gab["solicitacoes"] if s["id"] == "sol05")
        self.assertEqual(sol05["tipo"], "incompleta")
        self.assertTrue(sol05["necessidade_revisao_esperada"])
        self.assertIn("protocolo", sol05["campos_ausentes_esperados"])
        self.assertIn("curso", sol05["campos_ausentes_esperados"])

    def test_sol06_ambigua_encaminha_revisao(self):
        with open("dados/gabaritos/solicitacoes.json", encoding="utf-8") as f:
            gab = json.load(f)
        sol06 = next(s for s in gab["solicitacoes"] if s["id"] == "sol06")
        self.assertEqual(sol06["tipo"], "ambigua")
        self.assertTrue(sol06["necessidade_revisao_esperada"])
        self.assertEqual(sol06["decisao_esperada"], "encaminhar_para_revisao_humana")


if __name__ == "__main__":
    unittest.main()