"""Revisao humana vinculada a auditoria alternativa."""

import hashlib
from pathlib import Path

from src.alternativo_desafio02.audit import (
    RAIZ,
    listar_execucoes,
    registrar_decisao_humana,
)


def revisar_documento(
    id_execucao,
    decisao,
    arquivo_revisado,
    caminho_log=None,
    raiz_projeto=None,
):
    """Registra decisao humana sobre documento de uma execucao."""

    raiz = Path(raiz_projeto) if raiz_projeto else RAIZ
    raiz = raiz.resolve()

    documento = (raiz / arquivo_revisado).resolve()

    if not documento.is_relative_to(raiz):
        raise ValueError("Documento fora da pasta do projeto.")

    if not documento.is_file():
        raise ValueError("Documento revisado nao encontrado.")

    if decisao not in ("aprovado", "rejeitado"):
        raise ValueError("Decisao humana invalida.")

    registros = listar_execucoes(caminho_log)

    execucoes = [
        r for r in registros
        if r.get("id_execucao") == id_execucao
        and r.get("tipo_evento", "execucao") == "execucao"
    ]

    if len(execucoes) != 1:
        raise ValueError("Execucao nao encontrada ou duplicada.")

    execucao = execucoes[0]

    if execucao.get("status") != "sucesso":
        raise ValueError("Execucao malsucedida nao pode ser revisada.")

    if execucao.get("revisao_humana") != "pendente":
        raise ValueError("Execucao nao esta pendente de revisao.")

    arquivo_original = execucao.get("arquivo_saida")

    if not arquivo_original:
        raise ValueError("Execucao sem arquivo de saida registrado.")

    original = Path(arquivo_original)

    caminhos_permitidos = {
        original.as_posix(),
        (original.parent / (
            original.stem + "_revisada" + original.suffix
        )).as_posix(),
    }

    caminho_relativo = documento.relative_to(raiz).as_posix()

    if caminho_relativo not in caminhos_permitidos:
        raise ValueError("Documento nao corresponde a execucao.")

    conteudo = documento.read_bytes()

    if not conteudo:
        raise ValueError("Documento revisado esta vazio.")

    hash_documento = hashlib.sha256(conteudo).hexdigest()

    return registrar_decisao_humana(
        id_execucao=id_execucao,
        decisao=decisao,
        caminho=caminho_log,
        arquivo_revisado=caminho_relativo,
        sha256_documento=hash_documento,
    )


def verificar_integridade_documento(
    id_execucao,
    caminho_log=None,
    raiz_projeto=None,
):
    """Confere se o documento continua igual ao revisado."""

    raiz = Path(raiz_projeto) if raiz_projeto else RAIZ
    raiz = raiz.resolve()

    registros = listar_execucoes(caminho_log)

    decisoes = [
        r for r in registros
        if r.get("tipo_evento") == "decisao_humana"
        and r.get("id_execucao_referenciada") == id_execucao
    ]

    if len(decisoes) != 1:
        raise ValueError("Decisao humana unica nao encontrada.")

    decisao = decisoes[0]

    caminho_registrado = decisao.get("arquivo_revisado")
    hash_registrado = decisao.get("sha256_documento")

    if not caminho_registrado or not hash_registrado:
        raise ValueError("Identificacao do documento incompleta.")

    documento = (raiz / caminho_registrado).resolve()

    if not documento.is_relative_to(raiz):
        raise ValueError("Caminho do documento inseguro.")

    if not documento.is_file():
        return False

    hash_atual = hashlib.sha256(
        documento.read_bytes()
    ).hexdigest()

    return hash_atual == hash_registrado
