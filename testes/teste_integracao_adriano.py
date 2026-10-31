from pathlib import Path
import json
import pytest
from src.audio import normalizar_texto, comparar_transcricao
from src import image_generation as img


def test_normalizacao_com_acentos_e_pontuacao():
    assert normalizar_texto("Olá, MUNDO! 2026") == "ola mundo 2026"


def test_comparacao_transcricao():
    assert comparar_transcricao("Matrícula aberta!", "matricula aberta")["correspondencia_exata_normalizada"] is True
    assert comparar_transcricao("texto A", "texto B")["similaridade"] < 1


def test_comparacao_rejeita_texto_vazio():
    with pytest.raises(ValueError):
        comparar_transcricao("", "referência")


def test_proveniencia_sem_sobrescrita(tmp_path, monkeypatch):
    original = tmp_path / "original.png"
    revisada = tmp_path / "revisada.png"
    metadados = tmp_path / "proveniencia.json"
    assinatura = b"\x89PNG\r\n\x1a\n"
    original.write_bytes(assinatura)
    revisada.write_bytes(assinatura)
    metadados.write_text(json.dumps({"identificacao_ia": True, "imagem_original": original.name, "imagem_revisada": revisada.name, "aprovado": False}), encoding="utf-8")
    monkeypatch.setattr(img, "ORIGINAL", original)
    monkeypatch.setattr(img, "REVISADA", revisada)
    monkeypatch.setattr(img, "METADADOS", metadados)
    antes = metadados.read_bytes()
    assert img.carregar_proveniencia()["aprovado"] is False
    assert metadados.read_bytes() == antes
    metadados.write_text(json.dumps({"identificacao_ia": True, "imagem_original": original.name, "imagem_revisada": revisada.name, "aprovado": True}), encoding="utf-8")
    with pytest.raises(ValueError):
        img.carregar_proveniencia()
