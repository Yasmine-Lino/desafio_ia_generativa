import argparse
import base64
import json
import os
import re
import time
import wave
import uuid
import requests

from src.audit import registrar_execucao
from pathlib import Path
from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
MODELO = "gemini-2.5-flash-preview-tts"
VOZ = "Kore"


def preparar_texto(texto, aprovado):
    if not aprovado:
        raise ValueError("A minuta precisa de aprovação humana antes da síntese.")

    texto = texto.strip()

    if not texto:
        raise ValueError("A minuta está vazia.")

    if re.search(r"não\s+localizado", texto, flags=re.IGNORECASE):
        texto = (
            "Atenção: esta comunicação contém informações "
            "que não foram localizadas.\n\n" + texto
        )

    return texto


def sintetizar_minuta(caminho_minuta, aprovado=False, timeout=180, id_execucao=None, final_rf09=False, id_execucao_minuta=None, caminho_log=None):
    caminho_minuta = Path(caminho_minuta)

    if id_execucao is None:
        id_execucao = str(uuid.uuid4())

    if not caminho_minuta.is_file():
        raise FileNotFoundError("Arquivo da minuta não encontrado.")

    # O sinalizador --aprovado não substitui uma decisão auditada.
    if not id_execucao_minuta:
        raise ValueError("Informe a execução da minuta aprovada (--id-execucao-minuta).")
    from src.revisao_humana import verificar_integridade_documento
    from src.audit import listar_execucoes
    registros = listar_execucoes(caminho_log)
    decisoes = [r for r in registros if r.get("tipo_evento") == "decisao_humana"
                and r.get("id_execucao_referenciada") == id_execucao_minuta]
    if len(decisoes) != 1 or decisoes[0].get("decisao") != "aprovado":
        raise ValueError("Não há aprovação humana auditada para esta minuta.")
    if not verificar_integridade_documento(id_execucao_minuta, caminho_log=caminho_log):
        raise ValueError("O hash da minuta difere da versão aprovada.")
    documento_aprovado = (RAIZ / decisoes[0]["arquivo_revisado"]).resolve()
    if caminho_minuta.resolve() != documento_aprovado:
        raise ValueError("A minuta informada não corresponde à versão aprovada.")

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
        raise RuntimeError("Falha na comunicação com a API.") from erro

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
            raise RuntimeError("Formato de áudio não suportado: " + formato)

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
    destino = pasta / ("rf07_minuta_rf09_aprovada.wav" if final_rf09 else "rf07_minuta_falada.wav")
    arquivo_info = pasta / ("rf07_minuta_rf09_informacoes.json" if final_rf09 else "rf07_informacoes.json")

    if destino.exists() or arquivo_info.exists():
        raise FileExistsError(
            "Os arquivos do RF07 já existem e não serão sobrescritos."
        )

    informacoes = {
        "modelo": MODELO,
        "voz": VOZ,
        "arquivo_minuta": str(caminho_minuta),
        "sha256_minuta_aprovada": __import__("hashlib").sha256(caminho_minuta.read_bytes()).hexdigest(),
        "tipo_minuta": "rf09_final" if final_rf09 else "teste",
        "arquivo_audio": str(destino),
        "aprovacao_humana_declarada": aprovado,
        "id_execucao": id_execucao,
        "aviso_campos_ausentes": bool(
            re.search(r"não\s+localizado", texto_original, re.IGNORECASE)
        ),
        "tempo_segundos": duracao,
        "tokens_total": dados.get(
            "usageMetadata", {}
        ).get("totalTokenCount"),
        "revisao_audio_pendente": True,
    }

    pasta.mkdir(parents=True, exist_ok=True)

    # Primeiro prepara os arquivos temporários.
    # Os resultados históricos não são alterados.
    import tempfile

    temporarios = []
    publicados = []

    try:
        with tempfile.NamedTemporaryFile(
            dir=pasta,
            suffix=".wav.tmp",
            delete=False,
        ) as temporario:
            caminho_audio_temp = Path(temporario.name)
            temporarios.append(caminho_audio_temp)

        with wave.open(str(caminho_audio_temp), "wb") as arquivo:
            arquivo.setnchannels(1)
            arquivo.setsampwidth(2)
            arquivo.setframerate(24000)
            arquivo.writeframes(audio)

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=pasta,
            suffix=".json.tmp",
            delete=False,
        ) as temporario:
            caminho_info_temp = Path(temporario.name)
            temporarios.append(caminho_info_temp)
            json.dump(
                informacoes,
                temporario,
                ensure_ascii=False,
                indent=2,
            )

        # Publica sem sobrescrever arquivos existentes.
        with destino.open("xb") as arquivo:
            publicados.append(destino)
            arquivo.write(caminho_audio_temp.read_bytes())

        with arquivo_info.open("x", encoding="utf-8") as arquivo:
            publicados.append(arquivo_info)
            arquivo.write(
                caminho_info_temp.read_text(encoding="utf-8")
            )

    except Exception:
        for caminho in publicados:
            caminho.unlink(missing_ok=True)
        raise

    finally:
        for caminho in temporarios:
            caminho.unlink(missing_ok=True)

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
        help="Confirma que o texto foi revisado e aprovado."
    )

    parser.add_argument("--id-execucao-minuta", help="ID auditado da execução da minuta aprovada.")
    parser.add_argument("--final-rf09", action="store_true", help="Gera saída separada da minuta final RF09 sem sobrescrever o ensaio.")
    argumentos = parser.parse_args()

    identificador = str(uuid.uuid4())
    inicio = time.perf_counter()

    pasta = RAIZ / "resultados" / "audios"
    arquivo_audio = pasta / ("rf07_minuta_rf09_aprovada.wav" if argumentos.final_rf09 else "rf07_minuta_falada.wav")
    arquivo_info = pasta / ("rf07_minuta_rf09_informacoes.json" if argumentos.final_rf09 else "rf07_informacoes.json")

    dados_auditoria = {
        "requisito": "RF07",
        "origem": "sintese_voz",
        "provedor": "google",
        "modelo": MODELO,
        "versao_prompt": "rf07_v1",
        "parametros": {},
        "modalidade_entrada": "texto",
        "arquivo_saida": "resultados/audios/" + arquivo_audio.name,
        "arquivo_processado": "resultados/audios/" + arquivo_info.name,
        "revisao_humana": "pendente",
    }

    try:
        caminho_minuta = Path(argumentos.minuta).resolve()
        caminho_projeto = RAIZ.resolve()

        try:
            caminho_relativo = caminho_minuta.relative_to(
                caminho_projeto
            )
        except ValueError as erro:
            raise ValueError(
                "A minuta deve estar dentro da pasta do projeto."
            ) from erro

        dados_auditoria["arquivo_entrada"] = (
            caminho_relativo.as_posix()
        )

        if arquivo_audio.exists() or arquivo_info.exists():
            raise FileExistsError(
                "Os arquivos do RF07 já existem e não serão sobrescritos."
            )

        if argumentos.final_rf09 and caminho_relativo.as_posix() != "resultados/minutas/rf09_minuta_revisada.txt":
            raise ValueError("--final-rf09 exige resultados/minutas/rf09_minuta_revisada.txt")

        resultado = sintetizar_minuta(
            caminho_minuta,
            aprovado=argumentos.aprovado,
            id_execucao=identificador,
            final_rf09=argumentos.final_rf09,
            id_execucao_minuta=argumentos.id_execucao_minuta,
        )

        dados_auditoria.update({
            "status": "sucesso",
            "tempo_segundos": round(
                time.perf_counter() - inicio, 2
            ),
            "tokens_total": resultado.get("tokens_total"),
        })

        try:
            registrar_execucao(
                dados_auditoria,
                id_execucao=identificador,
            )
        except Exception:
            # Remove apenas os arquivos produzidos nesta execução.
            arquivo_audio.unlink(missing_ok=True)
            arquivo_info.unlink(missing_ok=True)
            raise

        print("Áudio gerado com sucesso.")
        print("Identificador:", identificador)
        print("Modelo:", resultado["modelo"])
        print("Voz:", resultado["voz"])
        print("Arquivo:", resultado["arquivo_audio"])
        print("Revisão do áudio ainda obrigatória.")

    except (
        ValueError,
        FileNotFoundError,
        FileExistsError,
        RuntimeError,
        OSError,
    ) as erro:
        if isinstance(erro, FileExistsError):
            codigo = "ARQUIVO_EXISTENTE"
        elif isinstance(erro, FileNotFoundError):
            codigo = "ARQUIVO_AUSENTE"
        elif isinstance(erro, OSError):
            codigo = "ERRO_GRAVACAO"
        elif isinstance(erro, RuntimeError):
            codigo = "ERRO_SINTESE"
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
        raise SystemExit(1)


if __name__ == "__main__":
    main()
