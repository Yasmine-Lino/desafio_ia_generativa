"""
RF16 - Guardrails, moderacao e limites.

Tres camadas:
  - entrada: tipo/tamanho de arquivo, comprimento, escopo, moderacao
  - processamento: documento recuperado e conteudo nao confiavel;
    delimitacao de contexto; nunca incluir segredos no prompt
  - saida: validar esquema, verificar citacoes, filtrar dados indevidos

Controle de recursos: timeout, no maximo 1 retry, teto de chamadas/tokens.

As regras sao deterministicas e documentadas. Nao dependem apenas da
frase "ignore instrucoes maliciosas" (proibido pelo enunciado).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Decisao(str, Enum):
    PERMITIR = "permitir"
    BLOQUEAR = "bloquear"
    REVISAR = "revisar"


class Camada(str, Enum):
    ENTRADA = "entrada"
    PROCESSAMENTO = "processamento"
    SAIDA = "saida"


@dataclass
class ResultadoGuardrail:
    decisao: Decisao
    camada: Camada
    motivo: str
    detalhes: list[str] = field(default_factory=list)
    texto_saneado: str | None = None


# ---------------------------------------------------------------------------
# Limites de recursos (configuraveis)
# ---------------------------------------------------------------------------

LIMITE_TEXTO_SOLICITACAO = 5000  # caracteres
LIMITE_TEXTO_ACERVO = 20000
TAMANHO_MAX_ARQUIVO_MB = 10
TIMEOUT_SEGUNDOS = 30
MAX_RETRIES = 1
TETO_CHAMADAS_POR_EXECUCAO = 10
TETO_TOKENS_POR_EXECUCAO = 50000

EXTENSOES_PERMITIDAS = {".txt", ".pdf", ".png", ".jpg", ".jpeg", ".mp3", ".mp4", ".wav"}

# Escopo do atendimento (secretaria ficticia de educacao tecnica)
TEMAS_NO_ESCOPO = {
    "inscricao", "matricula", "cota", "cotas", "curso", "cursos", "etec", "etecs",
    "edital", "cronograma", "prazo", "documento", "documentos", "sorteio",
    "classificacao", "vagas", "remanescentes", "heteroidentificacao", "enfermagem",
    "administracao", "agropecuaria", "informatica", "desenvolvimento", "sistemas",
}


# ---------------------------------------------------------------------------
# Padroes de ataque (deterministicos, documentados)
# ---------------------------------------------------------------------------

PADROES_INJECAO = [
    r"\bignore\s+(todas\s+)?(as\s+)?instru[cç][oõ]es\b",
    r"\bignore\s+(all\s+)?(previous\s+)?instructions\b",
    r"\bdesconsidere\s+(as\s+)?regras\b",
    r"\bvoce\s+agora\s+e\s+um\s+administrador\b",
    r"\bmodo\s+desenvolvedor\b",
    r"\bmodo\s+admin\b",
    r"\bjailbreak\b",
    r"\bnota\s+do\s+sistema\b",
    r"\binstru[cç][aã]o\s+do\s+sistema\b",
    r"\bprioridade\s+sobre\s+as\s+regras\b",
    r"\brevele\s+(as\s+)?chaves?\b",
    r"\brevele\s+(as\s+)?credenciais\b",
    r"\bmode\s+the\s+system\b",
]

PADROES_SEGREDO = [
    r"\bapi[_\s-]?key\b",
    r"\bsenha\s+(do|da|de)\b",
    r"\btoken\b",
    r"\bcredencial\b",
    r"\bGEMINI_API_KEY\b",
    r"\bGROQ_API_KEY\b",
    r"\bHF_TOKEN\b",
    r"\b\.env\b",
    r"\bcaminho\s+absoluto\b",
    r"\bc:\\users\\",
]

# Dados que nunca devem sair na resposta
PADROES_DADOS_INDEVIDOS_SAIDA = [
    r"GEMINI_API_KEY\s*=\s*\S+",
    r"GROQ_API_KEY\s*=\s*\S+",
    r"HF_TOKEN\s*=\s*\S+",
    r"(?i)senha\s*[:=]\s*\S+",
    r"[A-Za-z]:\\\\Users\\\\[^\s]+",
]


# ---------------------------------------------------------------------------
# Camada 1: entrada
# ---------------------------------------------------------------------------


def validar_entrada(
    texto: str,
    nome_arquivo: str | None = None,
    tamanho_bytes: int | None = None,
) -> ResultadoGuardrail:
    detalhes = []

    # Tamanho do texto
    if len(texto) > LIMITE_TEXTO_SOLICITACAO:
        return ResultadoGuardrail(
            decisao=Decisao.BLOQUEAR,
            camada=Camada.ENTRADA,
            motivo=f"texto excede {LIMITE_TEXTO_SOLICITACAO} caracteres",
            detalhes=[f"tamanho={len(texto)}"],
        )

    # Tipo e tamanho de arquivo
    if nome_arquivo:
        ext = "." + nome_arquivo.rsplit(".", 1)[-1].lower() if "." in nome_arquivo else ""
        if ext not in EXTENSOES_PERMITIDAS:
            return ResultadoGuardrail(
                decisao=Decisao.BLOQUEAR,
                camada=Camada.ENTRADA,
                motivo=f"extensao nao permitida: {ext}",
            )
        if tamanho_bytes and tamanho_bytes > TAMANHO_MAX_ARQUIVO_MB * 1024 * 1024:
            return ResultadoGuardrail(
                decisao=Decisao.BLOQUEAR,
                camada=Camada.ENTRADA,
                motivo=f"arquivo excede {TAMANHO_MAX_ARQUIVO_MB} MB",
            )

    # Injeção na entrada
    texto_lower = texto.lower()
    for padrao in PADROES_INJECAO:
        if re.search(padrao, texto_lower, re.IGNORECASE):
            return ResultadoGuardrail(
                decisao=Decisao.BLOQUEAR,
                camada=Camada.ENTRADA,
                motivo="tentativa de injecao de instrucao detectada na entrada",
                detalhes=[f"padrao={padrao}"],
            )

    # Tentativa de obter segredo
    for padrao in PADROES_SEGREDO:
        if re.search(padrao, texto_lower, re.IGNORECASE):
            return ResultadoGuardrail(
                decisao=Decisao.BLOQUEAR,
                camada=Camada.ENTRADA,
                motivo="tentativa de obter segredo ou credencial detectada",
                detalhes=[f"padrao={padrao}"],
            )

    # Escopo: se não houver nenhum tema do escopo, revisar
    palavras = set(re.findall(r"\w+", texto_lower))
    if not (palavras & TEMAS_NO_ESCOPO):
        return ResultadoGuardrail(
            decisao=Decisao.REVISAR,
            camada=Camada.ENTRADA,
            motivo="texto fora do escopo de atendimento (nenhum tema institucional reconhecido)",
        )

    return ResultadoGuardrail(
        decisao=Decisao.PERMITIR, camada=Camada.ENTRADA, motivo="entrada valida"
    )


# ---------------------------------------------------------------------------
# Camada 2: processamento (documento recuperado é conteudo nao confiavel)
# ---------------------------------------------------------------------------

TAG_DOC_INICIO = "<documento_nao_confiavel>"
TAG_DOC_FIM = "</documento_nao_confiavel>"


def tratar_documento_recuperado(texto_doc: str) -> ResultadoGuardrail:
    """
    Trata o documento recuperado como nao confiavel:
    - Detecta instrucoes maliciosas dentro do documento
    - Delimita o conteudo
    - Nunca executa o que esta escrito
    """
    detalhes = []
    texto_lower = texto_doc.lower()

    for padrao in PADROES_INJECAO:
        if re.search(padrao, texto_lower, re.IGNORECASE):
            detalhes.append(f"instrucao_maliciosa_em_documento: padrao={padrao}")

    # Delimita o conteudo, com marcacao explicita
    delimitado = f"{TAG_DOC_INICIO}\n{texto_doc}\n{TAG_DOC_FIM}"

    if detalhes:
        return ResultadoGuardrail(
            decisao=Decisao.BLOQUEAR,
            camada=Camada.PROCESSAMENTO,
            motivo="documento recuperado contem instrucao maliciosa; conteudo nao sera usado como comando",
            detalhes=detalhes,
            texto_saneado=delimitado,
        )
    return ResultadoGuardrail(
        decisao=Decisao.PERMITIR,
        camada=Camada.PROCESSAMENTO,
        motivo="documento delimitado como conteudo nao confiavel",
        texto_saneado=delimitado,
    )


def montar_contexto_seguro(trechos: list[str]) -> ResultadoGuardrail:
    """Monta o contexto do RAG delimitando cada trecho e bloqueando injecao."""
    detalhes = []
    partes = []
    bloqueou = False
    for i, trecho in enumerate(trechos):
        r = tratar_documento_recuperado(trecho)
        partes.append(f"[trecho {i + 1}]\n{r.texto_saneado}")
        if r.decisao == Decisao.BLOQUEAR:
            bloqueou = True
            detalhes.extend(r.detalhes)
    decisao = Decisao.REVISAR if bloqueou else Decisao.PERMITIR
    motivo = (
        "um ou mais trechos contem instrucao maliciosa; contexto deve ser revisado"
        if bloqueou
        else "contexto montado com delimitacao explicita"
    )
    return ResultadoGuardrail(
        decisao=decisao,
        camada=Camada.PROCESSAMENTO,
        motivo=motivo,
        detalhes=detalhes,
        texto_saneado="\n\n".join(partes),
    )


# ---------------------------------------------------------------------------
# Camada 3: saida
# ---------------------------------------------------------------------------


def validar_saida(texto_saida: str, exigir_citacao: bool = False) -> ResultadoGuardrail:
    detalhes = []
    texto = texto_saida

    # Remove ou bloqueia dados indevidos
    for padrao in PADROES_DADOS_INDEVIDOS_SAIDA:
        if re.search(padrao, texto, re.IGNORECASE):
            detalhes.append(f"dado_indevido_na_saida: padrao={padrao}")
            texto = re.sub(padrao, "[REMOVIDO]", texto, flags=re.IGNORECASE)

    if detalhes:
        return ResultadoGuardrail(
            decisao=Decisao.BLOQUEAR,
            camada=Camada.SAIDA,
            motivo="saida continha dado indevido ou segredo; removido antes de exibir",
            detalhes=detalhes,
            texto_saneado=texto,
        )

    # Citacao obrigatoria quando a resposta e institucional
    if exigir_citacao and not re.search(r"\[(DOC|fonte|doc)\s*\d+", texto, re.IGNORECASE):
        # Verifica tambem padrao "DOCxx"
        if not re.search(r"\bDOC\d{2}\b", texto):
            return ResultadoGuardrail(
                decisao=Decisao.REVISAR,
                camada=Camada.SAIDA,
                motivo="resposta institucional sem citacao verificavel",
            )

    return ResultadoGuardrail(
        decisao=Decisao.PERMITIR,
        camada=Camada.SAIDA,
        motivo="saida valida",
        texto_saneado=texto,
    )


# ---------------------------------------------------------------------------
# Controle de recursos
# ---------------------------------------------------------------------------


@dataclass
class OrcamentoExecucao:
    """Controla chamadas e tokens por execucao."""

    max_chamadas: int = TETO_CHAMADAS_POR_EXECUCAO
    max_tokens: int = TETO_TOKENS_POR_EXECUCAO
    chamadas: int = 0
    tokens: int = 0
    falhas_transitorias: int = 0

    def pode_chamar(self) -> ResultadoGuardrail:
        if self.chamadas >= self.max_chamadas:
            return ResultadoGuardrail(
                decisao=Decisao.BLOQUEAR,
                camada=Camada.PROCESSAMENTO,
                motivo=f"teto de chamadas atingido ({self.max_chamadas})",
            )
        if self.tokens >= self.max_tokens:
            return ResultadoGuardrail(
                decisao=Decisao.BLOQUEAR,
                camada=Camada.PROCESSAMENTO,
                motivo=f"teto de tokens atingido ({self.max_tokens})",
            )
        return ResultadoGuardrail(
            decisao=Decisao.PERMITIR, camada=Camada.PROCESSAMENTO, motivo="orcamento ok"
        )

    def registrar(self, tokens: int = 0) -> None:
        self.chamadas += 1
        self.tokens += tokens

    def registrar_falha_transitoria(self) -> bool:
        """Retorna True se ainda pode repetir (max 1 retry)."""
        self.falhas_transitorias += 1
        return self.falhas_transitorias <= MAX_RETRIES


if __name__ == "__main__":
    # Demonstracao: os 3 ataques devem ser bloqueados
    import json

    with open("dados/gabaritos/adversariais.json", encoding="utf-8") as f:
        ataques = json.load(f)["ataques"]

    for a in ataques:
        if a["id"] == "adv02":
            with open(a["documento_ficticio"], encoding="utf-8") as f:
                texto = f.read()
            r = tratar_documento_recuperado(texto)
        else:
            r = validar_entrada(a["texto_ataque"])
        print(f"[{a['id']}] decisao={r.decisao.value} motivo={r.motivo}")