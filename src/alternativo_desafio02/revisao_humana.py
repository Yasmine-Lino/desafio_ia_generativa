"""Revisão humana de documentos vinculados à auditoria."""

import hashlib
from pathlib import Path

from src.audit import (
    RAIZ,
    listar_execucoes,
    registrar_decisao_humana,
)


def revisar_documento(
    id_execucao,
    decisao,
    arquivo_revisado,
    caminho_log=None,
    raiz_projeto=None
):
    """Registra a decisão humana sobre uma versão específica."""

    raiz = Path(raiz_projeto) if raiz_projeto else RAIZ
    raiz = raiz.resolve()

    documento = (raiz / arquivo_revisado).resolve()

    if not documento.is_relative_to(raiz):
        raise ValueError(
            "O documento revisado deve estar dentro do projeto."
        )

    if not documento.is_file():
        raise ValueError("Documento revisado não encontrado.")

    if decisao not in ("aprovado", "rejeitado"):
        raise ValueError("Decisão humana inválida.")

    registros = listar_execucoes(caminho_log)

    execucoes = [
        registro
        for registro in registros
        if registro.get("id_execucao") == id_execucao
        and registro.get("tipo_evento", "execucao") == "execucao"
    ]

    if len(execucoes) != 1:
        raise ValueError("Execução não encontrada ou duplicada.")

    execucao = execucoes[0]

    if execucao.get("status") != "sucesso":
        raise ValueError(
            "Não é possível revisar uma execução malsucedida."
        )

    if execucao.get("revisao_humana") != "pendente":
        raise ValueError("A execução não está pendente de revisão.")

    # Confere o vínculo do documento com a execução original.
    arquivo_original = execucao.get("arquivo_saida")

    if not arquivo_original:
        raise ValueError(
            "A execução não identifica o arquivo de saída."
        )

    original = Path(arquivo_original)
    revisado = Path(documento.relative_to(raiz).as_posix())

    nome_revisado = (
        original.stem + "_revisada" + original.suffix
    )

    caminhos_permitidos = {
        original.as_posix(),
        (original.parent / nome_revisado).as_posix()
    }

    if revisado.as_posix() not in caminhos_permitidos:
        raise ValueError(
            "Documento não corresponde à execução auditada."
        )

    conteudo = documento.read_bytes()

    if not conteudo:
        raise ValueError("Documento revisado está vazio.")

    hash_documento = hashlib.sha256(conteudo).hexdigest()

    caminho_relativo = documento.relative_to(raiz).as_posix()

    evento = registrar_decisao_humana(
        id_execucao=id_execucao,
        decisao=decisao,
        caminho=caminho_log,
        arquivo_revisado=caminho_relativo,
        sha256_documento=hash_documento
    )

    return evento

def verificar_integridade_documento(
    id_execucao,
    caminho_log=None,
    raiz_projeto=None
):
    """Verifica se o documento mantém o conteúdo registrado na revisão."""

    raiz = Path(raiz_projeto) if raiz_projeto else RAIZ
    raiz = raiz.resolve()

    registros = listar_execucoes(caminho_log)

    decisoes = [
        registro
        for registro in registros
        if registro.get("tipo_evento") == "decisao_humana"
        and registro.get("id_execucao_referenciada") == id_execucao
    ]

    if len(decisoes) != 1:
        raise ValueError(
            "Não existe uma decisão humana única para esta execução."
        )

    decisao = decisoes[0]
    caminho_registrado = decisao.get("arquivo_revisado")
    hash_registrado = decisao.get("sha256_documento")

    if not caminho_registrado or not hash_registrado:
        raise ValueError(
            "A decisão não possui identificação da versão revisada."
        )

    documento = (raiz / caminho_registrado).resolve()

    if not documento.is_relative_to(raiz):
        raise ValueError("Caminho do documento inseguro.")

    if not documento.is_file():
        return False

    hash_atual = hashlib.sha256(
        documento.read_bytes()
    ).hexdigest()

    return hash_atual == hash_registrado
