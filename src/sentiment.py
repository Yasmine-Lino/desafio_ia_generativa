"""
RF22 - Classificacao de sentimentos das avaliacoes de atendimento.

- Retorna ID, polaridade (positiva/negativa/neutra/indeterminada), justificativa e revisao.
- Regra para mensagens mistas, ironia e falta de contexto: admitir indeterminacao.
- Confianca do modelo e estimativa nao calibrada: nao usar como probabilidade.
- Nao inferir personalidade, diagnostico ou caracteristica sensivel.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol

POLARIDADES = {"positiva", "negativa", "neutra", "indeterminada"}


class LLMProtocol(Protocol):
    def completar(self, prompt: str, **kwargs: Any) -> str: ...


@dataclass
class ResultadoSentimento:
    id: str
    polaridade: str
    justificativa: str
    precisa_revisao: bool = False


PROMPT_SENTIMENTO = """Classifique o sentimento da avaliacao de atendimento abaixo.
Opcoes: positiva, negativa, neutra, indeterminada.
Regras:
- Se houver elogio e critica misturados, ou ironia, use indeterminada.
- Nao infira personalidade, diagnostico ou caracteristica sensivel do autor.
- Responda em JSON: {{"polaridade": "...", "justificativa": "..."}}

Avaliacao:
{texto}
"""


def classificar_sentimento(texto: str, llm: LLMProtocol) -> tuple[str, str]:
    """Retorna (polaridade, justificativa). Forca indeterminada fora do enum."""
    prompt = PROMPT_SENTIMENTO.format(texto=texto)
    resposta = llm.completar(prompt).strip()
    try:
        dados = json.loads(resposta)
        pol = str(dados.get("polaridade", "indeterminada")).lower()
        just = str(dados.get("justificativa", ""))
    except json.JSONDecodeError:
        return "indeterminada", "resposta do LLM invalida"
    if pol not in POLARIDADES:
        pol = "indeterminada"
    return pol, just


def classificar_avaliacao(aval_id: str, texto: str, llm: LLMProtocol) -> ResultadoSentimento:
    pol, just = classificar_sentimento(texto, llm)
    return ResultadoSentimento(
        id=aval_id,
        polaridade=pol,
        justificativa=just,
        precisa_revisao=(pol == "indeterminada"),
    )


def avaliar_contra_gabarito(
    resultados: dict[str, ResultadoSentimento],
    gabarito: dict[str, Any],
) -> dict[str, Any]:
    """Compara com o gabarito de sentimentos e calcula acuracia."""
    total = 0
    acertos = 0
    ambiguidades_corretas = 0
    total_ambiguas = 0
    detalhes = []

    for aval in gabarito["avaliacoes"]:
        aid = aval["id"]
        if aid not in resultados:
            continue
        total += 1
        esperado = aval["rotulo_esperado"]
        obtido = resultados[aid].polaridade
        ok = obtido == esperado
        if ok:
            acertos += 1
        if esperado == "indeterminada":
            total_ambiguas += 1
            if obtido == "indeterminada":
                ambiguidades_corretas += 1
        detalhes.append({"id": aid, "esperado": esperado, "obtido": obtido, "ok": ok})

    return {
        "total": total,
        "acertos": acertos,
        "acuracia": round(acertos / total, 4) if total else 0.0,
        "ambiguas": {
            "total": total_ambiguas,
            "acertos": ambiguidades_corretas,
            "proporcao": round(ambiguidades_corretas / total_ambiguas, 4) if total_ambiguas else 0.0,
        },
        "detalhes": detalhes,
    }


def carregar_gabarito(caminho: str | Path = "dados/gabaritos/sentimentos.json") -> dict[str, Any]:
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    import re as _re

    class FakeLLM:
        def completar(self, prompt: str, **kwargs: Any) -> str:
            texto = prompt.lower()

            # 1) MISTAS: elogio + critica coexistem -> indeterminada
            elogios = [r"\beducado\b", r"\bprestativo\b", r"\bprestativa\b", r"\badorei\b", r"\bbom atendimento\b"]
            criticas = [r"\bmas\b", r"\bdesatualizada\b", r"\bconfuso\b", r"\bnao resolveu\b", r"\bnão resolveu\b", r"\bnao sei\b", r"\bnão sei\b", r"\bsistema ruim\b"]
            tem_elogio = any(_re.search(p, texto) for p in elogios)
            tem_critica = any(_re.search(p, texto) for p in criticas)
            if tem_elogio and tem_critica:
                return '{"polaridade": "indeterminada", "justificativa": "Mensagem mista: elogio e critica"}'
            if _re.search(r"\bnao sei se\b", texto) or _re.search(r"\bnão sei se\b", texto):
                return '{"polaridade": "indeterminada", "justificativa": "Autor declara incerteza"}'

            # 2) NEGATIVAS (palavra inteira)
            negativas = [
                r"\bpessimo\b", r"\bpéssimo\b", r"\bhorrivel\b", r"\bhorrível\b",
                r"\bnao resolveram\b", r"\bnão resolveram\b",
                r"\binsatisfeito\b", r"\binsatisfeita\b",
                r"\bperdi o prazo\b", r"\bninguem atendeu\b", r"\bninguém atendeu\b",
                r"\bfalta de organizacao\b", r"\bfalta de organização\b",
                r"\bfrio\b", r"\bsem empatia\b", r"\bnao recomendo\b", r"\bnão recomendo\b",
                r"\berrada\b",
            ]
            if any(_re.search(p, texto) for p in negativas):
                return '{"polaridade": "negativa", "justificativa": "Critica explicita"}'

            # 3) POSITIVAS (sem ressalva)
            positivas = [
                r"\bexcelente\b", r"\bparabens\b", r"\bparabéns\b",
                r"\botimo\b", r"\bótimo\b", r"\bsatisfeita\b", r"\bsatisfeito\b",
                r"\bmuito bem atendido\b", r"\bmuito bem atendida\b",
                r"\brecomendo\b",
            ]
            ressalvas = [r"\bmas\b", r"\bporem\b", r"\bporém\b", r"\bconfuso\b", r"\bnao sei\b", r"\bnão sei\b"]
            if any(_re.search(p, texto) for p in positivas) and not any(
                _re.search(r, texto) for r in ressalvas
            ):
                return '{"polaridade": "positiva", "justificativa": "Elogio explicito"}'

            # 4) NEUTRAS
            neutras = [
                r"\bdentro do esperado\b", r"\bsem reclamacoes\b", r"\bsem reclamações\b",
                r"\batendimento padrao\b", r"\batendimento padrão\b",
                r"\bnada a destacar\b", r"\bsem nada de excepcional\b", r"\bveio correta\b",
            ]
            if any(_re.search(p, texto) for p in neutras):
                return '{"polaridade": "neutra", "justificativa": "Relato factual"}'

            return '{"polaridade": "indeterminada", "justificativa": "Sem elementos suficientes"}'

    gab = carregar_gabarito()
    llm = FakeLLM()
    resultados = {}
    for aval in gab["avaliacoes"]:
        texto = Path(aval["arquivo"]).read_text(encoding="utf-8")
        resultados[aval["id"]] = classificar_avaliacao(aval["id"], texto, llm)

    av = avaliar_contra_gabarito(resultados, gab)
    print(json.dumps(av, indent=2, ensure_ascii=False))