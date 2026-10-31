
import re


def minimizar_texto(texto):
    """
    Oculta padrões conhecidos de dados pessoais antes
    do envio de textos fictícios ao provedor de IA.

    Não substitui a revisão humana.
    """
    if not isinstance(texto, str):
        raise ValueError("O conteúdo deve ser um texto.")

    regras = [
        (
            r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
            "[CPF ocultado]",
        ),
        (
            r"\b\d{11}\b",
            "[CPF ocultado]",
        ),
        (
            r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b",
            "[e-mail ocultado]",
        ),
        (
            r"\b(?:\+55\s?)?\(?\d{2}\)?\s?9?\d{4}[-\s]?\d{4}\b",
            "[telefone ocultado]",
        ),
        (
            r"\bCPF\s*[:\-]?\s*[\d.\-]+",
            "[CPF ocultado]",
        ),
        (
            r"\bRG\s*[:\-]?\s*[\d.\-]+",
            "[RG ocultado]",
        ),
        (
            r"\bnasci em\s+\d{2}/\d{2}/\d{4}\b",
            "[data de nascimento ocultada]",
        ),
        (
            r"\bnome da mãe\s*[:,]?\s*[^;\n.]+",
            "[nome da mãe ocultado]",
        ),
        (
            r"\bmeu nome é\s+[^,;\n.]+",
            "meu nome é [solicitante]",
        ),
    ]

    resultado = texto

    for padrao, substituicao in regras:
        resultado = re.sub(
            padrao,
            substituicao,
            resultado,
            flags=re.IGNORECASE,
        )

    return resultado


def minimizar_campos(dados, campos_permitidos):
    """
    Seleciona apenas campos autorizados e minimiza
    valores textuais, sem modificar o dicionário original.
    """
    if not isinstance(dados, dict):
        raise ValueError("Os dados devem ser um dicionário.")

    resultado = {}

    for campo in campos_permitidos:
        valor = dados.get(campo, "não localizado")

        if isinstance(valor, str):
            resultado[campo] = minimizar_texto(valor)
        elif isinstance(valor, list):
            resultado[campo] = [
                minimizar_texto(item)
                if isinstance(item, str)
                else item
                for item in valor
            ]
        else:
            resultado[campo] = valor

    return resultado


# ================== FUNCOES DESAFIO 02 ==================
from typing import Any
from src.audit import registrar_evento

def excluir_documento(doc_id: str, indice: Any = None) -> dict[str, Any]:
    from src.embeddings import IndiceVetorial
    idx = indice or IndiceVetorial()
    removidos = idx.remover_documento(doc_id)
    evento = {"acao": "exclusao_documento", "doc_id": doc_id, "chunks_removidos": removidos}
    registrar_evento("privacidade", evento)
    return evento

def registrar_revisao_humana(texto_solicitacao: str, status: str, justificativa: str, participacao_ia: bool = True, caminho_log: str = "revisoes.jsonl") -> str:
    if status not in {"aprovada", "rejeitada", "revisao"}:
        raise ValueError(f"Status invalido: {status}")
    if status in {"rejeitada", "revisao"} and not justificativa:
        raise ValueError("Justificativa obrigatoria")
    dados = {
        "status": status,
        "justificativa": justificativa,
        "participacao_ia": participacao_ia,
        "texto_solicitacao": texto_solicitacao,
    }
    return registrar_evento("revisao_humana", dados, arquivo_log=caminho_log)
