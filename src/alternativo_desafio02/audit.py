"""Auditoria isolada da implementacao alternativa do Desafio 2."""

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

DIR_LOGS = Path("resultados/logs/desafio02_alternativo")


def mascarar(texto: str) -> str:
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



def mascarar_dados(valor):
    """Mascara textos preservando a estrutura dos dados."""
    if isinstance(valor, str):
        return mascarar(valor)
    if isinstance(valor, dict):
        return {chave: mascarar_dados(item) for chave, item in valor.items()}
    if isinstance(valor, list):
        return [mascarar_dados(item) for item in valor]
    return valor


def registrar_evento(tipo: str, dados: dict, arquivo_log: str = "revisoes.jsonl") -> str:
    destino = DIR_LOGS / arquivo_log

    if Path(arquivo_log).name != arquivo_log:
        raise ValueError("Nome de arquivo de log invalido.")

    destino.parent.mkdir(parents=True, exist_ok=True)

    identificador = uuid4().hex

    evento = {
        "id": identificador,
        "tipo": tipo,
        "data_hora": datetime.now(timezone.utc).isoformat(),
        "dados": mascarar_dados(dados),
    }

    with destino.open("a", encoding="utf-8") as log:
        log.write(json.dumps(evento, ensure_ascii=False) + "\n")

    return identificador
