"""Testes RF21 - Auditoria da implementacao alternativa."""

import json
import hashlib

import pytest

from src.alternativo_desafio02.audit import (
    registrar_execucao,
    listar_execucoes,
    registrar_decisao_humana,
    consultar_revisao_humana,
)
from src.alternativo_desafio02.revisao_humana import (
    revisar_documento,
    verificar_integridade_documento,
)


def preparar_execucao(tmp_path):
    raiz = tmp_path / "projeto"
    documento = raiz / "resultados" / "minutas" / "teste.txt"
    documento.parent.mkdir(parents=True)
    documento.write_text("Minuta ficticia para teste.", encoding="utf-8")

    log = tmp_path / "auditoria.jsonl"

    execucao = registrar_execucao(
        {
            "requisito": "RF19",
            "origem": "rag",
            "provedor": "local",
            "status": "sucesso",
            "revisao_humana": "pendente",
            "arquivo_saida": "resultados/minutas/teste.txt",
            "id_caso": "caso_teste_01",
        },
        caminho=log,
    )

    return raiz, documento, log, execucao


def test_registra_execucao(tmp_path):
    raiz, documento, log, execucao = preparar_execucao(tmp_path)

    registros = listar_execucoes(log)

    assert len(registros) == 1
    assert registros[0]["tipo_evento"] == "execucao"
    assert registros[0]["status"] == "sucesso"
    assert execucao["id_execucao"]


def test_aprovacao_humana_e_integridade(tmp_path):
    raiz, documento, log, execucao = preparar_execucao(tmp_path)

    evento = revisar_documento(
        execucao["id_execucao"],
        "aprovado",
        "resultados/minutas/teste.txt",
        caminho_log=log,
        raiz_projeto=raiz,
    )

    assert evento["decisao"] == "aprovado"
    assert evento["id_execucao_referenciada"] == execucao["id_execucao"]

    esperado = hashlib.sha256(documento.read_bytes()).hexdigest()

    assert evento["sha256_documento"] == esperado
    assert consultar_revisao_humana(execucao["id_execucao"], log) == "aprovado"

    assert verificar_integridade_documento(
        execucao["id_execucao"],
        caminho_log=log,
        raiz_projeto=raiz,
    )


def test_detecta_documento_alterado(tmp_path):
    raiz, documento, log, execucao = preparar_execucao(tmp_path)

    revisar_documento(
        execucao["id_execucao"],
        "aprovado",
        "resultados/minutas/teste.txt",
        caminho_log=log,
        raiz_projeto=raiz,
    )

    documento.write_text("Conteudo alterado.", encoding="utf-8")

    assert not verificar_integridade_documento(
        execucao["id_execucao"],
        caminho_log=log,
        raiz_projeto=raiz,
    )


def test_rejeicao_humana(tmp_path):
    raiz, documento, log, execucao = preparar_execucao(tmp_path)

    revisar_documento(
        execucao["id_execucao"],
        "rejeitado",
        "resultados/minutas/teste.txt",
        caminho_log=log,
        raiz_projeto=raiz,
    )

    assert consultar_revisao_humana(execucao["id_execucao"], log) == "rejeitado"


def test_bloqueia_decisao_duplicada(tmp_path):
    raiz, documento, log, execucao = preparar_execucao(tmp_path)

    revisar_documento(
        execucao["id_execucao"],
        "aprovado",
        "resultados/minutas/teste.txt",
        caminho_log=log,
        raiz_projeto=raiz,
    )

    with pytest.raises(ValueError):
        revisar_documento(
            execucao["id_execucao"],
            "rejeitado",
            "resultados/minutas/teste.txt",
            caminho_log=log,
            raiz_projeto=raiz,
        )

    assert len(listar_execucoes(log)) == 2


def test_bloqueia_execucao_com_erro(tmp_path):
    log = tmp_path / "auditoria.jsonl"

    execucao = registrar_execucao(
        {
            "requisito": "RF19",
            "status": "erro",
            "revisao_humana": "pendente",
        },
        caminho=log,
    )

    with pytest.raises(ValueError):
        registrar_decisao_humana(
            execucao["id_execucao"],
            "aprovado",
            caminho=log,
        )


def test_bloqueia_documento_fora_do_projeto(tmp_path):
    raiz, documento, log, execucao = preparar_execucao(tmp_path)

    externo = tmp_path / "externo.txt"
    externo.write_text("Documento externo.", encoding="utf-8")

    with pytest.raises(ValueError):
        revisar_documento(
            execucao["id_execucao"],
            "aprovado",
            "../externo.txt",
            caminho_log=log,
            raiz_projeto=raiz,
        )

    assert len(listar_execucoes(log)) == 1


def test_bloqueia_documento_de_outra_execucao(tmp_path):
    raiz, documento, log, execucao = preparar_execucao(tmp_path)

    outro = raiz / "resultados" / "minutas" / "outro.txt"
    outro.write_text("Outra minuta.", encoding="utf-8")

    with pytest.raises(ValueError):
        revisar_documento(
            execucao["id_execucao"],
            "aprovado",
            "resultados/minutas/outro.txt",
            caminho_log=log,
            raiz_projeto=raiz,
        )


def test_mascara_dados_pessoais(tmp_path):
    log = tmp_path / "auditoria.jsonl"

    registrar_execucao(
        {
            "requisito": "RF19",
            "status": "sucesso",
            "origem": "teste",
            "id_caso": "caso_teste_02",
        },
        caminho=log,
    )

    # Verifica mascaramento diretamente no modulo.
    from src.alternativo_desafio02.audit import mascarar_dados

    resultado = mascarar_dados(
        "CPF 123.456.789-00 e email teste@exemplo.com"
    )

    assert "123.456.789-00" not in resultado
    assert "teste@exemplo.com" not in resultado


def test_rejeita_campo_nao_autorizado(tmp_path):
    log = tmp_path / "auditoria.jsonl"

    with pytest.raises(ValueError):
        registrar_execucao(
            {
                "requisito": "RF19",
                "status": "sucesso",
                "senha": "segredo",
            },
            caminho=log,
        )
