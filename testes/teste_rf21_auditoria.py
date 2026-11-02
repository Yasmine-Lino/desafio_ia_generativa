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
