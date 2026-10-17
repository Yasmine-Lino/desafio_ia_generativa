import json
from pathlib import Path

from src.llm_client import (
    consultar_llm,
    carregar_configuracao,
    ErroLLM,
)


RAIZ = Path(__file__).resolve().parent.parent

ORIGEM = RAIZ / "dados" / "processados" / "rf05_extracao.json"
PROMPT = RAIZ / "prompts" / "rf09_minuta_institucional.txt"
DESTINO = RAIZ / "resultados" / "minutas" / "rf09_minuta.txt"
METADADOS = RAIZ / "resultados" / "minutas" / "rf09_informacoes.json"


def preparar_dados(dados):
    """Seleciona somente as informações necessárias à minuta."""
    campos = [
        "protocolo",
        "data",
        "assunto",
        "pedido",
        "categoria",
        "documentos_pendentes",
        "campos_ausentes",
    ]

    return {
        campo: dados.get(campo, "não localizado")
        for campo in campos
    }


def gerar_minuta(dados, instrucoes):
    if not isinstance(dados, dict):
        raise ValueError("Os dados da solicitação são inválidos.")

    if not isinstance(instrucoes, str) or not instrucoes.strip():
        raise ValueError("O prompt institucional está vazio.")

    dados_protegidos = preparar_dados(dados)

    contexto = {
        "dados_da_solicitacao": dados_protegidos,
        "fontes": [
            "dados/originais/entrada_texto.txt",
            "dados/processados/rf05_extracao.json",
        ],
    }

    resposta = consultar_llm(
        [
            {
                "role": "system",
                "content": instrucoes,
            },
            {
                "role": "user",
                "content": (
                    "Elabore a minuta com base nestes dados:\n"
                    + json.dumps(
                        contexto,
                        ensure_ascii=False,
                        indent=2,
                    )
                ),
            },
        ],
        requisito="RF09",
        arquivo_origem="dados/processados/rf05_extracao.json",
        prompt_versao="prompts/rf09_minuta_institucional.txt",
        artefatos=["resultados/minutas/rf09_minuta.txt"],
        caso_id="caso-ficticio-matricula-01",
    )

    texto = resposta["resposta"].strip()

    if not texto:
        raise ValueError("A minuta gerada está vazia.")

    return texto, resposta


def main():
    config = carregar_configuracao()

    if config.get("revisao_humana_obrigatoria") is not True:
        print("Erro: revisão humana obrigatória não habilitada.")
        return

    if config.get("envio_automatico") is not False:
        print("Erro: envio automático deve estar desativado.")
        return

    if not ORIGEM.is_file():
        print("Erro: extração RF05 não encontrada.")
        return

    if not PROMPT.is_file():
        print("Erro: prompt institucional não encontrado.")
        return

    try:
        dados = json.loads(
            ORIGEM.read_text(encoding="utf-8-sig")
        )
        instrucoes = PROMPT.read_text(encoding="utf-8-sig")

        texto, resposta = gerar_minuta(dados, instrucoes)

        DESTINO.parent.mkdir(parents=True, exist_ok=True)
        DESTINO.write_text(texto, encoding="utf-8")

        informacoes = {
            "requisito": "RF09",
            "modelo": resposta["modelo"],
            "provedor": resposta["provedor"],
            "tempo_segundos": resposta["tempo_segundos"],
            "tokens_total": resposta["tokens_total"],
            "fontes": [
                "dados/originais/entrada_texto.txt",
                "dados/processados/rf05_extracao.json",
            ],
            "revisao_humana_pendente": True,
            "aprovado": False,
            "enviado": False,
        }

        METADADOS.write_text(
            json.dumps(
                informacoes,
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        print("Minuta gerada com sucesso.")
        print("Modelo:", resposta["modelo"])
        print("Tempo:", resposta["tempo_segundos"], "segundos")
        print("Tokens totais:", resposta["tokens_total"])
        print("Arquivo:", DESTINO)
        print("Status: PENDENTE DE REVISÃO HUMANA")
        print("Envio automático: DESATIVADO")

    except (ErroLLM, ValueError, json.JSONDecodeError) as erro:
        print("Erro ao gerar minuta:", erro)


if __name__ == "__main__":
    main()