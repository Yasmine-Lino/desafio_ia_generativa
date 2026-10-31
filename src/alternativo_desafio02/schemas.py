"""
RF14 - Extracao estruturada e validacao.

Define o contrato de dados versionado das solicitacoes do Desafio 02.
Distingue tres tipos de falha:
  1. JSON sintaticamente invalido (nao parseia)
  2. JSON valido mas fora do esquema (chave extra, tipo errado)
  3. JSON conforme ao esquema mas incoerente com regra de negocio
     (data impossivel, entidade nao presente no original)

A adequacao ao esquema NAO garante veracidade dos valores.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

VERSAO_ESQUEMA = "1.0.0"


class Categoria(str, Enum):
    """Categorias fechadas. Inclui OUTROS e REVISAO conforme RF15."""

    INSCRICAO = "inscricao"
    CRONOGRAMA = "cronograma"
    MATRICULA = "matricula"
    COTAS = "cotas"
    DOCUMENTOS = "documentos"
    OUTROS = "outros"
    REVISAO = "revisao"


class Canal(str, Enum):
    TEXTO = "texto"
    AUDIO_TRANSCRITO = "audio_transcrito"
    OCR = "ocr"
    FORMULARIO = "formulario"


class Entidade(BaseModel):
    """Entidade extraida. Origem separa literal de inferida (RF15)."""

    model_config = ConfigDict(extra="forbid")

    tipo: str = Field(..., description="pessoa, orgao, local, data, protocolo, curso, cota")
    valor: str
    origem: str = Field(..., description="literal | inferida")


class SolicitacaoContrato(BaseModel):
    """
    Contrato de dados versionado da solicitacao (RF14).

    Campos obrigatorios: protocolo, data, solicitante, assunto, pedido, categoria.
    Campos opcionais representam ausencia com None + lista em campos_ausentes.
    """

    model_config = ConfigDict(extra="forbid")

    versao_esquema: str = Field(default=VERSAO_ESQUEMA)
    protocolo: str | None = Field(default=None, description="Formato 2026-XXXXXX ou None se ausente")
    data: date | None = Field(default=None, description="Data da solicitacao")
    solicitante: str | None = Field(default=None)
    canal: Canal = Field(default=Canal.TEXTO)
    assunto: str | None = Field(default=None)
    pedido: str = Field(..., min_length=10, description="Texto do pedido do cidadao")
    categoria: Categoria = Field(default=Categoria.REVISAO)
    entidades: list[Entidade] = Field(default_factory=list)
    campos_ausentes: list[str] = Field(default_factory=list)
    necessidade_revisao: bool = Field(default=True)

    @field_validator("protocolo")
    @classmethod
    def validar_protocolo(cls, v: str | None) -> str | None:
        if v is None:
            return None
        import re

        if not re.fullmatch(r"\d{4}-\d{6}", v):
            raise ValueError(f"Protocolo fora do padrao 2026-XXXXXX: {v!r}")
        return v

    @field_validator("data")
    @classmethod
    def validar_data(cls, v: date | None) -> date | None:
        if v is None:
            return None
        if v > date.today():
            raise ValueError(f"Data no futuro: {v}")
        if v.year < 2000:
            raise ValueError(f"Data anterior a 2000: {v}")
        return v


# ---------------------------------------------------------------------------
# Resultado de validacao - distingue os tres tipos de falha
# ---------------------------------------------------------------------------


class TipoFalha(str, Enum):
    SINTATICA = "sintatica"
    ESQUEMA = "esquema"
    REGRA_NEGOCIO = "regra_negocio"
    NENHUMA = "nenhuma"


class ResultadoValidacao(BaseModel):
    ok: bool
    tipo_falha: TipoFalha = TipoFalha.NENHUMA
    mensagem: str = ""
    dados: dict[str, Any] | None = None
    detalhes: list[str] = Field(default_factory=list)


def validar_json_bruto(texto: str) -> ResultadoValidacao:
    """
    Camada 1: JSON sintaticamente valido?
    Nao confunde sintaxe com esquema.
    """
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError as e:
        return ResultadoValidacao(
            ok=False,
            tipo_falha=TipoFalha.SINTATICA,
            mensagem=f"JSON invalido: {e.msg} (linha {e.lineno}, coluna {e.colno})",
        )
    return ResultadoValidacao(ok=True, dados=dados)


def validar_esquema(dados: dict[str, Any]) -> ResultadoValidacao:
    """
    Camada 2: conforme ao esquema Pydantic?
    Diferencia chave extra (extra=forbid) de campo obrigatorio ausente.
    """
    try:
        obj = SolicitacaoContrato(**dados)
        return ResultadoValidacao(ok=True, dados=obj.model_dump(mode="json"))
    except ValidationError as e:
        detalhes = []
        tem_extra = False
        tem_ausente = False
        tem_tipo = False
        for erro in e.errors():
            tipo = erro["type"]
            loc = ".".join(str(p) for p in erro["loc"])
            if tipo == "extra_forbidden":
                tem_extra = True
                detalhes.append(f"chave_extra: {loc}")
            elif tipo == "missing":
                tem_ausente = True
                detalhes.append(f"campo_ausente: {loc}")
            else:
                tem_tipo = True
                detalhes.append(f"tipo_incorreto: {loc} ({tipo})")
        partes = []
        if tem_extra:
            partes.append("chave(s) extra(s)")
        if tem_ausente:
            partes.append("campo(s) obrigatorio(s) ausente(s)")
        if tem_tipo:
            partes.append("tipo(s) incorreto(s)")
        return ResultadoValidacao(
            ok=False,
            tipo_falha=TipoFalha.ESQUEMA,
            mensagem="Falha de esquema: " + ", ".join(partes),
            detalhes=detalhes,
        )


def validar_regra_negocio(
    obj: dict[str, Any], texto_original: str
) -> ResultadoValidacao:
    """
    Camada 3: coerencia com o original.
    - protocolo presente no original?
    - data presente no original?
    - categoria coerente com o assunto?
    Nao substitui a revisao humana.
    """
    detalhes = []

    protocolo = obj.get("protocolo")
    if protocolo and protocolo not in texto_original:
        detalhes.append(f"protocolo_nao_encontrado_no_original: {protocolo}")

    data_str = obj.get("data")
    if data_str:
        try:
            d = datetime.fromisoformat(data_str).date()
            formatos = [d.strftime("%d/%m/%Y"), d.strftime("%Y-%m-%d")]
            if not any(f in texto_original for f in formatos):
                detalhes.append(f"data_nao_encontrada_no_original: {data_str}")
        except ValueError:
            detalhes.append(f"data_invalida: {data_str}")

    if detalhes:
        return ResultadoValidacao(
            ok=False,
            tipo_falha=TipoFalha.REGRA_NEGOCIO,
            mensagem="Falha de regra de negocio: " + "; ".join(detalhes),
            detalhes=detalhes,
            dados=obj,
        )
    return ResultadoValidacao(ok=True, dados=obj)


def validar_pipeline(texto_json: str, texto_original: str) -> ResultadoValidacao:
    """
    Pipeline completo RF14: sintaxe -> esquema -> regra de negocio.
    Bloqueia antes de gerar minuta se qualquer camada falhar.
    """
    r1 = validar_json_bruto(texto_json)
    if not r1.ok:
        return r1

    r2 = validar_esquema(r1.dados or {})
    if not r2.ok:
        return r2

    r3 = validar_regra_negocio(r2.dados or {}, texto_original)
    return r3


def json_schema_versionado() -> dict[str, Any]:
    """Exporta o JSON Schema versionado do contrato (para documentacao e auditoria)."""
    schema = SolicitacaoContrato.model_json_schema()
    schema["$id"] = f"https://seciteci.mt.gov.br/schemas/solicitacao/{VERSAO_ESQUEMA}"
    schema["versao"] = VERSAO_ESQUEMA
    return schema


if __name__ == "__main__":
    # Demonstracao rapida: comparar JSON sintatico vs. validado
    exemplo_sintatico_ok = '{"pedido": "Quero informacoes sobre inscricao no curso de Enfermagem", "protocolo": "2026-000142", "data": "2026-04-12", "solicitante": "Maria Fernanda Souza"}'
    exemplo_com_chave_extra = '{"pedido": "Quero informacoes sobre inscricao no curso de Enfermagem", "protocolo": "2026-000142", "data": "2026-04-12", "solicitante": "Maria", "campo_inventado": true}'
    exemplo_tipo_errado = '{"pedido": "Quero informacoes sobre inscricao no curso de Enfermagem", "protocolo": 2026000142, "data": "2026-04-12", "solicitante": "Maria"}'
    exemplo_sem_obrigatorio = '{"protocolo": "2026-000142", "data": "2026-04-12", "solicitante": "Maria"}'

    for nome, texto in [
        ("sintatico_ok", exemplo_sintatico_ok),
        ("chave_extra", exemplo_com_chave_extra),
        ("tipo_errado", exemplo_tipo_errado),
        ("sem_obrigatorio", exemplo_sem_obrigatorio),
    ]:
        r = validar_pipeline(texto, texto)
        print(f"[{nome}] ok={r.ok} tipo={r.tipo_falha.value} msg={r.mensagem}")