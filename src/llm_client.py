import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv


RAIZ = Path(__file__).resolve().parent.parent


class ErroLLM(Exception):
    """Erro durante uma consulta ao modelo de linguagem."""


def carregar_configuracao():
    with (RAIZ / "config.json").open(
        "r", encoding="utf-8-sig"
    ) as arquivo:
        return json.load(arquivo)


def consultar_llm(
    mensagens,
    modelo=None,
    max_tokens=None,
    timeout=90,
    thinking_level="low"
):
    load_dotenv(RAIZ / ".env")

    chave = os.getenv("GEMINI_API_KEY")

    if not chave:
        raise ErroLLM(
            "Chave GEMINI_API_KEY não encontrada."
        )

    config = carregar_configuracao()

    if config.get("provedor") != "gemini":
        raise ErroLLM(
            "O cliente atual suporta o provedor Gemini."
        )

    modelo = modelo or config["modelo"]
    max_tokens = max_tokens or config["max_tokens"]

    if not isinstance(mensagens, list) or not mensagens:
        raise ErroLLM("A lista de mensagens está vazia.")

    instrucao_sistema = []
    conteudos = []

    for mensagem in mensagens:
        papel = mensagem.get("role")
        texto = mensagem.get("content")

        if not isinstance(texto, str) or not texto.strip():
            raise ErroLLM("Mensagem sem conteúdo válido.")

        if papel == "system":
            instrucao_sistema.append(texto)

        elif papel in ("user", "assistant"):
            conteudos.append({
                "role": "model" if papel == "assistant" else "user",
                "parts": [{"text": texto}]
            })

        else:
            raise ErroLLM(
                f"Papel de mensagem não suportado: {papel}"
            )

    if not conteudos:
        raise ErroLLM("Nenhuma mensagem de usuário ou assistente.")

    corpo = {
        "contents": conteudos,
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "thinkingConfig": {
                "thinkingLevel": thinking_level
            }
        }
    }

    if instrucao_sistema:
        corpo["systemInstruction"] = {
            "parts": [
                {"text": "\n\n".join(instrucao_sistema)}
            ]
        }

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{modelo}:generateContent"
    )

    inicio = time.perf_counter()

    # Repetir somente falhas transitórias; nunca repetir erros 4xx definitivos.
    for tentativa in range(1, 4):
        try:
            resposta = requests.post(
                url,
                headers={"x-goog-api-key": chave, "Content-Type": "application/json"},
                json=corpo,
                timeout=timeout
            )
        except requests.Timeout as erro:
            if tentativa == 3:
                raise ErroLLM("Tempo limite excedido na consulta à API após 3 tentativas.") from erro
        except requests.RequestException as erro:
            if tentativa == 3:
                raise ErroLLM("Não foi possível conectar ao serviço Gemini após 3 tentativas.") from erro
        else:
            if resposta.status_code not in (429, 500, 502, 503, 504) or tentativa == 3:
                break
        time.sleep(min(2 ** (tentativa - 1), 4))

    tempo = round(time.perf_counter() - inicio, 2)

    if resposta.status_code != 200:
        erros = {
            400: "Requisição inválida.",
            401: "Autenticação inválida.",
            403: "Acesso não autorizado.",
            404: "Modelo não encontrado ou indisponível.",
            429: "Limite de requisições ou cota atingida.",
            500: "Erro interno do provedor.",
            502: "Erro de comunicação com o provedor.",
            503: "Serviço temporariamente indisponível.",
            504: "Tempo limite do serviço excedido."
        }

        mensagem = erros.get(
            resposta.status_code,
            "Erro desconhecido na API."
        )

        raise ErroLLM(
            f"{mensagem} HTTP {resposta.status_code}."
        )

    try:
        dados = resposta.json()
    except ValueError as erro:
        raise ErroLLM(
            "A API retornou dados inválidos."
        ) from erro

    partes = []

    for candidato in dados.get("candidates", []):
        for parte in candidato.get("content", {}).get("parts", []):
            if isinstance(parte.get("text"), str):
                partes.append(parte["text"])

    texto = "\n".join(partes).strip()

    if not texto:
        raise ErroLLM(
            "A API não retornou uma resposta de texto."
        )

    uso = dados.get("usageMetadata", {})

    return {
        "provedor": "gemini",
        "modelo": modelo,
        "resposta": texto,
        "tempo_segundos": tempo,
        "tokens_entrada": uso.get("promptTokenCount"),
        "tokens_saida": uso.get("candidatesTokenCount"),
        "tokens_total": uso.get("totalTokenCount"),
        "custo_estimado_usd": None,
        "observacao_custo": (
            "Não calculado: preços por token não "
            "configurados neste projeto."
        )
    }


# ================== FUNCOES DESAFIO 02 ==================
import os
from typing import Any

class LLMAdaptadorMock:
    def __init__(self, nome: str = "mock"):
        self.nome = nome
        self.chamadas = 0
    def completar(self, prompt: str, **kwargs: Any) -> str:
        self.chamadas += 1
        if "Classifique" in prompt: return "inscricao"
        if "Resuma" in prompt: return "Resumo simulado."
        if "entidades" in prompt: return '{"entidades": [], "ausentes": []}'
        if "sentimento" in prompt: return '{"polaridade": "neutra", "justificativa": "Simulado"}'
        return "SEM_EVIDENCIA"

class LLMAdaptadorGemini:
    def __init__(self, modelo: str = "gemini-1.5-flash"):
        self.modelo = modelo
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key: raise ValueError("GEMINI_API_KEY nao configurada")
    def completar(self, prompt: str, **kwargs: Any) -> str:
        raise NotImplementedError("Use Mock offline.")

def criar_llm(nome: str = "mock") -> Any:
    if nome.lower() == "mock": return LLMAdaptadorMock()
    if nome.lower() == "gemini": return LLMAdaptadorGemini()
    raise ValueError(f"Provedor desconhecido: {nome}")
