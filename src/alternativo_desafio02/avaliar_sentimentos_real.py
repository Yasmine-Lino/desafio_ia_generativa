import json
from pathlib import Path

from src.llm_client import consultar_llm, carregar_configuracao
from src.alternativo_desafio02.sentiment import (
    ResultadoSentimento,
    classificar_avaliacao,
    avaliar_contra_gabarito,
    carregar_gabarito,
)

RAIZ = Path(__file__).resolve().parents[2]

ARQUIVO_AVALIACOES = RAIZ / "dados/avaliacoes/avaliacoes.json"
ARQUIVO_GABARITO = RAIZ / "dados/gabaritos/desafio2_sentimentos.json"
ARQUIVO_RESULTADO = RAIZ / "resultados/metricas/rf22_sentimentos_gemini.json"


class GeminiReal:
    def __init__(self):
        self.chamadas = []

    def completar(self, prompt):
        resposta = consultar_llm(
            mensagens=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        self.chamadas.append({
            "modelo": resposta["modelo"],
            "tokens_entrada": resposta["tokens_entrada"],
            "tokens_saida": resposta["tokens_saida"],
            "tempo_segundos": resposta["tempo_segundos"],
        })

        return resposta["resposta"]


def main():
    configuracao = carregar_configuracao()

    if configuracao.get("provedor") != "gemini":
        raise RuntimeError("O projeto nao esta configurado para Gemini.")

    avaliacoes = json.loads(
        ARQUIVO_AVALIACOES.read_text(encoding="utf-8-sig")
    )

    rotulos = json.loads(ARQUIVO_GABARITO.read_text(encoding="utf-8-sig"))

    if len(avaliacoes) != 12 or len(rotulos) != 12:
        raise ValueError("Esperadas exatamente 12 avaliacoes e 12 rotulos.")

    ids_entrada = [item["id"] for item in avaliacoes]
    ids_gabarito = [item["id"] for item in rotulos]
    if ids_entrada != ids_gabarito:
        raise ValueError(
            "Os IDs das avaliacoes e do gabarito nao correspondem. "
            "A classificacao foi interrompida para evitar comparacao incorreta."
        )

    # Adapta o gabarito A01-A12 ao formato esperado pelo comparador RF22.
    gabarito = {
        "avaliacoes": [
            {"id": item["id"], "rotulo_esperado": item["polaridade"]}
            for item in rotulos
        ]
    }

    llm = GeminiReal()
    resultados = {}
    erros = []

    print("\n=== CLASSIFICACAO REAL PELO GEMINI ===")

    for entrada, referencia in zip(avaliacoes, gabarito["avaliacoes"]):
        identificador = referencia["id"]

        try:
            resultado = classificar_avaliacao(
                identificador,
                entrada["texto"],
                llm
            )

            resultados[identificador] = resultado

            print(
                f"{entrada['id']} | "
                f"Esperado: {referencia['rotulo_esperado']} | "
                f"Obtido: {resultado.polaridade}"
            )

        except Exception as erro:
            erros.append({
                "id": identificador,
                "erro": str(erro)
            })
            print(f"{entrada['id']} | ERRO: {erro}")

    avaliacao = avaliar_contra_gabarito(resultados, gabarito)

    total_tokens_entrada = sum(
        x["tokens_entrada"] or 0 for x in llm.chamadas
    )
    total_tokens_saida = sum(
        x["tokens_saida"] or 0 for x in llm.chamadas
    )

    metricas_saida = dict(avaliacao)
    if avaliacao["total"] == 0:
        metricas_saida["acuracia"] = None
        metricas_saida["ambiguas"] = dict(avaliacao["ambiguas"])
        metricas_saida["ambiguas"]["proporcao"] = None

    documento = {
        "projeto": "Central Inteligente de Atendimento",
        "requisito": "RF22",
        "provedor": "Gemini",
        "modelo": configuracao["modelo"],
        "origem_dados": "dados/avaliacoes/avaliacoes.json",
        "total_avaliacoes": len(avaliacoes),
        "chamadas_realizadas": len(llm.chamadas),
        "metricas": metricas_saida,
        "tokens_entrada": total_tokens_entrada,
        "tokens_saida": total_tokens_saida,
        "erros": erros,
        "observacao": (
            "A classificacao usa os IDs A01-A12 e o gabarito "
            "dados/gabaritos/desafio2_sentimentos.json. Se nenhuma chamada "
            "for concluida, a acuracia fica nula (nao calculavel). "
            "Resultados ficticios nao representam validacao em dados reais."
        )
    }

    ARQUIVO_RESULTADO.parent.mkdir(parents=True, exist_ok=True)
    ARQUIVO_RESULTADO.write_text(
        json.dumps(documento, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\n=== RESULTADO RF22 ===")
    print(f"Acuracia: {avaliacao['acertos']}/{avaliacao['total']}")
    if metricas_saida["acuracia"] is None:
        print("Percentual: nao calculavel (nenhuma classificacao valida)")
    else:
        print(f"Percentual: {metricas_saida['acuracia'] * 100:.2f}%")
    print(f"Chamadas realizadas: {len(llm.chamadas)}")
    print(f"Erros: {len(erros)}")
    print(f"Tokens de entrada: {total_tokens_entrada}")
    print(f"Tokens de saida: {total_tokens_saida}")
    print(f"\nResultado salvo em: {ARQUIVO_RESULTADO}")


if __name__ == "__main__":
    main()
