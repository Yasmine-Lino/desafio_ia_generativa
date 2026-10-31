"""Registro de auditoria e rastreabilidade das execuções."""

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DIR_LOGS = Path("resultados/logs")
DIR_LOGS.mkdir(parents=True, exist_ok=True)

# ... o resto do arquivo continua aqui embaixo ...

RAIZ = Path(__file__).resolve().parent.parent
PASTA_LOGS = RAIZ / "resultados" / "logs"
ARQUIVO_LOG = PASTA_LOGS / "auditoria.jsonl"

STATUS_VALIDOS = {"sucesso", "erro", "pendente"}
REVISOES_VALIDAS = {"pendente", "aprovado", "rejeitado", "nao_aplicavel"}

CAMPOS_PERMITIDOS = {
    "requisito",
    "origem",
    "provedor",
    "modelo",
    "versao_prompt",
    "status",
    "tempo_segundos",
    "tokens_entrada",
    "tokens_saida",
    "tokens_total",
    "revisao_humana",
    "codigo_erro",
    "parametros",
    "id_caso",
    "modalidade_entrada",
    "arquivo_entrada",
    "arquivo_processado",
    "arquivo_saida",
}


def validar_registro(dados):
    if not isinstance(dados, dict):
        raise ValueError("Os dados da auditoria devem ser um dicionário.")

    desconhecidos = set(dados) - CAMPOS_PERMITIDOS
    if desconhecidos:
        raise ValueError(
            "Campos não permitidos na auditoria: "
            + ", ".join(sorted(desconhecidos))
        )

    requisito = dados.get("requisito")
    if not isinstance(requisito, str) or not re.fullmatch(
        r"RF\d{2}", requisito
    ):
        raise ValueError("Requisito inválido. Exemplo: RF09.")

    if dados.get("status") not in STATUS_VALIDOS:
        raise ValueError("Status de execução inválido.")

    if dados.get("revisao_humana", "pendente") not in REVISOES_VALIDAS:
        raise ValueError("Situação da revisão humana inválida.")

    for campo in ("origem", "provedor", "modelo", "versao_prompt"):
        valor = dados.get(campo)
        if valor is not None and (
            not isinstance(valor, str)
            or not re.fullmatch(r"[A-Za-z0-9_.:/-]{1,100}", valor)
        ):
            raise ValueError(f"Valor inválido para {campo}.")

    id_caso = dados.get("id_caso")
    if id_caso is not None and (
        not isinstance(id_caso, str)
        or not re.fullmatch(r"[A-Za-z0-9_-]{1,50}", id_caso)
    ):
        raise ValueError("Identificador do caso inválido.")

    modalidade = dados.get("modalidade_entrada")
    if modalidade is not None and modalidade not in (
        "texto", "audio", "imagem"
    ):
        raise ValueError("Modalidade de entrada inválida.")

    for campo in (
        "arquivo_entrada",
        "arquivo_processado",
        "arquivo_saida"
    ):
        valor = dados.get(campo)

        if valor is None:
            continue

        if not isinstance(valor, str) or len(valor) > 200:
            raise ValueError(f"Caminho inválido para {campo}.")

        if not re.fullmatch(r"[A-Za-z0-9_./-]+", valor):
            raise ValueError(f"Caminho inválido para {campo}.")

        caminho = Path(valor)

        if (
            caminho.is_absolute()
            or ".." in caminho.parts
            or not caminho.parts
        ):
            raise ValueError(f"Caminho inseguro para {campo}.")

    codigo_erro = dados.get("codigo_erro")
    if codigo_erro is not None and not re.fullmatch(
        r"[A-Z][A-Z0-9_]{0,49}", codigo_erro
    ):
        raise ValueError("Código de erro inválido.")

    for campo in ("tokens_entrada", "tokens_saida", "tokens_total"):
        valor = dados.get(campo)
        if valor is not None and (
            type(valor) is not int or valor < 0
        ):
            raise ValueError(f"Valor inválido para {campo}.")

    tempo = dados.get("tempo_segundos")
    if tempo is not None and (
        type(tempo) not in (int, float) or tempo < 0
    ):
        raise ValueError("Tempo de execução inválido.")

    parametros = dados.get("parametros", {})
    if not isinstance(parametros, dict):
        raise ValueError("Parâmetros inválidos.")

    permitidos = {"max_tokens", "temperatura", "thinking_level"}
    if set(parametros) - permitidos:
        raise ValueError("Parâmetros não permitidos na auditoria.")

    for chave, valor in parametros.items():
        if chave == "thinking_level":
            if valor not in ("minimal", "low", "medium", "high"):
                raise ValueError("Nível de raciocínio inválido.")
        elif chave == "max_tokens":
            if type(valor) is not int or valor <= 0:
                raise ValueError("Limite de tokens inválido.")
        elif chave == "temperatura":
            if type(valor) not in (int, float) or not 0 <= valor <= 2:
                raise ValueError("Temperatura inválida.")

    return True


def registrar_execucao(dados, caminho=None, id_execucao=None):
    """Acrescenta um registro com campos previamente autorizados."""

    validar_registro(dados)

    if id_execucao is None:
        identificador = str(uuid.uuid4())
    else:
        try:
            identificador = str(uuid.UUID(id_execucao))
        except (ValueError, TypeError, AttributeError) as erro:
            raise ValueError(
                "Identificador de execução inválido."
            ) from erro

    registro = {
        "id_execucao": identificador,
        "data_hora": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "requisito": dados["requisito"],
        "origem": dados.get("origem"),
        "provedor": dados.get("provedor"),
        "modelo": dados.get("modelo"),
        "versao_prompt": dados.get("versao_prompt"),
        "parametros": dados.get("parametros", {}),
        "status": dados["status"],
        "tempo_segundos": dados.get("tempo_segundos"),
        "tokens_entrada": dados.get("tokens_entrada"),
        "tokens_saida": dados.get("tokens_saida"),
        "tokens_total": dados.get("tokens_total"),
        "revisao_humana": dados.get("revisao_humana", "pendente"),
        "codigo_erro": dados.get("codigo_erro"),
        "id_caso": dados.get("id_caso"),
        "modalidade_entrada": dados.get("modalidade_entrada"),
        "arquivo_entrada": dados.get("arquivo_entrada"),
        "arquivo_processado": dados.get("arquivo_processado"),
        "arquivo_saida": dados.get("arquivo_saida"),
    }

    destino = Path(caminho) if caminho is not None else ARQUIVO_LOG
    destino.parent.mkdir(parents=True, exist_ok=True)

    with destino.open("a", encoding="utf-8") as arquivo:
        arquivo.write(
            json.dumps(registro, ensure_ascii=False) + "\n"
        )

    return registro


def listar_execucoes(caminho=None):
    """Lê os registros existentes sem alterar o arquivo."""

    destino = Path(caminho) if caminho is not None else ARQUIVO_LOG

    if not destino.exists():
        return []

    registros = []

    with destino.open("r", encoding="utf-8") as arquivo:
        for numero, linha in enumerate(arquivo, start=1):
            if not linha.strip():
                continue

            try:
                registros.append(json.loads(linha))
            except json.JSONDecodeError as erro:
                raise ValueError(
                    f"Registro inválido na linha {numero}."
                ) from erro

    return registros

def registrar_decisao_humana(
    id_execucao,
    decisao,
    caminho=None,
    arquivo_revisado=None,
    sha256_documento=None
):
    """Registra uma decisão humana vinculada a uma execução existente."""

    if decisao not in ("aprovado", "rejeitado"):
        raise ValueError(
            "A decisão deve ser 'aprovado' ou 'rejeitado'."
        )

    try:
        identificador = str(uuid.UUID(id_execucao))
    except (ValueError, TypeError, AttributeError) as erro:
        raise ValueError(
            "Identificador de execução inválido."
        ) from erro

    destino = Path(caminho) if caminho is not None else ARQUIVO_LOG
    registros = listar_execucoes(destino)

    execucoes = [
        registro for registro in registros
        if registro.get("id_execucao") == identificador
        and registro.get("tipo_evento", "execucao") == "execucao"
    ]

    if len(execucoes) != 1:
        raise ValueError(
            "Execução não encontrada ou identificador duplicado."
        )

    execucao = execucoes[0]

    if execucao.get("status") != "sucesso":
        raise ValueError(
            "Somente execuções bem-sucedidas podem ser revisadas."
        )

    if execucao.get("revisao_humana") != "pendente":
        raise ValueError(
            "A execução não está pendente de revisão."
        )

    decisoes_anteriores = [
        registro for registro in registros
        if registro.get("tipo_evento") == "decisao_humana"
        and registro.get("id_execucao_referenciada") == identificador
    ]

    if decisoes_anteriores:
        raise ValueError(
            "Esta execução já possui uma decisão humana registrada."
        )

    evento = {
        "id_evento": str(uuid.uuid4()),
        "tipo_evento": "decisao_humana",
        "id_execucao_referenciada": identificador,
        "data_hora": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "requisito": execucao["requisito"],
        "decisao": decisao
    }

    # Identificação opcional da versão revisada.
    if (arquivo_revisado is None) != (sha256_documento is None):
        raise ValueError(
            "Arquivo revisado e SHA-256 devem ser informados juntos."
        )

    if arquivo_revisado is not None:
        if (
            not isinstance(arquivo_revisado, str)
            or len(arquivo_revisado) > 200
            or not re.fullmatch(r"[A-Za-z0-9_./-]+", arquivo_revisado)
        ):
            raise ValueError("Caminho do documento revisado inválido.")

        caminho_documento = Path(arquivo_revisado)

        if (
            caminho_documento.is_absolute()
            or ".." in caminho_documento.parts
        ):
            raise ValueError("Caminho do documento revisado inseguro.")

        if (
            not isinstance(sha256_documento, str)
            or not re.fullmatch(r"[a-f0-9]{64}", sha256_documento)
        ):
            raise ValueError("SHA-256 do documento inválido.")

        evento["arquivo_revisado"] = arquivo_revisado
        evento["sha256_documento"] = sha256_documento

    destino.parent.mkdir(parents=True, exist_ok=True)

    with destino.open("a", encoding="utf-8") as arquivo:
        arquivo.write(
            json.dumps(evento, ensure_ascii=False) + "\n"
        )

    return evento


def consultar_revisao_humana(id_execucao, caminho=None):
    """Consulta a decisão efetiva sem alterar os registros."""

    try:
        identificador = str(uuid.UUID(id_execucao))
    except (ValueError, TypeError, AttributeError) as erro:
        raise ValueError(
            "Identificador de execução inválido."
        ) from erro

    registros = listar_execucoes(caminho)

    execucoes = [
        registro for registro in registros
        if registro.get("id_execucao") == identificador
        and registro.get("tipo_evento", "execucao") == "execucao"
    ]

    if len(execucoes) != 1:
        raise ValueError("Execução não encontrada ou duplicada.")

    decisoes = [
        registro for registro in registros
        if registro.get("tipo_evento") == "decisao_humana"
        and registro.get("id_execucao_referenciada") == identificador
    ]

    if len(decisoes) > 1:
        raise ValueError("Há decisões conflitantes no histórico.")

    if decisoes:
        return decisoes[0]["decisao"]

    return execucoes[0].get("revisao_humana", "pendente")



# =========================================================================
# Funcoes do Desafio 02 (acrescentadas para nao quebrar o Desafio 01)
# =========================================================================

import re

PADROES_SEGREDO = [
    (re.compile(r"(GEMINI_API_KEY\s*=\s*)\S+", re.IGNORECASE), r"\1***"),
    (re.compile(r"(GROQ_API_KEY\s*=\s*)\S+", re.IGNORECASE), r"\1***"),
    (re.compile(r"(HF_TOKEN\s*=\s*)\S+", re.IGNORECASE), r"\1***"),
    (re.compile(r"([a-zA-Z0-9_\-]{30,})"), r"***MASCARADO***"),
    (re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"), "***CPF***"),
]

def mascarar(texto: str) -> str:
    """Remove credenciais, CPFs e tokens longos do texto."""
    for padrao, substituto in PADROES_SEGREDO:
        texto = padrao.sub(substituto, texto)
    return texto

def registrar_evento(
    tipo: str,
    dados: dict[str, Any],
    arquivo_log: str = "auditoria.jsonl",
) -> str:
    """Grava um evento em JSONL e mascara segredos."""
    id_evento = str(uuid.uuid4())
    evento = {
        "id": id_evento,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tipo": tipo,
        "dados": _mascarar_dados(dados),
    }
    caminho = DIR_LOGS / arquivo_log
    with open(caminho, "a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")
    return id_evento

def _mascarar_dados(dados: Any) -> Any:
    if isinstance(dados, str):
        return mascarar(dados)
    if isinstance(dados, dict):
        return {k: _mascarar_dados(v) for k, v in dados.items()}
    if isinstance(dados, list):
        return [_mascarar_dados(x) for x in dados]
    return dados


# ================== FUNCOES DESAFIO 02 ==================
import re
import uuid
from datetime import datetime, timezone
from typing import Any

PADROES_SEGREDO = [
    (re.compile(r"(GEMINI_API_KEY\s*=\s*)\S+", re.IGNORECASE), r"\1***"),
    (re.compile(r"(GROQ_API_KEY\s*=\s*)\S+", re.IGNORECASE), r"\1***"),
    (re.compile(r"(HF_TOKEN\s*=\s*)\S+", re.IGNORECASE), r"\1***"),
    (re.compile(r"([a-zA-Z0-9_\-]{30,})"), r"***MASCARADO***"),
    (re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"), "***CPF***"),
]

def mascarar(texto: str) -> str:
    for padrao, sub in PADROES_SEGREDO:
        texto = padrao.sub(sub, texto)
    return texto

def registrar_evento(tipo: str, dados: dict[str, Any], arquivo_log: str = "auditoria.jsonl") -> str:
    id_evento = str(uuid.uuid4())
    evento = {
        "id": id_evento,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tipo": tipo,
        "dados": _mascarar_dados(dados),
    }
    caminho = DIR_LOGS / arquivo_log
    with open(caminho, "a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")
    return id_evento

def _mascarar_dados(dados: Any) -> Any:
    if isinstance(dados, str):
        return mascarar(dados)
    if isinstance(dados, dict):
        return {k: _mascarar_dados(v) for k, v in dados.items()}
    if isinstance(dados, list):
        return [_mascarar_dados(x) for x in dados]
    return dados
