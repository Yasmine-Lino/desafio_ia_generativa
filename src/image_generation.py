import json
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

PASTA = RAIZ / "resultados" / "imagens"
PROMPT = RAIZ / "prompts" / "rf10_geracao_imagem.txt"

ORIGINAL = PASTA / "rf10_cartaz_matricula.png"
REVISADA = PASTA / "rf10_cartaz_matricula_revisado_v2.png"
METADADOS = PASTA / "rf10_proveniencia.json"


def validar_png(caminho):
    caminho = Path(caminho)

    if not caminho.is_file():
        raise FileNotFoundError(f"Imagem não encontrada: {caminho}")

    if caminho.suffix.lower() != ".png":
        raise ValueError("O arquivo deve ser PNG.")

    with caminho.open("rb") as arquivo:
        assinatura = arquivo.read(8)

    if assinatura != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Arquivo PNG inválido.")

    return True


def salvar_metadados(dados):
    METADADOS.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def registrar_proveniencia():
    validar_png(ORIGINAL)
    validar_png(REVISADA)

    if METADADOS.exists():
        raise FileExistsError(
            "O registro de proveniência já existe. "
            "Ele não será sobrescrito para preservar a revisão humana."
        )

    if not PROMPT.is_file():
        raise FileNotFoundError("Prompt do RF10 não encontrado.")

    dados = {
        "requisito": "RF10",
        "modalidade": "geracao_de_imagem",
        "ferramenta": "ChatGPT",
        "modelo": (
            "modelo de geração de imagens do ChatGPT; "
            "identificação técnica não disponibilizada"
        ),
        "data_registro": datetime.now().astimezone().isoformat(
            timespec="seconds"
        ),
        "data_geracao": "2026-10-17",
        "prompt_documentado": "prompts/rf10_geracao_imagem.txt",
        "imagem_original": ORIGINAL.name,
        "imagem_revisada": REVISADA.name,
        "revisao_visual": {
            "texto": "Correção da orientação sobre documentos pendentes.",
            "simbolos": "Ícones educacionais ilustrativos.",
            "maos": "Não aplicável; não há pessoas.",
            "objetos": "Materiais escolares e computador.",
            "coerencia": "Relacionada ao caso fictício de matrícula."
        },
        "identificacao_ia": True,
        "revisao_humana_realizada": False,
        "aprovado": False,
        "revisao_adicional_pendente": False,
        "tentativa_api_gemini": {
            "modelo": "gemini-2.5-flash-image",
            "resultado": "HTTP 429",
            "motivo": "Cota gratuita informada como zero.",
            "imagem_gerada": False
        },
        "observacao": (
            "A imagem foi gerada no ChatGPT e salva manualmente "
            "no projeto. A aprovação depende de revisão humana."
        )
    }

    salvar_metadados(dados)
    return dados


def carregar_proveniencia():
    validar_png(ORIGINAL)
    validar_png(REVISADA)

    if not METADADOS.is_file():
        return registrar_proveniencia()

    try:
        dados = json.loads(
            METADADOS.read_text(encoding="utf-8-sig")
        )
    except (OSError, json.JSONDecodeError) as erro:
        raise ValueError(
            "O registro de proveniência não contém JSON válido."
        ) from erro

    if dados.get("identificacao_ia") is not True:
        raise ValueError(
            "O registro deve identificar a imagem como conteúdo de IA."
        )

    if dados.get("imagem_original") != ORIGINAL.name:
        raise ValueError(
            "O registro não aponta para a imagem original esperada."
        )

    arquivo_aprovado = dados.get("arquivo_aprovado")

    # Migra o registro anterior somente se a equipe já aprovou
    # especificamente o arquivo v2.
    if dados.get("imagem_revisada") != REVISADA.name:
        if (
            dados.get("aprovado") is not True
            or arquivo_aprovado != REVISADA.name
        ):
            raise ValueError(
                "O registro não aponta para a imagem revisada v2 aprovada."
            )

        nome_anterior = dados.get("imagem_revisada")
        if nome_anterior:
            dados.setdefault("imagem_revisada_anterior", nome_anterior)

        dados["imagem_revisada"] = REVISADA.name
        salvar_metadados(dados)

    if dados.get("revisao_humana_realizada") is not True:
        if dados.get("aprovado") is True:
            raise ValueError(
                "A imagem não pode estar aprovada sem revisão humana."
            )

    if dados.get("aprovado") is True:
        if dados.get("revisao_adicional_pendente") is True:
            raise ValueError(
                "A aprovação não pode ser concluída enquanto houver "
                "revisão adicional pendente."
            )

        if arquivo_aprovado != REVISADA.name:
            raise ValueError(
                "O arquivo aprovado não corresponde à imagem revisada v2."
            )

        validar_png(PASTA / arquivo_aprovado)

    return dados


def main():
    try:
        dados = carregar_proveniencia()

        print("RF10 — Proveniência registrada.")
        print("Ferramenta:", dados.get("ferramenta", "não informada"))
        print("Imagem original:", dados.get("imagem_original"))
        print("Imagem revisada:", dados.get("imagem_revisada"))
        print(
            "Revisão humana:",
            "REALIZADA"
            if dados.get("revisao_humana_realizada")
            else "PENDENTE"
        )
        print(
            "Aprovação:",
            "APROVADA"
            if dados.get("aprovado")
            else "PENDENTE"
        )
        print("Arquivo:", METADADOS)

    except (FileNotFoundError, FileExistsError, ValueError) as erro:
        print("Erro no RF10:", erro)


if __name__ == "__main__":
    main()