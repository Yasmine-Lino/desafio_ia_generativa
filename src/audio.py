import re
from difflib import SequenceMatcher
import unicodedata
import base64
import json
import os
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from src.audit import registrar_execucao


RAIZ = Path(__file__).resolve().parent.parent
MODELO = "gemini-3.5-transcribe"


def transcrever_audio(caminho, modelo=MODELO, timeout=180):
    load_dotenv(RAIZ / ".env")
    chave = os.getenv("GEMINI_API_KEY")

    if not chave:
        raise ValueError("Chave GEMINI_API_KEY não encontrada.")

    caminho = Path(caminho)

    if not caminho.is_file():
        raise FileNotFoundError("Arquivo de áudio não encontrado.")

    if caminho.suffix.lower() != ".mp3":
        raise ValueError("O arquivo deve estar no formato MP3.")

    audio_base64 = base64.b64encode(caminho.read_bytes()).decode("ascii")

    corpo = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": (
                            "Transcreva fielmente este áudio em português. "
                            "Não resuma, não invente informações e não "
                            "adicione comentários. Retorne somente a transcrição."
                        )
                    },
                    {
                        "inline_data": {
                            "mime_type": "audio/mpeg",
                            "data": audio_base64
                        }
                    }
                ]
            }
        ]
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
                "Content-Type": "application/json"
            },
            json=corpo,
            timeout=timeout
        )
    except requests.Timeout as erro:
        raise RuntimeError("A consulta demorou mais que o esperado.") from erro
    except requests.RequestException as erro:
        raise RuntimeError("Não foi possível conectar ao Gemini.") from erro

    tempo = round(time.perf_counter() - inicio, 2)

    if resposta.status_code != 200:
        erros = {
            400: "Formato da requisição não aceito.",
            401: "Chave de acesso inválida.",
            403: "Acesso não permitido.",
            404: "Modelo não encontrado ou indisponível.",
            413: "Arquivo muito grande.",
            429: "Limite de uso atingido.",
            500: "Erro interno do provedor.",
            503: "Serviço temporariamente indisponível."
        }
        mensagem = erros.get(resposta.status_code, "Falha na API.")
        raise RuntimeError(f"{mensagem} HTTP {resposta.status_code}.")

    try:
        dados = resposta.json()
    except ValueError as erro:
        raise RuntimeError("Resposta inválida da API.") from erro

    partes = []

    for candidato in dados.get("candidates", []):
        for parte in candidato.get("content", {}).get("parts", []):
            if isinstance(parte.get("text"), str):
                partes.append(parte["text"])

            audio_transcricao = parte.get("audioTranscription")

            if isinstance(audio_transcricao, str):
                partes.append(audio_transcricao)

            elif isinstance(audio_transcricao, dict):
                texto_audio = audio_transcricao.get("text")

                if isinstance(texto_audio, str):
                    partes.append(texto_audio)

    transcricao = "\n".join(partes).strip()

    if not transcricao:
        candidatos = dados.get("candidates", [])

        motivos = [
            candidato.get("finishReason", "não informado")
            for candidato in candidatos
        ]

        bloqueio = dados.get("promptFeedback", {}).get(
            "blockReason", "não informado"
        )

        raise RuntimeError(
            "A API não retornou uma transcrição. "
            f"Motivos de finalização: {motivos}. "
            f"Motivo de bloqueio: {bloqueio}. "
            f"Quantidade de candidatos: {len(candidatos)}."
        )

    uso = dados.get("usageMetadata", {})

    return {
        "modelo": modelo,
        "transcricao": transcricao,
        "tempo_segundos": tempo,
        "tokens_entrada": uso.get("promptTokenCount"),
        "tokens_saida": uso.get("candidatesTokenCount"),
        "tokens_total": uso.get("totalTokenCount"),
        "revisao_humana": True
    }


def main():
    import uuid

    inicio = time.perf_counter()

    origem = RAIZ / "dados" / "originais" / "entrada_audio.mp3"
    pasta = RAIZ / "dados" / "processados"

    arquivo_texto = pasta / "rf06_transcricao.txt"
    arquivo_info = pasta / "rf06_informacoes.json"

    identificador = str(uuid.uuid4())

    dados_auditoria = {
        "requisito": "RF06",
        "origem": "audio",
        "provedor": "google",
        "modelo": MODELO,
        "versao_prompt": "rf06_v1",
        "parametros": {},
        "modalidade_entrada": "audio",
        "arquivo_entrada": "dados/originais/entrada_audio.mp3",
        "arquivo_saida": "dados/processados/rf06_transcricao.txt",
        "arquivo_processado": "dados/processados/rf06_informacoes.json",
        "revisao_humana": "pendente",
    }

    arquivos_criados = []

    try:
        if arquivo_texto.exists() or arquivo_info.exists():
            raise FileExistsError(
                "Os arquivos do RF06 já existem e não serão sobrescritos."
            )

        resultado = transcrever_audio(origem)

        informacoes = {
            chave: valor
            for chave, valor in resultado.items()
            if chave != "transcricao"
        }

        informacoes["id_execucao"] = identificador
        informacoes["revisao_humana_pendente"] = True

        pasta.mkdir(parents=True, exist_ok=True)

        with arquivo_texto.open("x", encoding="utf-8") as arquivo:
            arquivos_criados.append(arquivo_texto)
            arquivo.write(resultado["transcricao"])

        with arquivo_info.open("x", encoding="utf-8") as arquivo:
            arquivos_criados.append(arquivo_info)
            json.dump(
                informacoes,
                arquivo,
                ensure_ascii=False,
                indent=2,
            )

        dados_auditoria.update({
            "status": "sucesso",
            "tempo_segundos": round(
                time.perf_counter() - inicio, 2
            ),
            "tokens_entrada": resultado.get("tokens_entrada"),
            "tokens_saida": resultado.get("tokens_saida"),
            "tokens_total": resultado.get("tokens_total"),
        })

        registrar_execucao(
            dados_auditoria,
            id_execucao=identificador,
        )

        print("Transcrição realizada com sucesso.")
        print("Identificador:", identificador)
        print("Arquivo:", arquivo_texto)
        print("Revisão humana obrigatória: True")

    except (
        ValueError,
        FileNotFoundError,
        FileExistsError,
        RuntimeError,
        OSError,
    ) as erro:

        for arquivo in arquivos_criados:
            arquivo.unlink(missing_ok=True)

        if isinstance(erro, FileExistsError):
            codigo = "ARQUIVO_EXISTENTE"
        elif isinstance(erro, FileNotFoundError):
            codigo = "ARQUIVO_AUSENTE"
        elif isinstance(erro, OSError):
            codigo = "ERRO_GRAVACAO"
        elif isinstance(erro, RuntimeError):
            codigo = "ERRO_TRANSCRICAO"
        else:
            codigo = "ERRO_VALIDACAO"

        dados_auditoria.update({
            "status": "erro",
            "tempo_segundos": round(
                time.perf_counter() - inicio, 2
            ),
            "codigo_erro": codigo,
        })

        registrar_execucao(
            dados_auditoria,
            id_execucao=identificador,
        )

        print("Erro:", erro)
if __name__ == "__main__":
    main()


def normalizar_texto(texto):
    texto = unicodedata.normalize("NFKD", texto.casefold())
    texto = "".join(
        caractere
        for caractere in texto
        if not unicodedata.combining(caractere)
    )
    palavras = re.findall(r"\w+", texto, flags=re.UNICODE)
    return " ".join(palavras)


def comparar_transcricao(transcricao, referencia):
    transcricao_normalizada = normalizar_texto(transcricao)
    referencia_normalizada = normalizar_texto(referencia)

    if not transcricao_normalizada or not referencia_normalizada:
        raise ValueError(
            "A transcrição e o gabarito precisam conter texto."
        )

    similaridade = SequenceMatcher(
        None,
        transcricao_normalizada,
        referencia_normalizada,
    ).ratio()

    return {
        "correspondencia_exata_normalizada": (
            transcricao_normalizada == referencia_normalizada
        ),
        "similaridade": round(similaridade, 4),
    }
