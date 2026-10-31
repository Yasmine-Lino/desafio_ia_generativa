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
