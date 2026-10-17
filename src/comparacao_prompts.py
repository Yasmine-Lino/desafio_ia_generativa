import csv
import json
import os
import time
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv


RAIZ = Path(__file__).resolve().parent.parent
PASTA_RESULTADOS = RAIZ / "resultados" / "logs"
PASTA_PROMPTS = RAIZ / "prompts"

CONTEXTO = """
Uma pessoa solicitou informações sobre o andamento de um pedido
de manutenção predial em uma secretaria pública.

Dados disponíveis:
- Solicitante: João Silva
- Protocolo: 2026/001234
- Data do registro: 12/06/2026
- Assunto: manutenção predial
- Situação: encaminhado para análise do setor responsável

Não há prazo de conclusão informado.
"""

PROMPT_A = f"""
Redija uma resposta institucional ao cidadão com base nestes dados:

{CONTEXTO}
"""

PROMPT_B = f"""
PERSONA:
Você é um atendente de uma secretaria pública.

CONTEXTO:
{CONTEXTO}

TAREFA:
Redigir uma resposta ao cidadão sobre o andamento do pedido.

FORMATO:
Produza uma mensagem curta, com saudação, informações
sobre o protocolo e encerramento.

CRITÉRIOS DE SUCESSO:
- Use linguagem clara, educada e institucional.
- Utilize apenas as informações fornecidas.
- Não invente prazos, procedimentos ou decisões.
- Quando faltar uma informação, indique "não localizado".
- Não afirme que o pedido foi concluído.
"""

METAPROMPT = f"""
Crie um prompt para orientar outro modelo de IA a redigir
uma resposta institucional a um cidadão.

O prompt criado deve conter persona, contexto, tarefa,
formato e critérios de sucesso.

O texto produzido pelo outro modelo deve ser claro, educado,
fiel aos dados e não pode inventar prazos, decisões ou fatos.

Utilize o seguinte contexto:

{CONTEXTO}

Responda somente com o prompt que deverá ser utilizado.
"""


def consultar_gemini(prompt, config, chave):
    modelo = config["modelo"]
    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{modelo}:generateContent"
    )

    parametros = {
        "contents": [
            {"role": "user", "parts": [{"text": prompt}]}
        ],
        "generationConfig": {
    	    "maxOutputTokens": config["max_tokens"],
    	    "thinkingConfig": {"thinkingLevel": "low"}
	}
    }

    inicio = time.perf_counter()

    try:
        resposta = requests.post(
            url,
            headers={
                "x-goog-api-key": chave,
                "Content-Type": "application/json"
            },
            json=parametros,
            timeout=60
        )
    except requests.Timeout as erro:
        raise RuntimeError("Tempo limite da API excedido.") from erro
    except requests.RequestException as erro:
        raise RuntimeError(
            "Não foi possível conectar ao serviço Gemini."
        ) from erro

    tempo = round(time.perf_counter() - inicio, 2)

    if resposta.status_code != 200:
        mensagens = {
            400: "Parâmetros inválidos ou não aceitos pelo modelo.",
            401: "Falha de autenticação.",
            403: "Acesso à API não autorizado.",
            404: "Modelo não encontrado ou indisponível.",
            429: "Limite de requisições ou cota atingida.",
            500: "Erro interno do serviço.",
            503: "Serviço temporariamente indisponível."
        }
        motivo = mensagens.get(
            resposta.status_code, "Erro ao consultar a API."
        )
        raise RuntimeError(
            f"{motivo} HTTP {resposta.status_code}."
        )

    dados = resposta.json()
    partes = []

    for candidato in dados.get("candidates", []):
        for parte in candidato.get("content", {}).get("parts", []):
            if parte.get("text"):
                partes.append(parte["text"])

    texto = "\n".join(partes).strip()

    if not texto:
        raise RuntimeError(
            "A API não retornou texto. Verifique o limite de tokens."
        )

    uso = dados.get("usageMetadata", {})

    return {
        "resposta": texto,
        "tempo_segundos": tempo,
        "tokens_entrada": uso.get("promptTokenCount"),
        "tokens_saida": uso.get("candidatesTokenCount"),
        "tokens_total": uso.get("totalTokenCount")
    }


def salvar_texto(nome, conteudo):
    caminho = PASTA_RESULTADOS / nome
    caminho.write_text(conteudo, encoding="utf-8")


def main():
    load_dotenv(RAIZ / ".env")

    chave = os.getenv("GEMINI_API_KEY")

    if not chave:
        print("Erro: GEMINI_API_KEY não encontrada no .env.")
        return

    with (RAIZ / "config.json").open(
        "r", encoding="utf-8-sig"
    ) as arquivo:
        config = json.load(arquivo)

    if config.get("provedor") != "gemini":
        print("Erro: este experimento utiliza o provedor Gemini.")
        return

    PASTA_RESULTADOS.mkdir(parents=True, exist_ok=True)
    PASTA_PROMPTS.mkdir(parents=True, exist_ok=True)

    identificador = datetime.now().strftime("%Y%m%d_%H%M%S")
    resultados = {}

    try:
        print("Gerando o Prompt C com metaprompting...")
        geracao_c = consultar_gemini(METAPROMPT, config, chave)
        prompt_c = geracao_c["resposta"]

        prompts = {
            "A_zero_shot": PROMPT_A,
            "B_estruturado": PROMPT_B,
            "C_metaprompt": prompt_c
        }

        for nome, prompt in prompts.items():
            (PASTA_PROMPTS / f"rf02_{nome}.txt").write_text(
                prompt, encoding="utf-8"
            )

        salvar_texto(
            f"rf02_{identificador}_metaprompt.txt",
            METAPROMPT
        )

        for nome, prompt in prompts.items():
            print(f"\nExecutando {nome}...")

            resultado = consultar_gemini(prompt, config, chave)

            resultados[nome] = {
                "prompt": prompt,
                **resultado
            }

            salvar_texto(
                f"rf02_{identificador}_{nome}.txt",
                resultado["resposta"]
            )

            print(
                f"Concluído em {resultado['tempo_segundos']} segundos."
            )

        relatorio = {
            "data": datetime.now().isoformat(timespec="seconds"),
            "provedor": config["provedor"],
            "modelo": config["modelo"],
	    "temperatura": "padrão do modelo",
	    "thinking_level": "low",
	    "max_tokens": config["max_tokens"],
            "metaprompt": METAPROMPT,
            "geracao_prompt_c": geracao_c,
            "resultados": resultados
        }

        arquivo_json = (
            PASTA_RESULTADOS / f"rf02_{identificador}.json"
        )
        arquivo_json.write_text(
            json.dumps(relatorio, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        arquivo_csv = (
            PASTA_RESULTADOS / f"rf02_{identificador}_avaliacao.csv"
        )

        with arquivo_csv.open(
            "w", newline="", encoding="utf-8-sig"
        ) as arquivo:
            escritor = csv.writer(arquivo, delimiter=";")
            escritor.writerow([
                "Prompt",
                "Fidelidade ao contexto",
                "Dados inventados",
                "Formato",
                "Tom institucional",
                "Lacunas",
                "Tempo de resposta (s)",
                "Tempo ate resultado utilizavel (s)",
                "Observacoes"
            ])

            for nome, resultado in resultados.items():
                escritor.writerow([
                    nome, "", "", "", "", "",
                    resultado["tempo_segundos"], "", ""
                ])

        print("\nRF02 executado com sucesso!")
        print(f"Relatório: {arquivo_json.name}")
        print(f"Matriz de avaliação: {arquivo_csv.name}")
        print("As avaliações qualitativas devem ser preenchidas.")

    except RuntimeError as erro:
        print(f"\nFalha no experimento: {erro}")
        print("Nenhuma chave de API foi registrada.")


if __name__ == "__main__":
    main()
