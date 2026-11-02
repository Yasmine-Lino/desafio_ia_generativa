"""Auditoria independente da implementacao alternativa do Desafio 2."""

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
DIR_LOGS = RAIZ / "resultados" / "logs" / "desafio02_alternativo"
ARQUIVO_LOG = DIR_LOGS / "auditoria.jsonl"

STATUS_VALIDOS = {"sucesso", "erro", "pendente"}
REVISOES_VALIDAS = {"pendente", "aprovado", "rejeitado", "nao_aplicavel"}

CAMPOS_PERMITIDOS = {
    "requisito", "origem", "provedor", "modelo",
    "versao_prompt", "status", "tempo_segundos",
    "tokens_entrada", "tokens_saida", "tokens_total",
    "revisao_humana", "codigo_erro", "parametros",
    "id_caso", "modalidade_entrada", "arquivo_entrada",
    "arquivo_processado", "arquivo_saida",
}


def mascarar_dados(valor):
    """Mascara dados pessoais e segredos antes de gravar."""
    if isinstance(valor, str):
        valor = re.sub(
            r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
            "***CPF***", valor
        )
        valor = re.sub(
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
            "***EMAIL***", valor
        )
        valor = re.sub(
            r"\b[A-Za-z_]*(?:API_KEY|TOKEN|SECRET|PASSWORD)"
            r"\s*=\s*[^\s,;]+",
            lambda m: m.group(0).split("=")[0] + "=***",
            valor,
            flags=re.IGNORECASE,
        )
        return valor

    if isinstance(valor, dict):
        return {k: mascarar_dados(v) for k, v in valor.items()}

    if isinstance(valor, list):
        return [mascarar_dados(v) for v in valor]

    return valor


def _destino(caminho=None):
    destino = Path(caminho) if caminho is not None else ARQUIVO_LOG
    destino.parent.mkdir(parents=True, exist_ok=True)
    return destino


def _validar_caminho(valor, campo):
    if valor is None:
        return

    if not isinstance(valor, str) or len(valor) > 200:
        raise ValueError(f"Caminho invalido: {campo}")

    caminho = Path(valor)

    if caminho.is_absolute() or ".." in caminho.parts:
        raise ValueError(f"Caminho inseguro: {campo}")

    if not re.fullmatch(r"[A-Za-z0-9_./-]+", valor):
        raise ValueError(f"Caminho invalido: {campo}")


def validar_registro(dados):
    if not isinstance(dados, dict):
        raise ValueError("Os dados devem ser um dicionario.")

    desconhecidos = set(dados) - CAMPOS_PERMITIDOS
    if desconhecidos:
        raise ValueError(
            f"Campos nao permitidos: {sorted(desconhecidos)}"
        )

    if not re.fullmatch(r"RF\d{2}", str(dados.get("requisito", ""))):
        raise ValueError("Requisito invalido.")

    if dados.get("status") not in STATUS_VALIDOS:
        raise ValueError("Status de execucao invalido.")

    if dados.get("revisao_humana", "pendente") not in REVISOES_VALIDAS:
        raise ValueError("Status de revisao invalido.")

    for campo in (
        "arquivo_entrada", "arquivo_processado", "arquivo_saida"
    ):
        _validar_caminho(dados.get(campo), campo)

    for campo in ("tokens_entrada", "tokens_saida", "tokens_total"):
        valor = dados.get(campo)
        if valor is not None and (type(valor) is not int or valor < 0):
            raise ValueError(f"Valor invalido: {campo}")

    tempo = dados.get("tempo_segundos")
    if tempo is not None and (
        type(tempo) not in (int, float) or tempo < 0
    ):
        raise ValueError("Tempo invalido.")

    return True


def registrar_execucao(dados, caminho=None, id_execucao=None):
    """Registra uma execucao com identificador unico."""

    validar_registro(dados)

    identificador = str(
        uuid.UUID(id_execucao) if id_execucao else uuid.uuid4()
    )

    registro = {
        "id_execucao": identificador,
        "tipo_evento": "execucao",
        "data_hora": datetime.now(timezone.utc).isoformat(),
        **dados,
        "revisao_humana": dados.get("revisao_humana", "pendente"),
    }

    registro = mascarar_dados(registro)
    destino = _destino(caminho)

    with destino.open("a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")

    return registro


def listar_execucoes(caminho=None):
    """Le os registros do arquivo JSONL."""

    destino = Path(caminho) if caminho is not None else ARQUIVO_LOG

    if not destino.exists():
        return []

    registros = []

    with destino.open("r", encoding="utf-8") as arquivo:
        for numero, linha in enumerate(arquivo, 1):
            if not linha.strip():
                continue

            try:
                registros.append(json.loads(linha))
            except json.JSONDecodeError as erro:
                raise ValueError(
                    f"Registro invalido na linha {numero}."
                ) from erro

    return registros


def registrar_decisao_humana(
    id_execucao,
    decisao,
    caminho=None,
    arquivo_revisado=None,
    sha256_documento=None,
):
    """Registra uma decisao humana vinculada a uma execucao."""

    aliases = {
        "aprovada": "aprovado",
        "rejeitada": "rejeitado",
    }
    decisao = aliases.get(decisao, decisao)

    if decisao not in {"aprovado", "rejeitado"}:
        raise ValueError("Decisao humana invalida.")

    try:
        identificador = str(uuid.UUID(id_execucao))
    except (ValueError, TypeError, AttributeError) as erro:
        raise ValueError("ID de execucao invalido.") from erro

    destino = Path(caminho) if caminho is not None else ARQUIVO_LOG
    registros = listar_execucoes(destino)

    execucoes = [
        r for r in registros
        if r.get("id_execucao") == identificador
        and r.get("tipo_evento", "execucao") == "execucao"
    ]

    if len(execucoes) != 1:
        raise ValueError("Execucao inexistente ou duplicada.")

    execucao = execucoes[0]

    if execucao.get("status") != "sucesso":
        raise ValueError("Execucao malsucedida nao pode ser revisada.")

    if execucao.get("revisao_humana") != "pendente":
        raise ValueError("Execucao nao esta pendente de revisao.")

    anteriores = [
        r for r in registros
        if r.get("tipo_evento") == "decisao_humana"
        and r.get("id_execucao_referenciada") == identificador
    ]

    if anteriores:
        raise ValueError("Esta execucao ja possui decisao humana.")

    if (arquivo_revisado is None) != (sha256_documento is None):
        raise ValueError("Arquivo e hash devem ser informados juntos.")

    evento = {
        "id_evento": str(uuid.uuid4()),
        "tipo_evento": "decisao_humana",
        "id_execucao_referenciada": identificador,
        "data_hora": datetime.now(timezone.utc).isoformat(),
        "requisito": execucao["requisito"],
        "decisao": decisao,
    }

    if arquivo_revisado is not None:
        _validar_caminho(arquivo_revisado, "arquivo_revisado")

        if not re.fullmatch(r"[a-f0-9]{64}", str(sha256_documento)):
            raise ValueError("Hash SHA-256 invalido.")

        evento["arquivo_revisado"] = arquivo_revisado
        evento["sha256_documento"] = sha256_documento

    with destino.open("a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(evento, ensure_ascii=False) + "\n")

    return evento


def consultar_revisao_humana(id_execucao, caminho=None):
    try:
        identificador = str(uuid.UUID(id_execucao))
    except (ValueError, TypeError, AttributeError) as erro:
        raise ValueError("ID de execucao invalido.") from erro

    registros = listar_execucoes(caminho)

    execucoes = [
        r for r in registros
        if r.get("id_execucao") == identificador
        and r.get("tipo_evento", "execucao") == "execucao"
    ]

    if len(execucoes) != 1:
        raise ValueError("Execucao inexistente ou duplicada.")

    decisoes = [
        r for r in registros
        if r.get("tipo_evento") == "decisao_humana"
        and r.get("id_execucao_referenciada") == identificador
    ]

    if len(decisoes) > 1:
        raise ValueError("Decisoes conflitantes no historico.")

    if decisoes:
        return decisoes[0]["decisao"]

    return execucoes[0].get("revisao_humana", "pendente")


def registrar_evento(tipo, dados, arquivo_log="eventos.jsonl"):
    """Compatibilidade com os registros de privacidade existentes."""

    if not re.fullmatch(r"[A-Za-z0-9_.-]+", arquivo_log):
        raise ValueError("Nome de arquivo invalido.")

    destino = _destino(DIR_LOGS / arquivo_log)

    evento = {
        "id": str(uuid.uuid4()),
        "tipo": tipo,
        "data_hora": datetime.now(timezone.utc).isoformat(),
        "dados": mascarar_dados(dados),
    }

    with destino.open("a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(evento, ensure_ascii=False) + "\n")

    return evento["id"]

def mascarar(texto):
    """Mascara chaves secretas e CPF em textos."""
    if not isinstance(texto, str):
        raise ValueError("O conteudo deve ser texto.")

    texto = re.sub(
        r"\b[A-Za-z_][A-Za-z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD)"
        r"\s*=\s*[^\s,;]+",
        lambda m: m.group(0).split("=", 1)[0] + "=***",
        texto,
        flags=re.IGNORECASE,
    )

    texto = re.sub(
        r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
        "***CPF***",
        texto,
    )

    return texto
