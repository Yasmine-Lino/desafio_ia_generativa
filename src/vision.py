import base64
import json
import os
import time
from pathlib import Path

import pymupdf
import requests
from dotenv import load_dotenv

from src.audit import registrar_execucao


RAIZ = Path(__file__).resolve().parent.parent
MODELO = "gemini-3.8-flash"


def extrair_documento(caminho, modelo=MODELO, timeout=180):
    caminho = Path(caminho)

    if not caminho.is_file():
        raise FileNotFoundError("Documento não encontrado.")

    if caminho.suffix.lower() != ".pdf":
        raise ValueError("O documento deve estar em formato PDF.")

    with pymupdf.open(caminho) as documento:
        if len(documento) != 1:
            raise ValueError("Este teste aceita PDF de uma página.")

        pagina = documento[0]
        imagem = pagina.get_pixmap(
            matrix=pymupdf.Matrix(2, 2),
            alpha=False,
        )
        imagem_base64 = base64.b64encode(
            imagem.tobytes("png")
        ).decode("ascii")

    load_dotenv(RAIZ / ".env")
    chave = os.getenv("GEMINI_API_KEY")

    if not chave:
        raise ValueError("GEMINI_API_KEY não encontrada.")

    prompt = (
        "Você está realizando OCR de um documento fictício. "
        "Transcreva fielmente todo o texto visível na imagem, "
        "incluindo títulos, campos preenchidos e declarações. "
        "Não resuma, não invente dados e não corrija silenciosamente. "
        "Para trechos que não conseguir ler, escreva [ilegível]. "
        "Para campos vazios, escreva [não preenchido]. "
        "Retorne apenas a transcrição, mantendo os rótulos dos campos."
    )

    corpo = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": prompt},
                {
                    "inline_data": {
                        "mime_type": "image/png",
                        "data": imagem_base64,
                    }
                },
            ],
        }]
    }

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{modelo}:generateContent"
    )

    inicio = time.perf_counter()

    try:
        resposta = requests.post(
            url,
            headers={
                "x-goog-api-key": chave,
                "Content-Type": "application/json",
            },
            json=corpo,
            timeout=timeout,
        )
    except requests.RequestException as erro:
        raise RuntimeError("Falha na conexão com o Gemini.") from erro

    duracao = round(time.perf_counter() - inicio, 2)

    if resposta.status_code != 200:
        raise RuntimeError(
            f"Falha na extração. HTTP {resposta.status_code}."
        )

    try:
        dados = resposta.json()
        partes = dados["candidates"][0]["content"]["parts"]
    except (ValueError, KeyError, IndexError, TypeError) as erro:
        raise RuntimeError("Resposta inválida da API.") from erro

    textos = [
        parte["text"]
        for parte in partes
        if isinstance(parte.get("text"), str)
    ]

    texto = "\n".join(textos).strip()

    if not texto:
        raise RuntimeError("O modelo não retornou texto.")

    uso = dados.get("usageMetadata", {})

    return {
        "modelo": modelo,
        "arquivo_original": caminho.name,
        "texto_bruto": texto,
        "tempo_segundos": duracao,
        "tokens_entrada": uso.get("promptTokenCount"),
        "tokens_saida": uso.get("candidatesTokenCount"),
        "tokens_total": uso.get("totalTokenCount"),
        "revisao_humana_pendente": True,
    }


def main():
    origem = RAIZ / "dados" / "originais" / "entrada_pdf-imagem.pdf"
    destino = RAIZ / "dados" / "processados"
    destino.mkdir(parents=True, exist_ok=True)

    try:
        resultado = extrair_documento(origem)

        arquivo_texto = destino / "rf08_texto_bruto.txt"
        arquivo_info = destino / "rf08_informacoes.json"

        arquivo_texto.write_text(
            resultado["texto_bruto"],
            encoding="utf-8",
        )

        informacoes = {
            chave: valor
            for chave, valor in resultado.items()
            if chave != "texto_bruto"
        }

        arquivo_info.write_text(
            json.dumps(informacoes, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        registrar_execucao(
            requisito="RF08",
            modalidade="ocr_de_documento",
            arquivo_origem="dados/originais/entrada_pdf-imagem.pdf",
            provedor="gemini",
            modelo=resultado["modelo"],
            prompt_versao="src/vision.py:ocr-v1",
            resultado_status="sucesso",
            artefatos=[
                "dados/processados/rf08_texto_bruto.txt",
                "dados/processados/rf08_informacoes.json",
            ],
            parametros={"timeout": 180},
            duracao_segundos=resultado["tempo_segundos"],
            decisao_humana="pendente",
            caso_id="caso-ficticio-matricula-01",
        )

        print("Extração realizada com sucesso.")
        print("Modelo:", resultado["modelo"])
        print("Tempo:", resultado["tempo_segundos"], "segundos")
        print("Tokens totais:", resultado["tokens_total"])
        print("Revisão humana pendente.")
        print("Arquivo:", arquivo_texto)

    except (ValueError, FileNotFoundError, RuntimeError) as erro:
        registrar_execucao(
            requisito="RF08",
            modalidade="ocr_de_documento",
            arquivo_origem="dados/originais/entrada_pdf-imagem.pdf",
            provedor="gemini",
            modelo=MODELO,
            prompt_versao="src/vision.py:ocr-v1",
            resultado_status="falha",
            parametros={"timeout": 180},
            erro=erro,
            decisao_humana="pendente",
            caso_id="caso-ficticio-matricula-01",
        )
        print("Erro:", erro)
        raise SystemExit(1)


if __name__ == "__main__":
    main()