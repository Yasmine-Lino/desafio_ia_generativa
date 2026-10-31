"""Limites e triagem local conservadora (RF16)."""
import re
from pathlib import Path
MAX_CARACTERES = 12000
MAX_ARQUIVO = 5 * 1024 * 1024
EXTENSOES = {".txt", ".pdf"}


ATAQUES = [
    r"ignore\s+(?:todas?\s+)?(?:as\s+)?instrucoes",
    r"revele?\s+(?:a\s+)?(?:chave|senha|token)",
    r"api[_ -]?key|system prompt",
    r"desative?\s+(?:a\s+)?seguranca",
    r"finja que\s+(?:e|voce e)\s+(?:o\s+)?sistema",
    r"envie?\s+(?:automaticamente|sem revisao)"
]

def avaliar_texto(texto):
    import unicodedata

    if not isinstance(texto, str) or not texto.strip():
        return {"decisao": "bloquear", "motivo": "entrada vazia"}

    if len(texto) > MAX_CARACTERES:
        return {"decisao": "bloquear", "motivo": "limite de caracteres"}

    normalizado = unicodedata.normalize("NFKD", texto.casefold())
    normalizado = "".join(
        caractere for caractere in normalizado
        if not unicodedata.combining(caractere)
    )

    if any(re.search(p, normalizado, re.I) for p in ATAQUES):
        return {
            "decisao": "revisar",
            "motivo": "possivel instrucao adversarial"
        }

    if re.search(r"(violencia|ameaca|explosivo)", normalizado, re.I):
        return {
            "decisao": "revisar",
            "motivo": "triagem de seguranca"
        }

    return {"decisao": "permitir", "motivo": "triagem local"}

def validar_arquivo(caminho):
    p=Path(caminho)
    if p.suffix.lower() not in EXTENSOES or not p.is_file() or p.stat().st_size>MAX_ARQUIVO:
        raise ValueError("Arquivo ausente, excessivo ou extensão não permitida")
    assinatura=p.read_bytes()[:5]
    if p.suffix.lower()==".pdf" and not assinatura.startswith(b"%PDF-"):
        raise ValueError("Assinatura PDF inválida")
    return p
