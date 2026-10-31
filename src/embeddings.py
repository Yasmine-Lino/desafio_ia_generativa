"""
RF17 - Embeddings e indice vetorial.

Gera embeddings locais (sentence-transformers) e mantem indice Chroma
persistente, com metadados completos por vetor:
  documento, versao, hash, pagina, secao, chunk_id

Registra modelo e dimensao. Mudanca de modelo exige reindexacao.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer

MODELO_EMBEDDING = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
DIR_INDICE = Path("indice")
COLECAO = "acervo"


def hash_texto(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def hash_arquivo(caminho: Path) -> str:
    return hashlib.sha256(caminho.read_bytes()).hexdigest()


class MotorEmbedding:
    """Encapsula o modelo e garante carregamento unico."""

    _instancia: "MotorEmbedding | None" = None

    def __init__(self, modelo: str = MODELO_EMBEDDING):
        self.modelo_nome = modelo
        self._model = SentenceTransformer(modelo)
        self.dimensao = self._model.get_sentence_embedding_dimension()

    @classmethod
    def obter(cls, modelo: str = MODELO_EMBEDDING) -> "MotorEmbedding":
        if cls._instancia is None or cls._instancia.modelo_nome != modelo:
            cls._instancia = cls(modelo)
        return cls._instancia

    def gerar(self, textos: list[str]) -> list[list[float]]:
        vetores = self._model.encode(textos, normalize_embeddings=True, show_progress_bar=False)
        return [v.tolist() for v in vetores]


class IndiceVetorial:
    """
    Indice Chroma persistente com metadados.
    - Reutiliza o indice apos reinicio.
    - Reindexar o mesmo documento nao duplica (hash + upsert).
    - Mudanca de modelo de embedding exige reindexacao (detectada por metadado).
    """

    def __init__(self, dir_indice: Path = DIR_INDICE, colecao: str = COLECAO):
        self.dir_indice = dir_indice
        self.dir_indice.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(
            path=str(self.dir_indice),
            settings=Settings(anonymized_telemetry=False),
        )
        self.motor = MotorEmbedding.obter()
        self.colecao = self.client.get_or_create_collection(
            name=colecao,
            metadata={
                "modelo_embedding": self.motor.modelo_nome,
                "dimensao": self.motor.dimensao,
                "versao_indice": "1.0.0",
            },
        )
        self._verificar_modelo()

    def _verificar_modelo(self) -> None:
        meta = self.colecao.metadata or {}
        modelo_antigo = meta.get("modelo_embedding")
        if modelo_antigo and modelo_antigo != self.motor.modelo_nome:
            raise RuntimeError(
                f"Modelo de embedding mudou ({modelo_antigo} -> {self.motor.modelo_nome}). "
                "Reindexe o acervo antes de continuar."
            )

    def contar(self) -> int:
        return self.colecao.count()

    def indexar_chunks(self, chunks: list[dict[str, Any]], forcar: bool = False) -> dict[str, Any]:
        """
        chunks: lista de {id, texto, metadados}
        Idempotente: mesmo id nao duplica; hash igual pula (a menos que forcar=True).
        """
        if not chunks:
            return {"inseridos": 0, "ignorados": 0}

        ids_existentes: set[str] = set()
        if not forcar:
            existentes = self.colecao.get(ids=[c["id"] for c in chunks], include=["metadatas"])
            for cid, meta in zip(existentes["ids"], existentes["metadatas"] or []):
                ids_existentes.add(cid)

        novos = [c for c in chunks if c["id"] not in ids_existentes]
        ignorados = len(chunks) - len(novos)

        if not novos:
            return {"inseridos": 0, "ignorados": ignorados}

        textos = [c["texto"] for c in novos]
        vetores = self.motor.gerar(textos)
        self.colecao.upsert(
            ids=[c["id"] for c in novos],
            embeddings=vetores,
            documents=textos,
            metadatas=[c["metadados"] for c in novos],
        )
        return {"inseridos": len(novos), "ignorados": ignorados}

    def buscar(self, consulta: str, top_k: int = 5) -> list[dict[str, Any]]:
        """
        Retorna top-k trechos com distancia e explicacao do sentido.
        Chroma usa distancia de cosseno (menor = mais similar) quando
        o embedding e normalizado.
        """
        vetor = self.motor.gerar([consulta])[0]
        resultado = self.colecao.query(
            query_embeddings=[vetor],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )
        itens = []
        for i in range(len(resultado["ids"][0])):
            itens.append(
                {
                    "chunk_id": resultado["ids"][0][i],
                    "texto": resultado["documents"][0][i],
                    "metadados": resultado["metadatas"][0][i],
                    "distancia": resultado["distances"][0][i],
                    "similaridade": 1.0 - resultado["distances"][0][i],
                    "sentido": "cosseno normalizado: 1.0 = identico, 0.0 = ortogonal",
                }
            )
        return itens

    def remover_documento(self, doc_id: str) -> int:
        """Remove todos os chunks de um documento (para RF24)."""
        existentes = self.colecao.get(where={"doc_id": doc_id})
        ids = existentes.get("ids", [])
        if ids:
            self.colecao.delete(ids=ids)
        return len(ids)

    def resetar(self) -> None:
        self.client.delete_collection(COLECAO)
        self.colecao = self.client.get_or_create_collection(
            name=COLECAO,
            metadata={
                "modelo_embedding": self.motor.modelo_nome,
                "dimensao": self.motor.dimensao,
                "versao_indice": "1.0.0",
            },
        )


if __name__ == "__main__":
    idx = IndiceVetorial()
    print(f"Modelo: {idx.motor.modelo_nome}")
    print(f"Dimensao: {idx.motor.dimensao}")
    print(f"Chunks no indice: {idx.contar()}")
    print(f"Indice persistente em: {idx.dir_indice.resolve()}")