"""Contrato canônico para adaptar saídas de RAG sem alterar o projeto legado."""
from dataclasses import dataclass, field

@dataclass
class RespostaUnificada:
    status: str
    resposta: str | None
    fontes: list = field(default_factory=list)
    precisa_revisao: bool = False


def adaptar_resposta_lexical(resultado: dict) -> RespostaUnificada:
    status = resultado.get("status", "revisar")
    return RespostaUnificada(
        status=status,
        resposta=resultado.get("resposta"),
        fontes=resultado.get("fontes") or [],
        precisa_revisao=status != "fundamentada (extrativa)",
    )


def adaptar_resposta_semantica(resultado) -> RespostaUnificada:
    status = str(getattr(resultado, "status", "revisar"))
    return RespostaUnificada(
        status=status,
        resposta=getattr(resultado, "resposta", None),
        fontes=list(getattr(resultado, "fontes", []) or []),
        precisa_revisao=bool(getattr(resultado, "precisa_revisao", True)),
    )
