"""Matriz T01-T15: sem evidência = não verificado, nunca aprovado automaticamente."""
import json
from pathlib import Path

IDS = tuple(f"T{i:02d}" for i in range(1, 16))

def gerar_matriz(evidencias=None):
    evidencias = evidencias or {}
    matriz = []
    for identificador in IDS:
        dado = evidencias.get(identificador, {})
        aprovado = dado.get("aprovado") is True and bool(dado.get("referencia"))
        matriz.append({"id": identificador, "situacao": "Passou" if aprovado else "Não verificado", "referencia": dado.get("referencia") if aprovado else None})
    return matriz

def salvar_matriz(caminho, evidencias=None):
    destino = Path(caminho)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(gerar_matriz(evidencias), ensure_ascii=False, indent=2), encoding="utf-8")
