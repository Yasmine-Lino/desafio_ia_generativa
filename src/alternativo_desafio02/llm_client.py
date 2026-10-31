"""Provedores de LLM da implementacao alternativa do Desafio 2."""

import os


class LLMAdaptadorMock:
    """Provedor local para testes, sem chamadas de rede."""

    def completar(self, prompt: str) -> str:
        return "Resposta simulada para teste."


class LLMAdaptadorGemini:
    """Adaptador Gemini ainda sem integracao real com a API."""

    def __init__(self):
        if not os.getenv("GEMINI_API_KEY"):
            raise ValueError("GEMINI_API_KEY nao configurada.")

    def completar(self, prompt: str) -> str:
        raise NotImplementedError(
            "Integracao Gemini ainda nao implementada neste adaptador."
        )


def criar_llm(provedor: str = "mock"):
    if provedor == "mock":
        return LLMAdaptadorMock()

    if provedor == "gemini":
        return LLMAdaptadorGemini()

    raise ValueError(f"Provedor nao suportado: {provedor}")
