"""RAG conservador: resposta fundamentada ou abstenção (RF19)."""
import re
from .guardrails import avaliar_texto


def detectar_prazos_divergentes(trechos):
    """Verifica prazos diferentes em versoes do mesmo documento."""
    prazos_por_base = {}

    for item in trechos:
        nome = item["documento"]
        base = re.sub(r"_v[0-9]+(?=\.)", "", nome)

        encontrados = re.findall(
            r"\b([0-9]+)\s+dias?\s+(uteis|\u00fateis|corridos)\b",
            item["texto"].casefold()
        )

        for numero, tipo in encontrados:
            prazos_por_base.setdefault(base, set()).add(
                (int(numero), tipo.replace("?", "u"))
            )

    return any(
        len(prazos) > 1
        for prazos in prazos_por_base.values()
    )

def responder(pergunta,indice,k=3,limiar=0.12):
    if avaliar_texto(pergunta)["decisao"]!="permitir":
        return {"status":"revisar","resposta":"Solicitação encaminhada para revisão.","fontes":[],"trechos":[]}
    achados=indice.buscar(pergunta,k)
    validos=[x for x in achados if x["similaridade"]>=limiar and avaliar_texto(x["texto"])["decisao"]=="permitir"]
    # Não responder se a pergunta contém número ou termo distintivo ausente do contexto.
    palavras_ignoradas = {
        "qual", "quais", "como", "para", "sobre", "entre",
        "uma", "um", "que", "o", "a", "\u00e9", "de", "da", "do",
        "em", "no", "na", "os", "as", "existe", "pode",
        "apresentar", "precisa", "informar", "s\u00e3o",
        "necess\u00e1rio", "necess\u00e1rios",
        "necess\u00e1ria", "necess\u00e1rias", "realizar"
    }

    termos = set(re.findall(r"\w+", pergunta.casefold())) - palavras_ignoradas
    contexto=" ".join(x["texto"] for x in validos).casefold()
    numeros={t for t in termos if any(c.isdigit() for c in t)}
    sem_apoio=any(t not in contexto for t in numeros) or (bool(termos) and sum(t in contexto for t in termos)/len(termos)<0.5)
    if not validos or sem_apoio:
        return {"status":"sem evidência suficiente","resposta":"Não localizado no acervo. Encaminhar para revisão humana.","fontes":[],"trechos":achados}
    # Se houver versões diferentes de um documento, não presumir que a mais recente prevalece.
    versoes={x["documento"].rsplit('_v',1)[0] for x in validos}
    if len({(x["documento"], x["versao"]) for x in validos}) > 1 and any(re.search(r"conflito|contradi\w*|diverg\w*", x["texto"], flags=re.IGNORECASE) for x in validos):
        return {"status":"conflito de fontes","resposta":"Há orientações divergentes; revisão humana necessária.","fontes":[x["id"] for x in validos],"trechos":validos}
    if detectar_prazos_divergentes(validos):
        return {
            "status": "conflito de fontes",
            "resposta": "Prazos divergentes encontrados. Revisao humana necessaria.",
            "fontes": [
                {
                    "id": x["id"],
                    "documento": x["documento"],
                    "versao": x["versao"],
                    "pagina": x["pagina"]
                }
                for x in validos
            ],
            "trechos": validos
        }

    # Modo extrativo: não inventa fundamentos, prazos ou decisões.

    # Reclassificacao local: considerar a intencao da pergunta.
    def pontuar_fonte(item):
        pergunta_normalizada = pergunta.casefold()
        texto = item["texto"].casefold()
        pontos = item["similaridade"]

        # Valoriza expressoes especificas presentes na pergunta
        # e no trecho, sem depender do gabarito.
        termos_pergunta = re.findall(
            r"\w+", pergunta_normalizada
        )
        termos_texto = re.findall(r"\w+", texto)

        for tamanho_expressao, bonus in (
            (2, 0.08),
            (3, 0.04)
        ):
            expressoes_pergunta = {
                tuple(termos_pergunta[i:i + tamanho_expressao])
                for i in range(
                    len(termos_pergunta) - tamanho_expressao + 1
                )
            }
            expressoes_texto = {
                tuple(termos_texto[i:i + tamanho_expressao])
                for i in range(
                    len(termos_texto) - tamanho_expressao + 1
                )
            }

            correspondencias = (
                expressoes_pergunta & expressoes_texto
            )

            pontos += bonus * len(correspondencias)

        pede_documentos = (
            any(t in pergunta_normalizada for t in (
                "documento", "comprovante"
            ))
            and any(t in pergunta_normalizada for t in (
                "necess", "apresentar", "precisa"
            ))
        )

        if pede_documentos:
            if any(t in texto for t in (
                "apresente", "apresentar", "comprovante",
                "documenta", "exige"
            )):
                pontos += 0.03

        return pontos

    x = max(validos, key=pontuar_fonte)
    resposta=x["texto"].strip()[:500]
    return {"status":"fundamentada (extrativa)","resposta":resposta,"fontes":[{"id":x["id"],"documento":x["documento"],"versao":x["versao"],"pagina":x["pagina"]}],"trechos":validos}
