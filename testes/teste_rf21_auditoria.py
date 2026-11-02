from pathlib import Path
import json
import tempfile
from unittest.mock import patch

import pytest

from src.fluxo_desafio2 import executar_provedor


def test_rf21_registra_sucesso_custo_e_latencia():
    with tempfile.TemporaryDirectory() as pasta:
        log = Path(pasta) / "provedores.jsonl"

        resposta = {
            "texto": "Resposta de teste",
            "provedor": "openai",
            "modelo": "modelo-teste",
            "tokens": 120,
            "custo": 0.0012,
        }

        with patch("src.provedor_desafio2.gerar", return_value=resposta):
            resultado = executar_provedor(
                "Pergunta ficticia",
                "Contexto ficticio",
                modo="openai",
                arquivo_log=str(log),
            )

        registro = json.loads(log.read_text(encoding="utf-8"))

        assert resultado == resposta
        assert registro["status"] == "sucesso"
        assert registro["provedor_solicitado"] == "openai"
        assert registro["modelo"] == "modelo-teste"
        assert registro["tokens"] == 120
        assert registro["custo_estimado_usd"] == 0.0012
        assert registro["latencia_segundos"] >= 0
        assert registro["envio_automatico"] is False
        assert registro["id"]
        assert registro["horario"]


def test_rf21_registra_falha_sem_expor_contexto():
    with tempfile.TemporaryDirectory() as pasta:
        log = Path(pasta) / "provedores.jsonl"

        with patch(
            "src.provedor_desafio2.gerar",
            side_effect=RuntimeError("Falha simulada"),
        ):
            with pytest.raises(RuntimeError):
                executar_provedor(
                    "Pergunta confidencial de teste",
                    "Contexto confidencial de teste",
                    modo="gemini",
                    arquivo_log=str(log),
                )

        conteudo = log.read_text(encoding="utf-8")
        registro = json.loads(conteudo)

        assert registro["status"] == "falha"
        assert registro["erro_tipo"] == "RuntimeError"
        assert registro["provedor_solicitado"] == "gemini"
        assert registro["latencia_segundos"] >= 0
        assert registro["envio_automatico"] is False
        assert "Pergunta confidencial de teste" not in conteudo
        assert "Contexto confidencial de teste" not in conteudo

def test_t12_troca_provedor_preserva_indice(tmp_path):
    from unittest.mock import Mock, patch

    from src.fluxo_desafio2 import executar_rag_provedor

    indice = Mock()
    indice.dados = {
        "versao_indice": 2,
        "modelo": "hashing-lexical-v1",
        "itens": {},
    }

    rag_simulado = {
        "status": "fundamentada (extrativa)",
        "resposta": "O prazo e de 30 dias.",
        "trechos": [
            {
                "documento": "norma_ficticia.txt",
                "versao": "1",
                "pagina": 1,
                "texto": "O prazo e de 30 dias.",
            }
        ],
    }

    versao_original = indice.dados["versao_indice"]
    log = tmp_path / "provedores_t12.jsonl"

    with (
        patch(
            "src.rag.responder",
            return_value=rag_simulado,
        ) as recuperar,
        patch(
            "src.fluxo_desafio2.executar_provedor",
            side_effect=[
                RuntimeError("Falha simulada"),
                {
                    "provedor": "gemini",
                    "texto": "O prazo e de 30 dias.",
                },
            ],
        ) as gerar,
    ):
        primeira = executar_rag_provedor(
            "Qual e o prazo?",
            indice,
            modo="openai",
            arquivo_log=log,
        )

        segunda = executar_rag_provedor(
            "Qual e o prazo?",
            indice,
            modo="gemini",
            arquivo_log=log,
        )

    assert primeira["status"] == "revisar"
    assert primeira["erro_tipo"] == "RuntimeError"
    assert primeira["envio_automatico"] is False

    assert segunda["status"] == "revisar"
    assert segunda["geracao"]["provedor"] == "gemini"
    assert segunda["envio_automatico"] is False

    assert recuperar.call_count == 2
    assert gerar.call_count == 2

    assert all(
        chamada.args[1] is indice
        for chamada in recuperar.call_args_list
    )

    assert [
        chamada.kwargs["modo"]
        for chamada in gerar.call_args_list
    ] == ["openai", "gemini"]

    indice.indexar.assert_not_called()
    assert indice.dados["versao_indice"] == versao_original
