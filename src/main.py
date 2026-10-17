import json
import platform
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path

from dotenv import load_dotenv
from src.audit import registrar_execucao


RAIZ_PROJETO = Path(__file__).resolve().parent.parent


def carregar_configuracao():
    arquivo = RAIZ_PROJETO / "config.json"

    with arquivo.open("r", encoding="utf-8-sig") as f:
        return json.load(f)


def verificar_pastas(config):
    caminhos = config.get("caminhos", {})

    for nome, caminho in caminhos.items():
        pasta = RAIZ_PROJETO / caminho

        if not pasta.is_dir():
            raise FileNotFoundError(
                f"Pasta não encontrada: {nome} ({caminho})"
            )

        print(f"[OK] {nome}: {caminho}")


def mostrar_versoes():
    print(f"Python: {platform.python_version()}")

    for biblioteca in ("PyMuPDF", "python-dotenv", "requests"):
        try:
            print(f"{biblioteca}: {version(biblioteca)}")
        except PackageNotFoundError:
            print(f"{biblioteca}: não instalada")


def main():
    print("Desafio Prático 1 - IA Generativa")
    print("-" * 45)

    load_dotenv(RAIZ_PROJETO / ".env")
    config = carregar_configuracao()

    print(f"Projeto: {config['projeto']}")
    print(f"Ambiente: {config['ambiente']}")
    print(f"Provedor: {config['provedor']}")
    print(f"Modelo: {config['modelo']}")
    print(f"Revisão humana: {config['revisao_humana_obrigatoria']}")
    print(f"Envio automático: {config['envio_automatico']}")

    print("\nVerificando pastas:")
    verificar_pastas(config)

    print("\nVersões utilizadas:")
    mostrar_versoes()

    registrar_execucao(
        requisito="RF01",
        modalidade="inicializacao",
        arquivo_origem="config.json",
        provedor=config["provedor"],
        modelo=config["modelo"],
        prompt_versao="não aplicável",
        resultado_status="sucesso",
        artefatos=["config.json"],
        parametros={"max_tokens": config["max_tokens"]},
        decisao_humana="não aplicável",
        caso_id="inicializacao",
    )

    print("\nInicialização concluída.")


if __name__ == "__main__":
    main()