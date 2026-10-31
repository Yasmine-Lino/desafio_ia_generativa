"""Fabrica de indices isolados; o backend semantico e opcional."""
from pathlib import Path


def criar_indice(modo="lexical", caminho=None, *, colecao="acervo_desafio02"):
    if modo == "lexical":
        from src.embeddings import Indice
        return Indice(caminho or "indice/acervo.json")
    if modo == "semantico":
        try:
            from src.alternativo_desafio02.embeddings import IndiceVetorial
        except ImportError as exc:
            raise RuntimeError(
                "Backend semantico indisponivel. Instale requirements.txt "
                "em ambiente Python 3.12 isolado."
            ) from exc
        return IndiceVetorial(
            dir_indice=Path(caminho or "indice/chroma_desafio02"),
            colecao=colecao,
        )
    raise ValueError("Backend invalido: use lexical ou semantico")


def buscar_trechos(indice, pergunta, *, modo="lexical", quantidade=3):
    """Normaliza a recuperacao, sem afirmar que a resposta e fundamentada.

    Nao mistura scores: similaridade lexical e distancia semantica
    possuem interpretacoes e calibracoes diferentes.
    """
    if not isinstance(pergunta, str) or not pergunta.strip():
        raise ValueError("A pergunta nao pode ser vazia")
    if not isinstance(quantidade, int) or isinstance(quantidade, bool) or quantidade < 1:
        raise ValueError("quantidade deve ser um inteiro positivo")
    if modo == "lexical":
        encontrados = indice.buscar(pergunta, k=quantidade)
        return [
            {
                "id": item["id"],
                "texto": item["texto"],
                "documento": item.get("documento"),
                "metadados": {
                    "versao": item.get("versao"),
                    "pagina": item.get("pagina"),
                },
                "pontuacao": item["similaridade"],
                "tipo_pontuacao": "cosseno_lexical",
            }
            for item in encontrados
        ]
    if modo == "semantico":
        encontrados = indice.buscar(pergunta, top_k=quantidade)
        return [
            {
                "id": item["chunk_id"],
                "texto": item["texto"],
                "documento": item.get("metadados", {}).get("doc_id"),
                "metadados": item.get("metadados", {}),
                "pontuacao": item["distancia"],
                "tipo_pontuacao": "distancia_chroma",
            }
            for item in encontrados
        ]
    raise ValueError("Backend invalido: use lexical ou semantico")
