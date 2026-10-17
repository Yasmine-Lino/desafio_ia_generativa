"""Registro estruturado e seguro de execuções do projeto."""

import json
import uuid
from datetime import datetime
from pathlib import Path



RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_LOG = RAIZ / "resultados" / "logs" / "auditoria.jsonl"

PARAMETROS_PERMITIDOS = {
    "temperatura",
    "max_tokens",
    "timeout",
    "thinking_level",
    "voz",
}


def registrar_execucao(
    *,
    requisito,
    modalidade,
    arquivo_origem,
    provedor,
    modelo,
    prompt_versao,
    resultado_status,
    artefatos=None,
    parametros=None,
    duracao_segundos=None,
    erro=None,
    decisao_humana="pendente",
    caso_id=None,
):
    """Acrescenta um registro sem armazenar chaves ou conteúdo pessoal."""

    campos_obrigatorios = {
        "requisito": requisito,
        "modalidade": modalidade,
        "provedor": provedor,
        "modelo": modelo,
        "prompt_versao": prompt_versao,
        "resultado_status": resultado_status,
    }

    ausentes = [
        nome
        for nome, valor in campos_obrigatorios.items()
        if not isinstance(valor, str) or not valor.strip()
    ]
    if ausentes:
        raise ValueError(
            "Campos obrigatórios ausentes: " + ", ".join(ausentes)
        )

    parametros_seguros = {
        chave: valor
        for chave, valor in (parametros or {}).items()
        if chave in PARAMETROS_PERMITIDOS
    }

    registro = {
        "id_execucao": str(uuid.uuid4()),
        "data_hora": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "caso_id": caso_id or "não informado",
        "requisito": requisito,
        "modalidade": modalidade,
        "arquivo_origem": arquivo_origem or "não informado",
        "provedor": provedor,
        "modelo": modelo,
        "parametros": parametros_seguros,
        "versao_prompt": prompt_versao,
        "resultado": {
            "status": resultado_status,
            "artefatos": artefatos or [],
        },
        "duracao_segundos": duracao_segundos,
        "erro_tipo": type(erro).__name__ if erro else None,
        "decisao_humana": decisao_humana,
        "segredos_registrados": False,
        "conteudo_integral_registrado": False,
    }

    ARQUIVO_LOG.parent.mkdir(parents=True, exist_ok=True)
    with ARQUIVO_LOG.open("a", encoding="utf-8") as arquivo:
        arquivo.write(
            json.dumps(registro, ensure_ascii=False) + "\n"
        )

    return registro