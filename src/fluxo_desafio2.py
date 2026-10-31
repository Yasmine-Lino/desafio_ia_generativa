"""Fluxo textual integrado e revisão humana persistida, sem envio automático."""
import datetime
import json
import uuid
from pathlib import Path
from .nlp import ficha
from .embeddings import Indice
from .rag import responder
from .guardrails import avaliar_texto

def executar(texto,indice,arquivo_log="resultados/logs/desafio2.jsonl"):
    id_exec=str(uuid.uuid4());inicio=datetime.datetime.now(datetime.timezone.utc).isoformat()
    dados=ficha(texto)
    pergunta=dados["estrutura"]["assunto"] or texto[:150]
    rag=responder(pergunta,indice)
    status="pendente" if rag["status"].startswith("fundamentada") and not dados["estrutura"]["necessita_revisao"] else "revisar"
    resultado={"id":id_exec,"inicio":inicio,"esquema":"2.0","prompt":"extrativo-v1","indice":indice.dados["versao_indice"],"consulta":"[minimizada]","ids_recuperados":[x["id"] for x in rag["trechos"]],"ficha":dados,"rag":rag,"status":status,"decisao_humana":None,"envio_automatico":False}
    log=Path(arquivo_log);log.parent.mkdir(parents=True,exist_ok=True)
    with log.open("a",encoding="utf-8") as f:f.write(json.dumps({k:v for k,v in resultado.items() if k not in ("ficha","rag")},ensure_ascii=False)+"\n")
    return resultado

def revisar(resultado,decisao,justificativa,destino="resultados/minutas/revisoes_desafio2.jsonl"):
    if decisao not in ("aprovada","rejeitada","revisar") or not justificativa.strip():raise ValueError("Decisão e justificativa obrigatórias")
    if resultado["status"]=="revisar" and decisao=="aprovada":raise ValueError("Não aprovar caso sem evidência ou com inconsistências")
    registro={"id":resultado["id"],"decisao":decisao,"justificativa":justificativa,"horario":datetime.datetime.now(datetime.timezone.utc).isoformat(),"ia_participou":True}
    p=Path(destino);p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("a",encoding="utf-8") as f:f.write(json.dumps(registro,ensure_ascii=False)+"\n")
    return registro


def executar_provedor(
    pergunta,
    contexto,
    modo=None,
    arquivo_log="resultados/logs/provedores_desafio2.jsonl"
):
    """Executa um provedor e registra sucesso ou falha."""
    from .provedor_desafio2 import gerar, carregar_config_desafio2

    config = carregar_config_desafio2()
    provedor = modo if modo is not None else config["provedor_principal"]

    registro = {
        "id": str(uuid.uuid4()),
        "horario": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
        "provedor_solicitado": provedor,
        "status": None,
        "erro_tipo": None,
        "modelo": None,
        "tokens": None,
        "envio_automatico": False
    }

    try:
        resultado = gerar(pergunta, contexto, modo=provedor)
        registro["status"] = "sucesso"
        registro["modelo"] = resultado.get("modelo")
        registro["tokens"] = resultado.get("tokens")
        return resultado

    except Exception as erro:
        registro["status"] = "falha"
        registro["erro_tipo"] = type(erro).__name__
        raise

    finally:
        log = Path(arquivo_log)
        log.parent.mkdir(parents=True, exist_ok=True)

        with log.open("a", encoding="utf-8") as f:
            f.write(
                json.dumps(registro, ensure_ascii=False) + "\n"
            )


def executar_rag_provedor(
    pergunta,
    indice,
    modo=None,
    arquivo_log="resultados/logs/provedores_desafio2.jsonl"
):
    """Consulta o RAG antes de utilizar um provedor externo."""
    from .rag import responder
    from .provedor_desafio2 import carregar_config_desafio2

    config = carregar_config_desafio2()
    provedor = modo if modo is not None else config["provedor_principal"]

    if provedor not in ("openai", "gemini"):
        raise ValueError("Provedor externo nao configurado")

    rag = responder(pergunta, indice)

    if rag["status"] != "fundamentada (extrativa)":
        registro = {
            "id": str(uuid.uuid4()),
            "horario": datetime.datetime.now(
                datetime.timezone.utc
            ).isoformat(),
            "provedor_solicitado": provedor,
            "status": "bloqueado_rag",
            "motivo": rag["status"],
            "erro_tipo": None,
            "modelo": None,
            "tokens": None,
            "envio_automatico": False
        }

        log = Path(arquivo_log)
        log.parent.mkdir(parents=True, exist_ok=True)

        with log.open("a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")

        return {
            "status": "revisar",
            "rag": rag,
            "geracao": None,
            "provedor_solicitado": provedor,
            "envio_automatico": False
        }

    partes = []

    for trecho in rag["trechos"]:
        partes.append(
            "Documento: " + str(trecho["documento"]) + "\n"
            + "Versao: " + str(trecho["versao"]) + "\n"
            + "Pagina: " + str(trecho["pagina"]) + "\n"
            + "Conteudo: " + trecho["texto"]
        )

    contexto = "\n\n".join(partes)

    try:
        geracao = executar_provedor(
            pergunta,
            contexto,
            modo=provedor,
            arquivo_log=arquivo_log
        )
    except Exception as erro:
        return {
            "status": "revisar",
            "rag": rag,
            "geracao": None,
            "provedor_solicitado": provedor,
            "erro_tipo": type(erro).__name__,
            "envio_automatico": False
        }

    return {
        "status": "revisar",
        "rag": rag,
        "geracao": geracao,
        "provedor_solicitado": provedor,
        "envio_automatico": False
    }
