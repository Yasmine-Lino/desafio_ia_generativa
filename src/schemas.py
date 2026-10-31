"""Contrato versionado de solicitação e regras de negócio (RF14)."""
import datetime
import json
import re

VERSAO = "2.0"
CAMPOS = ("protocolo", "data", "solicitante", "assunto", "pedido", "categoria", "entidades", "campos_ausentes", "necessita_revisao")
CATEGORIAS = {"matricula", "documentacao", "outros", "revisao"}

class EsquemaInvalido(ValueError):
    pass

def validar(dados, original=""):
    if not isinstance(dados, dict):
        raise EsquemaInvalido("A saída deve ser um objeto JSON")
    extras = set(dados) - set(CAMPOS) - {"versao"}
    ausentes = set(CAMPOS) - set(dados)
    if extras or ausentes:
        raise EsquemaInvalido(f"Chaves extras: {sorted(extras)}; obrigatórias ausentes: {sorted(ausentes)}")
    if dados.get("versao", VERSAO) != VERSAO:
        raise EsquemaInvalido("Versão de esquema incompatível")
    for campo in ("protocolo", "data", "solicitante", "assunto", "pedido"):
        if dados[campo] is not None and not isinstance(dados[campo], str):
            raise EsquemaInvalido(f"Tipo incorreto: {campo}")
    if dados["categoria"] not in CATEGORIAS:
        raise EsquemaInvalido("Categoria não permitida")
    if not isinstance(dados["entidades"], dict) or not isinstance(dados["campos_ausentes"], list) or not isinstance(dados["necessita_revisao"], bool):
        raise EsquemaInvalido("Tipos inválidos em entidades, campos_ausentes ou necessita_revisao")
    for c in dados["campos_ausentes"]:
        if c not in CAMPOS or dados[c] is not None:
            raise EsquemaInvalido("Lista de ausências incoerente")
    for c in ("protocolo", "data", "solicitante", "assunto", "pedido"):
        if dados[c] is None and c not in dados["campos_ausentes"]:
            raise EsquemaInvalido(f"Ausência não declarada: {c}")
    if dados["data"]:
        try: datetime.datetime.strptime(dados["data"], "%d/%m/%Y")
        except ValueError: raise EsquemaInvalido("Data inválida") from None
    if original:
        for campo in ("protocolo", "data", "solicitante"):
            if dados[campo] and dados[campo].casefold() not in original.casefold():
                raise EsquemaInvalido(f"{campo} não consta na entrada")
    return dados

def comparar_json(texto, original=""):
    try: obj = json.loads(texto)
    except json.JSONDecodeError as e: return {"json_sintatico": False, "esquema_valido": False, "erro": str(e)}
    try: validar(obj, original); return {"json_sintatico": True, "esquema_valido": True, "erro": None}
    except EsquemaInvalido as e: return {"json_sintatico": True, "esquema_valido": False, "erro": str(e)}
