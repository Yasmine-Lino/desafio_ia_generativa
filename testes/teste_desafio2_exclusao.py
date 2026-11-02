import json
from pathlib import Path
from tempfile import TemporaryDirectory
from src.embeddings import Indice
from src.exclusao_desafio2 import excluir_documento


def test_txt_pdf_ids_distintos():
    from src.ingestion import documento
    from unittest.mock import patch
    with TemporaryDirectory() as d:
        pasta = Path(d)
        txt = pasta / "mesmo_v1.txt"
        pdf = pasta / "mesmo_v1.pdf"
        txt.write_text("Documento de matricula", encoding="utf-8")
        pdf.write_bytes(b"%PDF-ficticio")
        with patch("src.ingestion.ler_documento", side_effect=lambda p: [(1, "Documento de matricula")]):
            a, b = documento(txt)[0], documento(pdf)[0]
        assert a["id"] != b["id"]
        assert a["documento"] != b["documento"]


def test_exclusao_preserva_original_e_limpa_derivados():
    with TemporaryDirectory() as d:
        p = Path(d)
        original = p / "documento_v1.txt"
        original.write_text("O documento exige comprovante.", encoding="utf-8")
        i = Indice(p / "indice.json")
        i.indexar([original])
        trecho = next(iter(i.dados["itens"]))
        log = p / "desafio2.jsonl"
        revisoes = p / "revisoes.jsonl"
        auditoria = p / "exclusoes.jsonl"
        log.write_text(json.dumps({"id":"exec-1","ids_recuperados":[trecho]})+"\n", encoding="utf-8")
        revisoes.write_text(json.dumps({"id":"exec-1","decisao":"revisar"})+"\n", encoding="utf-8")
        evento = excluir_documento(i, original.name, log_execucoes=log, revisoes=revisoes, log_exclusoes=auditoria)
        assert evento["trechos_removidos"] == 1
        assert evento["execucoes_derivadas_removidas"] == 1
        assert log.read_text(encoding="utf-8") == ""
        assert revisoes.read_text(encoding="utf-8") == ""
        assert original.exists()
        assert not i.buscar("documento comprovante")
        assert auditoria.exists()

def test_t14_exclusao_persistente_apos_recarregar(tmp_path):
    original = tmp_path / "excluir.txt"
    manter = tmp_path / "manter.txt"

    original.write_text("comprovante exclusivo matricula", encoding="utf-8")
    manter.write_text("certidao exclusiva atendimento", encoding="utf-8")

    caminho_indice = tmp_path / "indice.json"
    indice = Indice(caminho_indice)
    indice.indexar([original, manter])

    versao_anterior = indice.dados["versao_indice"]
    assert any(
        item["documento"] == original.name
        for item in indice.dados["itens"].values()
    )

    excluir_documento(
        indice,
        original.name,
        log_execucoes=tmp_path / "execucoes.jsonl",
        revisoes=tmp_path / "revisoes.jsonl",
        log_exclusoes=tmp_path / "exclusoes.jsonl",
    )

    recarregado = Indice(caminho_indice)

    assert recarregado.dados["versao_indice"] == versao_anterior + 1
    assert not any(
        item["documento"] == original.name
        for item in recarregado.dados["itens"].values()
    )
    assert any(
        item["documento"] == manter.name
        for item in recarregado.dados["itens"].values()
    )
    assert not recarregado.buscar("comprovante matricula")
    assert recarregado.buscar("certidao atendimento")
    assert original.exists()
    assert manter.exists()


def test_t14_conteudo_auditoria_exclusao(tmp_path):
    from datetime import datetime

    original = tmp_path / "documento_auditoria.txt"
    original.write_text("documento para auditoria", encoding="utf-8")

    indice = Indice(tmp_path / "indice.json")
    indice.indexar([original])

    id_trecho = next(iter(indice.dados["itens"]))

    log = tmp_path / "execucoes.jsonl"
    revisoes = tmp_path / "revisoes.jsonl"
    auditoria = tmp_path / "exclusoes.jsonl"

    log.write_text(
        json.dumps({"id": "exec-t14", "ids_recuperados": [id_trecho]}) + "\n",
        encoding="utf-8",
    )
    revisoes.write_text(
        json.dumps({"id": "exec-t14", "decisao": "revisar"}) + "\n",
        encoding="utf-8",
    )

    evento = excluir_documento(
        indice,
        original.name,
        log_execucoes=log,
        revisoes=revisoes,
        log_exclusoes=auditoria,
    )

    registros = [
        json.loads(linha)
        for linha in auditoria.read_text(encoding="utf-8").splitlines()
        if linha.strip()
    ]

    assert len(registros) == 1
    assert registros[0] == evento
    assert evento["documento"] == original.name
    assert evento["trechos_removidos"] == 1
    assert evento["execucoes_derivadas_removidas"] == 1
    assert evento["revisoes_derivadas_removidas"] == 1
    assert evento["documento_original_preservado"] is True
    assert datetime.fromisoformat(evento["horario"]).tzinfo is not None

    assert log.read_text(encoding="utf-8") == ""
    assert revisoes.read_text(encoding="utf-8") == ""
    assert original.exists()
