"""
RF15 - Sumarizacao, classificacao e extracao de entidades.

Gera uma ficha de compreensao de cada solicitacao:
  - resumo de ate 100 palavras, sem inventar dados
  - categoria de um enum fechado
  - entidades separando literal de inferida

A avaliacao contra gabarito e feita separadamente (avaliar_contra_gabarito),
para poder ser testada sem chamar LLM.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Protocol

from src.schemas import Categoria, Entidade

MAX_PALAVRAS_RESUMO = 100

# Categorias que o classificador pode retornar (enum fechado)
CATEGORIAS_VALIDAS = {c.value for c in Categoria}


class LLMProtocol(Protocol):
    """Interface minima do cliente LLM (injeta mock nos testes)."""

    def completar(self, prompt: str, **kwargs: Any) -> str: ...


@dataclass
class FichaCompreensao:
    """Saida estruturada do RF15 para uma solicitacao."""

    resumo: str
    categoria: str
    entidades: list[Entidade] = field(default_factory=list)
    campos_ausentes: list[str] = field(default_factory=list)
    necessidade_revisao: bool = False
    erros: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Prompts (versionados em prompts/ tambem, mas aqui ficam como constante)
# ---------------------------------------------------------------------------

PROMPT_RESUMO = """Resuma a solicitacao a seguir em no maximo {max_palavras} palavras.
Regras:
- Nao invente dados que nao estejam no texto.
- Preserve os fatos essenciais: curso, local, cota, prazo, pedido.
- Nao complete informacoes ausentes.
- Responda apenas com o resumo, sem preambulo.

Solicitacao:
{texto}
"""

PROMPT_CATEGORIA = """Classifique a solicitacao em UMA das categorias abaixo:
{lista}

Se o pedido for ambiguo ou faltar informacao para classificar, use "revisao".
Se nao se encaixar em nenhuma, use "outros".
Responda apenas com a categoria, em minusculas.

Solicitacao:
{texto}
"""

PROMPT_ENTIDADES = """Extraia entidades da solicitacao.
Tipos: pessoa, orgao, local, data, protocolo, curso, cota.
Para cada entidade, informe tipo, valor e origem:
- literal: aparece textualmente no texto
- inferida: deduzida do contexto (ex.: ETEC implicita pela cidade)
Nao complete entidades ausentes por suposicao.
Responda em JSON: {{"entidades": [{{"tipo": "...", "valor": "...", "origem": "..."}}], "ausentes": ["..."]}}

Solicitacao:
{texto}
"""


# ---------------------------------------------------------------------------
# Funcoes de NLP (chamam LLM)
# ---------------------------------------------------------------------------


def resumir(texto: str, llm: LLMProtocol, max_palavras: int = MAX_PALAVRAS_RESUMO) -> str:
    """Gera resumo com limite de palavras. Trunca se o LLM exceder."""
    prompt = PROMPT_RESUMO.format(max_palavras=max_palavras, texto=texto)
    resposta = llm.completar(prompt).strip()
    return _truncar_palavras(resposta, max_palavras)


def classificar(texto: str, llm: LLMProtocol) -> str:
    """Classifica em categoria fechada. Fora do enum -> revisao."""
    lista = ", ".join(sorted(CATEGORIAS_VALIDAS))
    prompt = PROMPT_CATEGORIA.format(lista=lista, texto=texto)
    resposta = llm.completar(prompt).strip().lower()
    # Normaliza: pega so a primeira palavra se vier frase
    token = re.split(r"[\s,.;]", resposta, maxsplit=1)[0]
    if token in CATEGORIAS_VALIDAS:
        return token
    return Categoria.REVISAO.value


def extrair_entidades(texto: str, llm: LLMProtocol) -> tuple[list[Entidade], list[str]]:
    """
    Extrai entidades e campos ausentes.
    Retorna (entidades, campos_ausentes).
    Nunca inventa: se o LLM alucinar, o avaliador detecta.
    """
    prompt = PROMPT_ENTIDADES.format(texto=texto)
    resposta = llm.completar(prompt).strip()
    try:
        dados = json.loads(resposta)
    except json.JSONDecodeError:
        return [], ["resposta_llm_invalida"]

    entidades = []
    for item in dados.get("entidades", []):
        if not isinstance(item, dict):
            continue
        try:
            entidades.append(
                Entidade(
                    tipo=str(item.get("tipo", "")),
                    valor=str(item.get("valor", "")),
                    origem=str(item.get("origem", "literal")),
                )
            )
        except Exception:
            continue
    ausentes = [str(x) for x in dados.get("ausentes", [])]
    return entidades, ausentes


def gerar_ficha(texto: str, llm: LLMProtocol) -> FichaCompreensao:
    """Pipeline RF15 completo sobre uma solicitacao."""
    ficha = FichaCompreensao(resumo="", categoria=Categoria.REVISAO.value)
    try:
        ficha.resumo = resumir(texto, llm)
        ficha.categoria = classificar(texto, llm)
        ficha.entidades, ficha.campos_ausentes = extrair_entidades(texto, llm)
        ficha.necessidade_revisao = (
            ficha.categoria == Categoria.REVISAO.value or bool(ficha.campos_ausentes)
        )
    except Exception as e:  # noqa: BLE001
        ficha.erros.append(f"falha no pipeline: {e}")
        ficha.necessidade_revisao = True
    return ficha


# ---------------------------------------------------------------------------
# Avaliacao contra gabarito (sem LLM) - calcula acuracia e omissoes
# ---------------------------------------------------------------------------


@dataclass
class ResultadoAvaliacao:
    total: int = 0
    acertos_categoria: int = 0
    omissoes_entidade: int = 0
    entidades_incorretas: int = 0
    fatos_sem_suporte: int = 0
    detalhes: list[dict[str, Any]] = field(default_factory=list)

    @property
    def acuracia_categoria(self) -> float:
        return self.acertos_categoria / self.total if self.total else 0.0

    def resumo(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "acertos_categoria": self.acertos_categoria,
            "acuracia_categoria": round(self.acuracia_categoria, 4),
            "omissoes_entidade": self.omissoes_entidade,
            "entidades_incorretas": self.entidades_incorretas,
            "fatos_sem_suporte": self.fatos_sem_suporte,
        }


def _normalizar(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def avaliar_contra_gabarito(
    fichas: dict[str, FichaCompreensao],
    gabarito: dict[str, Any],
) -> ResultadoAvaliacao:
    """
    Compara as fichas com o gabarito de solicitacoes.
    - acerto de categoria: ficha.categoria == gabarito.categoria_esperada
    - omissao de entidade: entidade esperada ausente na ficha
    - entidade incorreta: entidade na ficha que nao esta no gabarito
    - fato sem suporte: fato essencial do gabarito ausente no resumo
    """
    res = ResultadoAvaliacao()
    for sol in gabarito["solicitacoes"]:
        sid = sol["id"]
        ficha = fichas.get(sid)
        if ficha is None:
            continue
        res.total += 1

        # categoria
        if ficha.categoria == sol["categoria_esperada"]:
            res.acertos_categoria += 1

        # entidades esperadas por tipo
        esperadas: set[tuple[str, str]] = set()
        for tipo, valores in sol["entidades_esperadas"].items():
            for v in valores:
                esperadas.add((tipo, _normalizar(v)))

        obtidas: set[tuple[str, str]] = {
            (e.tipo, _normalizar(e.valor)) for e in ficha.entidades
        }

        omissoes = esperadas - obtidas
        incorretas = obtidas - esperadas
        res.omissoes_entidade += len(omissoes)
        res.entidades_incorretas += len(incorretas)

        # fatos essenciais no resumo
        resumo_norm = _normalizar(ficha.resumo)
        fatos_ausentes = [
            fato
            for fato in sol["resumo_fatos_essenciais"]
            if not _contem_fato(resumo_norm, _normalizar(fato))
        ]
        res.fatos_sem_suporte += len(fatos_ausentes)

        res.detalhes.append(
            {
                "id": sid,
                "categoria_esperada": sol["categoria_esperada"],
                "categoria_obtida": ficha.categoria,
                "omissoes": sorted(omissoes),
                "incorretas": sorted(incorretas),
                "fatos_ausentes_no_resumo": fatos_ausentes,
            }
        )
    return res


def _contem_fato(resumo_norm: str, fato_norm: str) -> bool:
    """Verifica se um fato essencial aparece no resumo (match parcial por palavras-chave)."""
    palavras = [p for p in re.findall(r"\w+", fato_norm) if len(p) > 3]
    if not palavras:
        return True
    return sum(1 for p in palavras if p in resumo_norm) >= max(1, len(palavras) // 2)


def _truncar_palavras(texto: str, limite: int) -> str:
    palavras = texto.split()
    if len(palavras) <= limite:
        return texto
    return " ".join(palavras[:limite])


def carregar_gabarito(caminho: str | Path = "dados/gabaritos/solicitacoes.json") -> dict[str, Any]:
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def carregar_solicitacao(sol_id: str) -> str:
    caminho = Path(f"dados/solicitacoes/{sol_id}.txt")
    return caminho.read_text(encoding="utf-8")


if __name__ == "__main__":
    # Demonstracao com LLM falso (nao chama API)
    class FakeLLM:
        def completar(self, prompt: str, **kwargs: Any) -> str:
            if "Resuma" in prompt:
                return "Cidadao solicita informacoes sobre inscricao no curso de Enfermagem da ETEC Cuiaba, cota L2, documentos e prazo."
            if "Classifique" in prompt:
                return "inscricao"
            return '{"entidades": [{"tipo": "curso", "valor": "Tecnico em Enfermagem", "origem": "literal"}], "ausentes": []}'

    llm = FakeLLM()
    texto = carregar_solicitacao("sol01")
    ficha = gerar_ficha(texto, llm)
    print("Resumo:", ficha.resumo)
    print("Categoria:", ficha.categoria)
    print("Entidades:", [(e.tipo, e.valor, e.origem) for e in ficha.entidades])
    print("Revisao:", ficha.necessidade_revisao)