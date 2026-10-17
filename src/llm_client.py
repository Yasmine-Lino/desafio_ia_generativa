import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

from src.audit import registrar_execucao


RAIZ = Path(__file__).resolve().parent.parent


class ErroLLM(Exception):
    """Erro durante uma consulta ao modelo de linguagem."""


def carregar_configuracao():
    with (RAIZ / "config.json").open(
        "r", encoding="utf-8-sig"
    ) as arquivo:
        return json.load(arquivo)


def _consultar_llm_sem_auditoria(
    mensagens,
    modelo=None,
    max_tokens=None,
    timeout=90,
    thinking_level="low",
):
    load_dotenv(RAIZ / ".env")

    chave = os.getenv("GEMINI_API_KEY")

    if not chave:
        raise ErroLLM("Chave GEMINI_API_KEY não encontrada.")

    config = carregar_configuracao()

    if config.get("provedor") != "gemini":
        raise ErroLLM("O cliente atual suporta o provedor Gemini.")

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
                "parts": [{"text": texto}],
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
                "thinkingLevel": thinking_level,
            },
        },
    }

    if instrucao_sistema:
        corpo["systemInstruction"] = {
            "parts": [
                {"text": "\n\n".join(instrucao_sistema)}
            ],
        }

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{modelo}:generateContent"
    )

    inicio = time.perf_counter()

    try:
        resposta = requests.post(
            url,
            headers={
                "x-goog-api-key": chave,
                "Content-Type": "application/json",
            },
            json=corpo,
            timeout=timeout,
        )

    except requests.Timeout as erro:
        raise ErroLLM(
            "Tempo limite excedido na consulta à API."
        ) from erro

    except requests.RequestException as erro:
        raise ErroLLM(
            "Não foi possível conectar ao serviço Gemini."
        ) from erro

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
            504: "Tempo limite do serviço excedido.",
        }

        mensagem = erros.get(
            resposta.status_code,
            "Erro desconhecido na API.",
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
        ),
    }


def consultar_llm(
    mensagens,
    modelo=None,
    max_tokens=None,
    timeout=90,
    thinking_level="low",
    *,
    requisito=None,
    arquivo_origem=None,
    prompt_versao="nao_informado",
    artefatos=None,
    caso_id=None,
):
    # Mantém chamadas sem contexto, como testes existentes, sem criar log.
    if not requisito:
        return _consultar_llm_sem_auditoria(
            mensagens,
            modelo=modelo,
            max_tokens=max_tokens,
            timeout=timeout,
            thinking_level=thinking_level,
        )

    inicio = time.perf_counter()

    try:
        config = carregar_configuracao()
    except Exception:
        config = {}

    provedor_log = config.get("provedor", "gemini")
    modelo_log = modelo or config.get("modelo", "não informado")
    max_tokens_log = max_tokens or config.get("max_tokens")

    try:
        resultado = _consultar_llm_sem_auditoria(
            mensagens,
            modelo=modelo,
            max_tokens=max_tokens,
            timeout=timeout,
            thinking_level=thinking_level,
        )
    except Exception as erro:
        registrar_execucao(
            requisito=requisito,
            modalidade="geracao_de_texto",
            arquivo_origem=arquivo_origem,
            provedor=provedor_log,
            modelo=modelo_log,
            prompt_versao=prompt_versao,
            resultado_status="falha",
            artefatos=artefatos,
            parametros={
                "max_tokens": max_tokens_log,
                "timeout": timeout,
                "thinking_level": thinking_level,
            },
            duracao_segundos=round(
                time.perf_counter() - inicio, 2
            ),
            erro=erro,
            caso_id=caso_id,
        )
        raise

    registrar_execucao(
        requisito=requisito,
        modalidade="geracao_de_texto",
        arquivo_origem=arquivo_origem,
        provedor=resultado["provedor"],
        modelo=resultado["modelo"],
        prompt_versao=prompt_versao,
        resultado_status="sucesso",
        artefatos=artefatos,
        parametros={
            "max_tokens": max_tokens_log,
            "timeout": timeout,
            "thinking_level": thinking_level,
        },
        duracao_segundos=resultado["tempo_segundos"],
        decisao_humana="pendente",
        caso_id=caso_id,
    )

    return resultado