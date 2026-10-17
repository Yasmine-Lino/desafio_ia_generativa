import argparse
import base64
import json
import os
import re
import time
import wave
from pathlib import Path

import requests
from dotenv import load_dotenv

from src.audit import registrar_execucao


RAIZ = Path(__file__).resolve().parent.parent
MODELO = "gemini-2.5-flash-preview-tts"
VOZ = "Kore"


def preparar_texto(texto, aprovado):
    if not aprovado:
        raise ValueError(
            "A minuta precisa de aprovação humana antes da síntese."
        )

    texto = texto.strip()

    if not texto:
        raise ValueError("A minuta está vazia.")

    if re.search(r"não\s+localizado", texto, flags=re.IGNORECASE):
        texto = (
            "Atenção: esta comunicação contém informações "
            "que não foram localizadas.\n\n" + texto
        )

    return texto


def sintetizar_minuta(caminho_minuta, aprovado=False, timeout=180):
    caminho_minuta = Path(caminho_minuta)

    if not caminho_minuta.is_file():
        raise FileNotFoundError("Arquivo da minuta não encontrado.")

    texto_original = caminho_minuta.read_text(encoding="utf-8-sig")
    texto_falado = preparar_texto(texto_original, aprovado)

    load_dotenv(RAIZ / ".env")
    chave = os.getenv("GEMINI_API_KEY")

    if not chave:
        raise ValueError("GEMINI_API_KEY não encontrada.")

    corpo = {
        "contents": [{
            "parts": [{
                "text": (
                    "Leia em português brasileiro, com voz clara, "
                    "tom institucional cordial e ritmo moderado. "
                    "Leia fielmente o conteúdo, sem resumir ou "
                    "acrescentar informações.\n\n"
                    + texto_falado
                )
            }]
        }],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": VOZ
                    }
                }
            }
        }
    }

    url = (
        "https://generativelanguage.googleapis.com/v1beta/"
        f"models/{MODELO}:generateContent"
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
    except requests.RequestException as erro:
        raise RuntimeError(
            "Falha na comunicação com a API."
        ) from erro

    duracao = round(time.perf_counter() - inicio, 2)

    if resposta.status_code != 200:
        raise RuntimeError(
            f"Não foi possível gerar o áudio. HTTP {resposta.status_code}."
        )

    try:
        dados = resposta.json()
        partes = dados["candidates"][0]["content"]["parts"]
    except (ValueError, KeyError, IndexError, TypeError) as erro:
        raise RuntimeError("Resposta inesperada da API.") from erro

    audio = None

    for parte in partes:
        conteudo = parte.get("inlineData") or parte.get("inline_data")

        if not conteudo or not conteudo.get("data"):
            continue

        formato = (
            conteudo.get("mimeType")
            or conteudo.get("mime_type", "")
        )

        if not formato.lower().startswith("audio/l16"):
            raise RuntimeError(
                "Formato de áudio não suportado: " + formato
            )

        try:
            audio = base64.b64decode(
                conteudo["data"], validate=True
            )
        except (ValueError, base64.binascii.Error) as erro:
            raise RuntimeError("Dados de áudio inválidos.") from erro

        break

    if not audio:
        raise RuntimeError("A API não retornou dados de áudio.")

    pasta = RAIZ / "resultados" / "audios"
    pasta.mkdir(parents=True, exist_ok=True)

    destino = pasta / "rf07_minuta_falada.wav"

    with wave.open(str(destino), "wb") as arquivo:
        arquivo.setnchannels(1)
        arquivo.setsampwidth(2)
        arquivo.setframerate(24000)
        arquivo.writeframes(audio)

    informacoes = {
        "modelo": MODELO,
        "voz": VOZ,
        "arquivo_minuta": str(caminho_minuta),
        "arquivo_audio": str(destino),
        "aprovacao_humana_declarada": aprovado,
        "aviso_campos_ausentes": bool(
            re.search(r"não\s+localizado", texto_original, re.IGNORECASE)
        ),
        "tempo_segundos": duracao,
        "tokens_total": dados.get(
            "usageMetadata", {}
        ).get("totalTokenCount"),
        "revisao_audio_pendente": True
    }

    (pasta / "rf07_informacoes.json").write_text(
        json.dumps(informacoes, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return informacoes


def main():
    parser = argparse.ArgumentParser(
        description="Geração de voz para minuta aprovada."
    )

    parser.add_argument(
        "minuta",
        help="Caminho do arquivo de texto."
    )
    parser.add_argument(
        "--aprovado",
        action="store_true",
        help="Confirma que o texto foi revisado e aprovado por uma pessoa."
    )

    argumentos = parser.parse_args()
    nome_arquivo = Path(argumentos.minuta).name

    try:
        resultado = sintetizar_minuta(
            argumentos.minuta,
            aprovado=argumentos.aprovado
        )

        registrar_execucao(
            requisito="RF07",
            modalidade="sintese_de_voz",
            arquivo_origem=nome_arquivo,
            provedor="gemini",
            modelo=resultado["modelo"],
            prompt_versao="src/sintese_voz.py:tts-v1",
            resultado_status="sucesso",
            artefatos=[
                "resultados/audios/rf07_minuta_falada.wav",
                "resultados/audios/rf07_informacoes.json",
            ],
            parametros={
                "voz": resultado["voz"],
                "timeout": 180,
            },
            duracao_segundos=resultado["tempo_segundos"],
            decisao_humana="aprovada_para_sintese",
            caso_id="caso-ficticio-matricula-01",
        )

        print("Áudio gerado com sucesso.")
        print("Modelo:", resultado["modelo"])
        print("Voz:", resultado["voz"])
        print("Arquivo:", resultado["arquivo_audio"])
        print("Tempo:", resultado["tempo_segundos"], "segundos")
        print("Revisão do áudio ainda obrigatória.")

    except (ValueError, FileNotFoundError, RuntimeError) as erro:
        registrar_execucao(
            requisito="RF07",
            modalidade="sintese_de_voz",
            arquivo_origem=nome_arquivo,
            provedor="gemini",
            modelo=MODELO,
            prompt_versao="src/sintese_voz.py:tts-v1",
            resultado_status="falha",
            parametros={
                "voz": VOZ,
                "timeout": 180,
            },
            erro=erro,
            decisao_humana="pendente",
            caso_id="caso-ficticio-matricula-01",
        )
        print("Erro:", erro)
        raise SystemExit(1)


if __name__ == "__main__":
    main()