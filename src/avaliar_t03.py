import json
from pathlib import Path
from src.nlp import ficha

def ler(caminho):
    return json.loads(Path(caminho).read_text(encoding="utf-8"))

def executar():
    casos = ler("dados/solicitacoes/casos.json")
    gabarito = ler("dados/gabaritos/desafio2_solicitacoes.json")
    referencias = {item["id"]: item for item in gabarito}

    campos = (
        "categoria", "protocolo", "data",
        "solicitante", "necessita_revisao"
    )

    resultados = []
    acertos = 0
    total = 0

    for caso in casos:
        esperado = referencias[caso["id"]]
        saida = ficha(caso["texto"])["estrutura"]

        comparacoes = {}

        for campo in campos:
            correto = saida[campo] == esperado[campo]
            comparacoes[campo] = {
                "esperado": esperado[campo],
                "obtido": saida[campo],
                "correto": correto
            }
            total += 1
            acertos += int(correto)

        aprovado = all(
            item["correto"] for item in comparacoes.values()
        )

        resultados.append({
            "id": caso["id"],
            "aprovado": aprovado,
            "comparacoes": comparacoes
        })

        print(
            f'{caso["id"]}: '
            f'{"OK" if aprovado else "DIVERGENTE"}'
        )

        for campo, item in comparacoes.items():
            if not item["correto"]:
                print(
                    f'  {campo}: '
                    f'esperado={item["esperado"]!r}, '
                    f'obtido={item["obtido"]!r}'
                )

    resumo = {
        "teste": "T03",
        "total_solicitacoes": len(casos),
        "solicitacoes_aprovadas": sum(
            item["aprovado"] for item in resultados
        ),
        "campos_corretos": acertos,
        "total_campos": total,
        "taxa_concordancia": round(
            acertos / total * 100, 2
        ) if total else 0,
        "resultados": resultados
    }

    destino = Path("resultados/metricas/t03_solicitacoes.json")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        json.dumps(resumo, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print()
    print(
        "Solicitacoes aprovadas:",
        resumo["solicitacoes_aprovadas"],
        "/",
        resumo["total_solicitacoes"]
    )
    print("Campos corretos:", acertos, "/", total)
    print("Concordancia:", resumo["taxa_concordancia"], "%")
    print("Evidencia salva em:", destino)

    return resumo

if __name__ == "__main__":
    executar()
