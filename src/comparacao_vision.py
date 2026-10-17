import difflib
import json
import re
import unicodedata
from pathlib import Path


RAIZ = Path(__file__).resolve().parent.parent
OCR = RAIZ / "dados" / "processados" / "rf08_texto_bruto.txt"
GABARITO = RAIZ / "dados" / "gabaritos" / "rf08_texto.txt"
SAIDA = RAIZ / "dados" / "processados" / "rf08_comparacao.json"

ARTIGOS = {"da", "das", "de", "do", "dos", "e"}


def sem_acentos(texto):
    texto = unicodedata.normalize("NFD", texto.casefold())
    return "".join(
        caractere for caractere in texto
        if unicodedata.category(caractere) != "Mn"
    )


def normalizar(texto):
    return re.sub(r"[^a-z0-9]", "", sem_acentos(texto))


def normalizar_rotulo(rotulo):
    palavras = re.findall(r"[a-z0-9]+", sem_acentos(rotulo))
    return "".join(palavra for palavra in palavras if palavra not in ARTIGOS)


def extrair_campos(texto):
    campos = {}

    for linha in texto.splitlines():
        correspondencia = re.match(r"^\s*([^:]+):\s*(.*?)\s*$", linha)

        if correspondencia:
            rotulo, valor = correspondencia.groups()
            chave = normalizar_rotulo(rotulo)

            if chave:
                campos[chave] = valor

    return campos


def comparar_textos(texto_ocr, texto_gabarito):
    ocr_normalizado = normalizar(texto_ocr)
    gabarito_normalizado = normalizar(texto_gabarito)

    campos_ocr = extrair_campos(texto_ocr)
    campos_gabarito = extrair_campos(texto_gabarito)
    rotulos = sorted(set(campos_ocr) | set(campos_gabarito))

    corretos = []
    divergentes = []

    for rotulo in rotulos:
        valor_ocr = campos_ocr.get(rotulo)
        valor_gabarito = campos_gabarito.get(rotulo)

        if (
            valor_ocr is not None
            and valor_gabarito is not None
            and normalizar(valor_ocr) == normalizar(valor_gabarito)
        ):
            corretos.append(rotulo)
        else:
            divergentes.append(rotulo)

    return {
        "correspondencia_exata_normalizada": (
            ocr_normalizado == gabarito_normalizado
        ),
        "similaridade": round(
            difflib.SequenceMatcher(
                None, gabarito_normalizado, ocr_normalizado
            ).ratio(),
            4,
        ),
        "campos_comparados": len(rotulos),
        "campos_corretos": corretos,
        "campos_divergentes_ou_ausentes": divergentes,
        "revisao_humana_pendente": True,
    }


def main():
    if not OCR.is_file():
        raise FileNotFoundError(f"OCR não encontrado: {OCR}")

    if not GABARITO.is_file():
        raise FileNotFoundError(f"Gabarito não encontrado: {GABARITO}")

    texto_ocr = OCR.read_text(encoding="utf-8-sig")
    texto_gabarito = GABARITO.read_text(encoding="utf-8-sig")

    if not texto_ocr.strip() or not texto_gabarito.strip():
        raise ValueError("OCR e gabarito precisam conter texto.")

    resultado = comparar_textos(texto_ocr, texto_gabarito)
    resultado["arquivo_ocr"] = "dados/processados/rf08_texto_bruto.txt"
    resultado["arquivo_gabarito"] = "dados/gabaritos/rf08_texto.txt"

    SAIDA.write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("Comparação RF08 concluída.")
    print(
        "Correspondência exata normalizada:",
        resultado["correspondencia_exata_normalizada"],
    )
    print("Similaridade:", resultado["similaridade"])
    print("Campos corretos:", len(resultado["campos_corretos"]))
    print(
        "Campos divergentes ou ausentes:",
        len(resultado["campos_divergentes_ou_ausentes"]),
    )
    print("Revisão humana pendente: sim")
    print("Arquivo:", SAIDA)


if __name__ == "__main__":
    main()