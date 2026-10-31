import json
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

PASTA = RAIZ / "resultados" / "imagens"
PROMPT = RAIZ / "prompts" / "rf10_geracao_imagem.txt"

ORIGINAL = PASTA / "rf10_cartaz_matricula.png"
REVISADA = PASTA / "rf10_cartaz_matricula_revisado.png"
METADADOS = PASTA / "rf10_proveniencia.json"


def validar_png(caminho):
    caminho = Path(caminho)

    if not caminho.is_file():
        raise FileNotFoundError(
            f"Imagem não encontrada: {caminho}"
        )

    if caminho.suffix.lower() != ".png":
        raise ValueError("O arquivo deve ser PNG.")

    with caminho.open("rb") as arquivo:
        assinatura = arquivo.read(8)

    if assinatura != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Arquivo PNG inválido.")

    return True


def registrar_proveniencia():
    validar_png(ORIGINAL)
    validar_png(REVISADA)

    if METADADOS.exists():
        raise FileExistsError(
            "O registro de proveniência já existe. "
            "Ele não será sobrescrito para preservar a revisão humana."
        )

    if not PROMPT.is_file():
        raise FileNotFoundError(
            "Prompt do RF10 não encontrado."
        )

    dados = {
        "requisito": "RF10",
        "modalidade": "geracao_de_imagem",
        "ferramenta": "ChatGPT",
        "modelo": "modelo de geração de imagens do ChatGPT; identificação técnica não disponibilizada",
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

    METADADOS.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    return dados


def main():
    try:
        dados = registrar_proveniencia()

        print("RF10 — Proveniência registrada.")
        print("Ferramenta:", dados["ferramenta"])
        print("Imagem original:", dados["imagem_original"])
        print("Imagem revisada:", dados["imagem_revisada"])
        print("Revisão humana: PENDENTE")
        print("Arquivo:", METADADOS)

    except (FileNotFoundError, FileExistsError, ValueError) as erro:
        print("Erro no RF10:", erro)


if __name__ == "__main__":
    main()


def carregar_proveniencia():
    """Lê e valida o registro atual sem alterar a decisão humana."""
    validar_png(ORIGINAL)
    validar_png(REVISADA)
    if not METADADOS.is_file():
        raise FileNotFoundError("Registro de proveniência não encontrado.")
    try:
        dados = json.loads(METADADOS.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as erro:
        raise ValueError("Registro de proveniência inválido.") from erro
    if not isinstance(dados, dict) or dados.get("identificacao_ia") is not True:
        raise ValueError("A proveniência deve identificar a geração por IA.")
    if dados.get("imagem_original") != ORIGINAL.name:
        raise ValueError("Imagem original diferente da proveniência.")
    if dados.get("imagem_revisada") != REVISADA.name:
        raise ValueError("Imagem revisada diferente da proveniência.")
    if dados.get("aprovado") is True and dados.get("revisao_humana_realizada") is not True:
        raise ValueError("Aprovação exige revisão humana registrada.")
    return dados
