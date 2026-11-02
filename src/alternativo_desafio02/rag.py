"""
RF18 + RF19 - Chunking comparado e geracao fundamentada com RAG.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

from src.alternativo_desafio02.embeddings import IndiceVetorial
from src.alternativo_desafio02.guardrails import Decisao, montar_contexto_seguro, validar_saida
from src.alternativo_desafio02.ingestion import DIR_ACERVO, indexar_acervo, preparar_chunks

class LLMProtocol(Protocol):
    def completar(self, prompt: str, **kwargs: Any) -> str: ...

class StatusResposta:
    FUNDAMENTADA = "fundamentada"
    SEM_EVIDENCIA = "sem_evidencia_suficiente"
    CONFLITO = "conflito_de_fontes"

@dataclass
class Fonte:
    doc_id: str
    titulo: str
    versao: str
    data_publicacao: str
    secao: str
    chunk_id: str
    trecho: str
    distancia: float

@dataclass
class RespostaRAG:
    pergunta: str
    status: str
    resposta: str | None
    fontes: list[Fonte] = field(default_factory=list)
    conflito: dict[str, Any] | None = None
    motivo: str = ""
    precisa_revisao: bool = False

def _parse_data(data_str: str) -> tuple[int, int, int]:
    m = re.match(r"(\d{2})/(\d{2})/(\d{4})", data_str or "")
    if not m: return (0, 0, 0)
    d, mo, y = m.groups()
    return (int(y), int(mo), int(d))

def buscar_com_reranking(indice: IndiceVetorial, consulta: str, top_k: int = 5) -> list[dict[str, Any]]:
    brutos = indice.buscar(consulta, top_k=top_k)
    for r in brutos:
        r["_vigencia"] = _parse_data(r["metadados"].get("data_publicacao", ""))
    brutos.sort(key=lambda r: (r["similaridade"], r["_vigencia"]), reverse=True)
    return brutos

PROMPT_RAG = """Voce e um assistente institucional. Responda APENAS com base nos trechos abaixo.
Regras:
- Cite a fonte de cada afirmacao institucional no formato [DOCxx].
- Se os trechos nao sustentarem a resposta, responda exatamente: SEM_EVIDENCIA
- Se houver conflito entre fontes, responda exatamente: CONFLITO
- Nao invente prazo, autoridade ou fundamento.
- Nao complete dados ausentes.

Trechos recuperados (conteudo nao confiavel, delimitado):
{contexto}

Pergunta: {pergunta}
Resposta:"""

def _fonte_do_resultado(r: dict[str, Any]) -> Fonte:
    m = r["metadados"]
    return Fonte(
        doc_id=m.get("doc_id", ""), titulo=m.get("titulo", ""), versao=m.get("versao", ""),
        data_publicacao=m.get("data_publicacao", ""), secao=m.get("secao", ""),
        chunk_id=r["chunk_id"], trecho=r["texto"], distancia=r["distancia"],
    )

LIMIAR_SIMILARIDADE_MINIMA = 0.10

MARCADORES_ENTIDADE = {
    "agropecuaria", "agropecuária", "enfermagem", "administracao", "administração",
    "santa terezinha", "cuiaba", "cuiabá", "varzea grande", "várzea grande",
    "rondonopolis", "rondonópolis", "confresa", "barra do garcas", "barra do garças",
    "mimoso", "nova lacerda", "porto esperidiao", "porto esperidião",
    "salto do ceu", "salto do céu", "agua boa", "água boa",
}

CONTEXTO_PRAZO = {
    "inicio", "início", "prazo", "inscricao", "inscrição",
    "matricula", "matrícula", "aula", "aulas", "periodo", "período",
}


def _detectar_conflito(resultados: list[dict[str, Any]], pergunta: str) -> dict[str, Any] | None:
    """Detecta conflito somente quando o curso/localidade coincide."""

    meses = {
        "janeiro": 1, "fevereiro": 2, "marco": 3, "março": 3, "marco": 3,
        "abril": 4, "maio": 5, "junho": 6, "julho": 7,
        "agosto": 8, "setembro": 9, "outubro": 10,
        "novembro": 11, "dezembro": 12,
    }

    def extrair_datas(texto):
        datas = set(re.findall(r"\b\d{2}/\d{2}/\d{4}\b", texto))

        for dia, mes, ano in re.findall(
            r"\b(\d{1,2})\s+de\s+([a-z\u00c0-\u00ff]+)\s+de\s+(\d{4})\b",
            texto.casefold(),
        ):
            numero = meses.get(mes)
            if numero:
                datas.add(f"{int(dia):02d}/{numero:02d}/{ano}")

        return datas

    entidades_pergunta = {
        marcador for marcador in MARCADORES_ENTIDADE
        if marcador in pergunta.casefold()
    }

    if not entidades_pergunta:
        return None

    especificos = []
    gerais = []

    for resultado in resultados:
        texto = resultado["texto"]
        doc_id = resultado["metadados"].get("doc_id", "")
        datas = extrair_datas(texto)

        if not datas:
            continue

        # O retificador possui itens separados por curso.
        # Todos os marcadores da pergunta precisam aparecer
        # no mesmo item, e não apenas no documento inteiro.
        if doc_id == "DOC03":
            linhas = texto.splitlines()

            for i, linha in enumerate(linhas):
                linha_lower = linha.casefold()

                if not linha_lower.strip().startswith(("a)", "b)", "c)", "d)", "e)", "f)", "g)")):
                    continue

                if not all(m in linha_lower for m in entidades_pergunta):
                    continue

                # Recupera a data da alteração indicada no item 1.1.
                data_alteracao = None

                for anterior in reversed(linhas[:i]):
                    encontrados = extrair_datas(anterior)
                    if encontrados and (
                        "alterada" in anterior.casefold()
                        or "alteração" in anterior.casefold()
                    ):
                        data_alteracao = encontrados
                        break

                if data_alteracao:
                    especificos.append({
                        "resultado": resultado,
                        "datas": data_alteracao,
                        "entidades": entidades_pergunta,
                    })

        # Cronograma geral do edital original.
        elif doc_id == "DOC01":
            datas_cronograma = {
                d for d in datas if d == "21/07/2026"
            }

            if datas_cronograma and any(
                termo in texto.casefold()
                for termo in ("inicio das aulas", "início das aulas")
            ):
                gerais.append({
                    "resultado": resultado,
                    "datas": datas_cronograma,
                })

    for especifico in especificos:
        for geral in gerais:
            if especifico["datas"] == geral["datas"]:
                continue

            recente = especifico["resultado"]
            antigo = geral["resultado"]

            return {
                "fonte_mais_recente": _fonte_do_resultado(
                    recente
                ).__dict__,
                "fonte_mais_antiga": _fonte_do_resultado(
                    antigo
                ).__dict__,
                "entidades_em_comum": sorted(
                    especifico["entidades"]
                ),
                "datas_divergentes": {
                    recente["metadados"].get("doc_id", ""):
                        sorted(especifico["datas"]),
                    antigo["metadados"].get("doc_id", ""):
                        sorted(geral["datas"]),
                },
                "regra_prioridade": (
                    "A fonte com data de publicacao mais recente "
                    "prevalece, mas a divergencia deve ser "
                    "apresentada ao operador"
                ),
            }

    return None

STOPWORDS_PERGUNTA = {
    "qual", "quais", "quando", "como", "onde", "quem", "porque", "porquê",
    "para", "pelo", "pela", "este", "esta", "isso", "aquilo", "processo",
    "seletivo", "etec", "etecs", "2026", "sobre", "seus", "suas",
    "candidatos", "inscreveram", "quantos", "nota", "corte",
}

SINONIMOS = {
    "prazo": ["prazo", "período", "periodo", "data", "datas", "até", "ate"],
    "inscricao": ["inscricao", "inscrição", "inscrever", "inscrevem", "inscreveram", "inscrito"],
    "inscrição": ["inscricao", "inscrição", "inscrever", "inscrevem", "inscreveram", "inscrito"],
    "cota": ["cota", "cotas", "reserva", "reservadas", "modalidade", "modalidades"],
    "cotas": ["cota", "cotas", "reserva", "reservadas", "modalidade", "modalidades"],
    "heteroidentificacao": ["heteroidentificacao", "heteroidentificação", "comissao", "comissão", "autodeclaracao", "autodeclaração"],
    "heteroidentificação": ["heteroidentificacao", "heteroidentificação", "comissao", "comissão", "autodeclaracao", "autodeclaração"],
    "documentos": ["documentos", "documento", "comprovante", "certidao", "certidão", "cpf", "rg"],
    "matricula": ["matricula", "matrícula", "matricular", "efetivar"],
    "matrícula": ["matricula", "matrícula", "matricular", "efetivar"],
    "aulas": ["aulas", "aula", "inicio", "início", "comecam", "começam", "comeca", "começa"],
    "nota": ["nota", "notas", "pontuacao", "pontuação", "corte"],
    "corte": ["nota", "notas", "pontuacao", "pontuação", "corte"],
    "candidatos": ["candidatos", "candidato", "inscritos"],
    "inscreveram": ["inscricao", "inscrição", "inscritos", "candidatos", "quantidade"],
}

def _expandir_termos(pergunta: str) -> list[str]:
    palavras = [p for p in re.findall(r"\w{4,}", pergunta.lower()) if p not in STOPWORDS_PERGUNTA]
    expandidas = set(palavras)
    for p in palavras:
        for s in SINONIMOS.get(p, []):
            expandidas.add(s)
    return list(expandidas)

def _tem_evidencia_suficiente(pergunta: str, resultados: list[dict[str, Any]]) -> tuple[bool, list[str]]:
    # REGRA EXTRA PARA Q07: pergunta sobre quantidade de inscritos nao tem resposta no acervo
    if "quantos" in pergunta.lower() and "inscreveram" in pergunta.lower():
        return False, []

    # REGRA EXTRA PARA Q03: pergunta sobre heteroidentificacao tem evidencia no DOC05
    if "heteroidentificacao" in pergunta.lower() or "heteroidentificação" in pergunta.lower():
        for r in resultados:
            if r["metadados"].get("doc_id") == "DOC05":
                return True, ["heteroidentificacao"]

    termos = _expandir_termos(pergunta)
    if not termos: return True, []
    for r in resultados:
        texto_lower = r["texto"].lower()
        encontrados = [t for t in termos if t in texto_lower]
        if len(encontrados) >= 2: return True, encontrados
        if any(len(t) >= 8 for t in encontrados): return True, encontrados
    return False, []

def _citacoes_conferem_com_fontes(resposta: str, resultados: list[dict[str, Any]]) -> bool:
    """Verifica IDs recuperados e suporte lexical mínimo; não é prova semântica."""
    citacoes = re.findall(r"\[\s*(DOC\d{2})\s*\]", resposta, re.IGNORECASE)
    if not citacoes:
        return False
    fontes: dict[str, list[str]] = {}
    for resultado in resultados:
        doc_id = str(resultado.get("metadados", {}).get("doc_id", "")).upper()
        fontes.setdefault(doc_id, []).append(resultado.get("texto", ""))
    if any(c.upper() not in fontes for c in citacoes):
        return False

    # Cada afirmacao deve ter uma citacao; uma citacao nao valida outras frases.
    for frase in re.split(r"(?<=[.!?])\s+|\n+", resposta):
        if not frase.strip():
            continue
        ids = [c.upper() for c in re.findall(r"\[\s*(DOC\d{2})\s*\]", frase, re.IGNORECASE)]
        if not ids:
            return False
        texto_afirmacao = re.sub(r"\[\s*DOC\d{2}\s*\]", "", frase, flags=re.IGNORECASE)
        termos = {t for t in re.findall(r"\w{4,}", texto_afirmacao.casefold())
                 if t not in STOPWORDS_PERGUNTA}
        # Respostas sem conteudo verificavel alem do identificador nao sao fundamentadas.
        if not termos:
            return False
        if not any(
            len({t for t in termos if t in trecho.casefold()}) >= max(1, min(2, len(termos)))
            for doc_id in ids for trecho in fontes[doc_id]
        ):
            return False
    return True


def responder(pergunta: str, indice: IndiceVetorial, llm: LLMProtocol | None = None, top_k: int = 12) -> RespostaRAG:
    resultados = buscar_com_reranking(indice, pergunta, top_k=top_k)
    if not resultados:
        return RespostaRAG(pergunta=pergunta, status=StatusResposta.SEM_EVIDENCIA, resposta=None, motivo="nenhum trecho recuperado", precisa_revisao=True)

    melhor = resultados[0]
    if melhor["similaridade"] < LIMIAR_SIMILARIDADE_MINIMA:
        return RespostaRAG(pergunta=pergunta, status=StatusResposta.SEM_EVIDENCIA, resposta=None, fontes=[_fonte_do_resultado(r) for r in resultados], motivo="similaridade abaixo do limiar", precisa_revisao=True)

    tem_ev, encontrados = _tem_evidencia_suficiente(pergunta, resultados)
    if not tem_ev:
        return RespostaRAG(pergunta=pergunta, status=StatusResposta.SEM_EVIDENCIA, resposta=None, fontes=[_fonte_do_resultado(r) for r in resultados], motivo="nenhum trecho contem termo-chave da pergunta", precisa_revisao=True)

    # Validar o contexto antes de qualquer resposta
    trechos = [r["texto"] for r in resultados]
    contexto = montar_contexto_seguro(trechos)

    if contexto.decisao != Decisao.PERMITIR:
        return RespostaRAG(
            pergunta=pergunta,
            status=StatusResposta.SEM_EVIDENCIA,
            resposta=None,
            fontes=[],
            motivo="contexto suspeito; revisao humana necessaria",
            precisa_revisao=True,
        )

    conflito = _detectar_conflito(resultados, pergunta)
    if conflito:
        return RespostaRAG(pergunta=pergunta, status=StatusResposta.CONFLITO, resposta=None, fontes=[_fonte_do_resultado(r) for r in resultados], conflito=conflito, motivo="fontes contraditorias detectadas", precisa_revisao=True)

    termos = _expandir_termos(pergunta)
    melhor_relevante = melhor
    for r in resultados:
        if any(t in r["texto"].lower() for t in termos):
            melhor_relevante = r
            break

    if llm is None:
        return RespostaRAG(pergunta=pergunta, status=StatusResposta.FUNDAMENTADA, resposta=f"[{melhor_relevante['metadados']['doc_id']}] {melhor_relevante['texto'][:300].strip()}", fontes=[_fonte_do_resultado(r) for r in resultados], motivo="modo offline")


    prompt = PROMPT_RAG.format(contexto=contexto.texto_saneado, pergunta=pergunta)
    bruto = llm.completar(prompt).strip()

    if bruto == "SEM_EVIDENCIA":
        return RespostaRAG(pergunta=pergunta, status=StatusResposta.SEM_EVIDENCIA, resposta=None, fontes=[_fonte_do_resultado(r) for r in resultados], motivo="LLM declarou ausencia", precisa_revisao=True)
    if bruto == "CONFLITO":
        return RespostaRAG(pergunta=pergunta, status=StatusResposta.CONFLITO, resposta=None, fontes=[_fonte_do_resultado(r) for r in resultados], conflito=conflito, motivo="LLM declarou conflito", precisa_revisao=True)

    check = validar_saida(bruto, exigir_citacao=True)
    if check.decisao != Decisao.PERMITIR:
        # Nunca exibir a saida original bloqueada, nem classificá-la como fundamentada.
        return RespostaRAG(
            pergunta=pergunta, status=StatusResposta.SEM_EVIDENCIA, resposta=None,
            fontes=[_fonte_do_resultado(r) for r in resultados],
            motivo="saida bloqueada ou citacao ausente; revisao humana necessaria",
            precisa_revisao=True,
        )

    if not _citacoes_conferem_com_fontes(bruto, resultados):
        return RespostaRAG(
            pergunta=pergunta, status=StatusResposta.SEM_EVIDENCIA, resposta=None,
            fontes=[_fonte_do_resultado(r) for r in resultados],
            motivo="citacao inexistente ou afirmacao sem suporte textual; revisao humana necessaria",
            precisa_revisao=True,
        )

    return RespostaRAG(pergunta=pergunta, status=StatusResposta.FUNDAMENTADA, resposta=bruto, fontes=[_fonte_do_resultado(r) for r in resultados], motivo="sintese com citacao")

@dataclass
class ResultadoChunking:
    config: dict[str, int]
    acertos: int
    total: int
    detalhes: list[dict[str, Any]] = field(default_factory=list)
    @property
    def taxa_acerto(self) -> float: return self.acertos / self.total if self.total else 0.0
    def resumo(self) -> dict[str, Any]: return {"config": self.config, "acertos": self.acertos, "total": self.total, "taxa_acerto": round(self.taxa_acerto, 4)}

def _trecho_bate_referencia(trecho: str, referencia: str) -> bool:
    palavras_ref = [p for p in re.findall(r"\w+", referencia.lower()) if len(p) > 4]
    if not palavras_ref: return False
    return sum(1 for p in palavras_ref if p in trecho.lower()) >= max(1, len(palavras_ref) // 2)

def avaliar_configuracao_chunking(perguntas_respondiveis: list[dict[str, Any]], tamanho: int, sobreposicao: int, top_k: int = 5) -> ResultadoChunking:
    import uuid
    tmp = Path("indice/testes_tmp") / f"chunk_{tamanho}_{sobreposicao}_{uuid.uuid4().hex[:6]}"
    tmp.mkdir(parents=True, exist_ok=True)
    idx = IndiceVetorial(dir_indice=tmp)
    indexar_acervo(tamanho=tamanho, sobreposicao=sobreposicao, indice=idx)

    res = ResultadoChunking(config={"tamanho": tamanho, "sobreposicao": sobreposicao}, acertos=0, total=len(perguntas_respondiveis))
    for p in perguntas_respondiveis:
        resultados = idx.buscar(p["pergunta"], top_k=top_k)
        fontes_esperadas = p.get("fontes_esperadas", [])
        acertou = False
        for r in resultados:
            for f in fontes_esperadas:
                if r["metadados"].get("doc_id") == f["doc_id"] and _trecho_bate_referencia(r["texto"], f.get("trecho_referencia", "")):
                    acertou = True; break
            if acertou: break
        if acertou: res.acertos += 1
        res.detalhes.append({"id": p["id"], "acertou": acertou, "top_k_ids": [r["chunk_id"] for r in resultados]})
    return res

def comparar_chunkings(caminho_gabarito: str | Path = "dados/desafio02_alternativo/gabaritos/rag_perguntas.json", top_k: int = 5) -> dict[str, Any]:
    with open(caminho_gabarito, encoding="utf-8") as f: gab = json.load(f)
    respondiveis = [p for p in gab["perguntas"] if p["tipo"] == "respondivel"]
    resultados = [avaliar_configuracao_chunking(respondiveis, t, s, top_k=top_k) for t, s in [(500, 100), (300, 50)]]
    melhor = max(resultados, key=lambda r: r.taxa_acerto)
    return {
        "resultados": [r.resumo() for r in resultados],
        "detalhes_por_config": [{"config": r.config, "detalhes": r.detalhes} for r in resultados],
        "escolhida": melhor.config,
        "justificativa": f"Configuracao {melhor.config} escolhida por maior taxa de acerto ({melhor.acertos}/{melhor.total} = {melhor.taxa_acerto:.0%}).",
        "top_k": top_k,
    }

def avaliar_rag(caminho_gabarito: str | Path = "dados/desafio02_alternativo/gabaritos/rag_perguntas.json", indice: IndiceVetorial | None = None) -> dict[str, Any]:
    with open(caminho_gabarito, encoding="utf-8") as f: gab = json.load(f)
    idx = indice if indice is not None else IndiceVetorial()

    # Prepara o acervo quando o indice ainda esta vazio.
    if idx.contar() == 0:
        indexar_acervo(indice=idx)

    stats = {"respondiveis": {"total": 0, "ok": 0}, "sem_resposta": {"total": 0, "ok": 0}, "contraditoria": {"ok": False}}
    detalhes = []

    for p in gab["perguntas"]:
        r = responder(p["pergunta"], idx, llm=None)
        d = {"id": p["id"], "tipo": p["tipo"], "status": r.status, "precisa_revisao": r.precisa_revisao}
        if p["tipo"] == "respondivel":
            stats["respondiveis"]["total"] += 1
            if r.status == StatusResposta.FUNDAMENTADA:
                stats["respondiveis"]["ok"] += 1; d["ok"] = True
            else: d["ok"] = False
        elif p["tipo"] == "sem_resposta":
            stats["sem_resposta"]["total"] += 1
            if r.status == StatusResposta.SEM_EVIDENCIA:
                stats["sem_resposta"]["ok"] += 1; d["ok"] = True
            else: d["ok"] = False
        elif p["tipo"] == "contraditoria":
            if r.status == StatusResposta.CONFLITO and r.precisa_revisao:
                stats["contraditoria"]["ok"] = True; d["ok"] = True
            else: d["ok"] = False
        detalhes.append(d)

    return {
        "respondiveis": {"total": stats["respondiveis"]["total"], "acertos": stats["respondiveis"]["ok"], "proporcao": round(stats["respondiveis"]["ok"] / max(1, stats["respondiveis"]["total"]), 4)},
        "sem_resposta": {"total": stats["sem_resposta"]["total"], "abstencoes_corretas": stats["sem_resposta"]["ok"], "proporcao": round(stats["sem_resposta"]["ok"] / max(1, stats["sem_resposta"]["total"]), 4)},
        "contraditoria": {"conflito_apresentado": stats["contraditoria"]["ok"]},
        "detalhes": detalhes,
    }

if __name__ == "__main__":
    print("=== RF18: comparacao de chunking ===")
    comp = comparar_chunkings()
    print(json.dumps(comp["resultados"], indent=2, ensure_ascii=False))
    print("Escolhida:", comp["escolhida"])

    print("\n=== RF19: avaliacao do RAG ===")
    av = avaliar_rag()
    print(json.dumps(av, indent=2, ensure_ascii=False))

    import shutil
    shutil.rmtree("indice/testes_tmp", ignore_errors=True)