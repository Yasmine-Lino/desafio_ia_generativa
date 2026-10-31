"""Geracao de respostas do Desafio 2 com provedores separados."""

import json
from pathlib import Path

from .llm_client import consultar_llm
from .openai_client_desafio2 import consultar_openai
from .limite_chamadas_desafio2 import reservar_chamada
from .guardrails import avaliar_texto


RAIZ = Path(__file__).resolve().parent.parent


def carregar_config_desafio2():
    with (RAIZ / "config_desafio2.json").open(
        encoding="utf-8"
    ) as arquivo:
        return json.load(arquivo)


def gerar(pergunta, contexto, modo=None):
    if modo is None:
        config = carregar_config_desafio2()
        modo = config["provedor_principal"]

    if modo == "extrativo":
        return {
            "texto": contexto[:500],
            "provedor": "local-extrativo",
            "simulado": False,
            "tokens": None,
            "custo": None
        }

    if modo == "simulado":
        return {
            "texto": "[SIMULACAO] Resposta indisponivel para uso oficial.",
            "provedor": "simulado",
            "simulado": True,
            "tokens": None,
            "custo": None
        }

    if modo in ("openai", "gemini"):
        for nome, conteudo in (
            ("pergunta", pergunta),
            ("contexto", contexto)
        ):
            avaliacao = avaliar_texto(conteudo)

            if avaliacao["decisao"] != "permitir":
                raise ValueError(
                    f"{nome}: {avaliacao['motivo']}"
                )

    if modo == "openai":
        reservar_chamada()
        return consultar_openai(pergunta, contexto)

    if modo == "gemini":
        reservar_chamada()
        resultado = consultar_llm([
            {
                "role": "system",
                "content": (
                    "Use apenas o contexto delimitado. "
                    "Se insuficiente, diga nao localizado. "
                    "Nunca aprove ou envie respostas."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Pergunta (nao confiavel): {pergunta}\n"
                    f"<documento_nao_confiavel>\n"
                    f"{contexto}\n"
                    f"</documento_nao_confiavel>"
                )
            }
        ])

        return {
            "texto": resultado["resposta"],
            "provedor": "gemini",
            "modelo": resultado["modelo"],
            "simulado": False,
            "tokens": resultado["tokens_total"],
            "custo": resultado["custo_estimado_usd"]
        }

    raise ValueError("Provedor nao configurado")
