"""Ficha de compreensão por extração literal, sem inferir ausências (RF14/15)."""
import re
from .schemas import validar, VERSAO
from .guardrails import avaliar_texto

CATEGORIAS = {"matricula": ("matrícula", "matricula", "inscrição", "inscricao", "vaga"), "documentacao": ("documento", "comprovante", "histórico", "historico", "certidão")}

def ficha(texto):
    triagem=avaliar_texto(texto)
    if triagem["decisao"]=="bloquear": raise ValueError(triagem["motivo"])
    protocolo=re.search(r"(?i)\b(?:protocolo|código)\s*[:#-]?\s*([\w/-]{4,})",texto)
    data=re.search(r"\b\d{2}/\d{2}/\d{4}\b",texto)
    nome=re.search(r"(?im)^\s*(?:solicitante|nome)\s*:\s*([^\n]+)",texto)
    assunto=re.search(r"(?im)^\s*assunto\s*:\s*([^\n]+)",texto)
    categoria=next((k for k,palavras in CATEGORIAS.items() if any(p in texto.lower() for p in palavras)),"outros")
    if triagem["decisao"]=="revisar": categoria="revisao"
    valores={"protocolo":protocolo.group(1) if protocolo else None,"data":data.group() if data else None,"solicitante":nome.group(1).strip() if nome else None,"assunto":assunto.group(1).strip() if assunto else None,"pedido":texto.strip() if texto.strip() else None}
    # O protocolo só é validado contra a entrada completa, e nunca gerado por suposição.
    ausentes=[k for k,v in valores.items() if v is None]
    entidades={"pessoas": [valores["solicitante"]] if valores["solicitante"] else [],"datas": [valores["data"]] if valores["data"] else [],"protocolos": [valores["protocolo"]] if valores["protocolo"] else [],"orgaos":[],"locais":[]}
    import unicodedata
    texto_normalizado = unicodedata.normalize("NFKD", texto.casefold())
    texto_normalizado = "".join(
        c for c in texto_normalizado if not unicodedata.combining(c)
    )
    tem_matricula = any(
        termo in texto_normalizado for termo in ("matricula", "inscricao")
    )
    tem_segunda_via = "segunda via" in texto_normalizado
    multiplos_assuntos = tem_matricula and tem_segunda_via
    dados={"versao":VERSAO,**valores,"categoria":categoria,"entidades":entidades,"campos_ausentes":ausentes,"necessita_revisao":bool(ausentes) or triagem["decisao"]!="permitir" or multiplos_assuntos}
    validar(dados,texto)
    frases=re.split(r"(?<=[.!?])\s+",texto.strip())
    resumo=" ".join(frases[:3]); resumo=" ".join(resumo.split()[:100])
    return {"estrutura":dados,"resumo":resumo,"categoria":categoria,"entidades":entidades,"triagem":triagem,"inferencia":[]}
