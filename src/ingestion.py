"""
RF17 + RF18 - Ingestao e chunking do acervo.

- Extrai texto de TXT e PDF (pymupdf).
- Divide em chunks com tamanho e sobreposicao configuraveis.
- Metadados por chunk: doc_id, versao, hash, pagina, secao, chunk_id.
- Indexa no Chroma de forma idempotente (hash do arquivo).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pymupdf

from src.embeddings import IndiceVetorial, hash_arquivo, hash_texto

DIR_ACERVO = Path("dados/acervo")

# Metadados conhecidos por documento (extraidos do cabecalho)
RE_DOC_ID = re.compile(r"Identificador:\s*(DOC\d{2})", re.IGNORECASE)
RE_TITULO = re.compile(r"Titulo:\s*(.+)", re.IGNORECASE)
RE_VERSAO = re.compile(r"Versao:\s*([\d.]+)", re.IGNORECASE)
RE_DATA = re.compile(r"Data de publicacao:\s*([\d/]+)", re.IGNORECASE)
RE_SECAO = re.compile(r"^(\d+(?:\.\d+)*\.?)\s+(.+)$", re.MULTILINE)


@dataclass
class Chunk:
    id: str
    texto: str
    metadados: dict[str, Any]


def extrair_texto_txt(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8")


def extrair_texto_pdf(caminho: Path) -> tuple[str, int]:
    """Retorna (texto, numero_de_paginas)."""
    doc = pymupdf.open(caminho)
    partes = []
    for page in doc:
        partes.append(page.get_text())
    n = doc.page_count
    doc.close()
    return "\n".join(partes), n


def metadados_do_texto(texto: str, caminho: Path, paginas: int = 1) -> dict[str, Any]:
    doc_id = (RE_DOC_ID.search(texto) or [None, caminho.stem])[1]
    titulo = (RE_TITULO.search(texto) or [None, caminho.stem])[1].strip()
    versao = (RE_VERSAO.search(texto) or [None, "1.0"])[1]
    data = (RE_DATA.search(texto) or [None, ""])[1]
    return {
        "doc_id": doc_id,
        "titulo": titulo,
        "versao": versao,
        "data_publicacao": data,
        "arquivo": str(caminho),
        "formato": caminho.suffix.lstrip(".").lower(),
        "paginas": paginas,
        "hash_arquivo": hash_arquivo(caminho),
    }


def chunkar(
    texto: str,
    tamanho: int = 500,
    sobreposicao: int = 100,
) -> list[str]:
    """
    Chunking por paragrafos, respeitando tamanho e sobreposicao em caracteres.
    Preserva limites de paragrafo quando possivel.
    """
    if sobreposicao >= tamanho:
        raise ValueError("sobreposicao deve ser menor que tamanho")
    paragrafos = [p.strip() for p in re.split(r"\n\s*\n", texto) if p.strip()]
    chunks: list[str] = []
    buffer = ""
    for p in paragrafos:
        if len(buffer) + len(p) + 1 <= tamanho:
            buffer = (buffer + "\n" + p).strip()
        else:
            if buffer:
                chunks.append(buffer)
            # Se o paragrafo sozinho e maior que o tamanho, quebra em pedacos
            if len(p) > tamanho:
                for i in range(0, len(p), tamanho - sobreposicao):
                    chunks.append(p[i : i + tamanho])
                buffer = ""
            else:
                # Inicia novo buffer com sobreposicao do anterior
                inicio = max(0, len(buffer) - sobreposicao) if buffer else 0
                buffer = (buffer[inicio:] + "\n" + p).strip()
    if buffer:
        chunks.append(buffer)
    return chunks


def _secao_do_chunk(chunk: str) -> str:
    """Tenta identificar a secao numerica mais proxima no inicio do chunk."""
    m = re.match(r"^(\d+(?:\.\d+)*\.?)\s", chunk)
    return m.group(1) if m else ""


def preparar_chunks(
    caminho: Path,
    tamanho: int = 500,
    sobreposicao: int = 100,
) -> list[dict[str, Any]]:
    """Extrai, chunka e monta metadados de um documento."""
    if caminho.suffix.lower() == ".pdf":
        texto, paginas = extrair_texto_pdf(caminho)
    else:
        texto = extrair_texto_txt(caminho)
        paginas = 1

    meta_base = metadados_do_texto(texto, caminho, paginas)
    pedacos = chunkar(texto, tamanho, sobreposicao)
    chunks = []
    for i, pedaco in enumerate(pedacos):
        # Inclui o formato no id para evitar colisao entre .txt e .pdf do mesmo doc
        chunk_id = (
            f"{meta_base['doc_id']}::{meta_base['formato']}::v{meta_base['versao']}::p{i:03d}"
        )
        meta = dict(meta_base)
        meta["chunk_id"] = chunk_id
        meta["indice"] = i
        meta["secao"] = _secao_do_chunk(pedaco)
        meta["hash_chunk"] = hash_texto(pedaco)
        meta["tamanho_chunk"] = tamanho
        meta["sobreposicao"] = sobreposicao
        chunks.append(
            {
                "id": chunk_id,
                "texto": pedaco,
                "metadados": meta,
            }
        )
    return chunks


def indexar_acervo(
    dir_acervo: Path = DIR_ACERVO,
    tamanho: int = 500,
    sobreposicao: int = 100,
    indice: IndiceVetorial | None = None,
    forcar: bool = False,
) -> dict[str, Any]:
    """Indexa todos os documentos do acervo. Idempotente."""
    idx = indice or IndiceVetorial()
    todos_chunks: list[dict[str, Any]] = []
    por_doc: list[dict[str, Any]] = []

    for caminho in sorted(dir_acervo.glob("*")):
        if caminho.suffix.lower() not in {".txt", ".pdf"}:
            continue
        # Ignora o documento adversarial de teste (RF16) na indexacao oficial
        if "envenenado" in caminho.name:
            continue
        chunks = preparar_chunks(caminho, tamanho, sobreposicao)
        todos_chunks.extend(chunks)
        por_doc.append(
            {
                "arquivo": caminho.name,
                "chunks": len(chunks),
                "doc_id": chunks[0]["metadados"]["doc_id"] if chunks else None,
            }
        )

    res = idx.indexar_chunks(todos_chunks, forcar=forcar)
    return {
        "documentos": por_doc,
        "total_chunks": len(todos_chunks),
        "inseridos": res["inseridos"],
        "ignorados": res["ignorados"],
        "chunks_no_indice": idx.contar(),
        "modelo": idx.motor.modelo_nome,
        "dimensao": idx.motor.dimensao,
        "parametros": {"tamanho": tamanho, "sobreposicao": sobreposicao},
    }


if __name__ == "__main__":
    import json

    resultado = indexar_acervo()
    print(json.dumps(resultado, indent=2, ensure_ascii=False))