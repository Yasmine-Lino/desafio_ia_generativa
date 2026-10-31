"""Contagens determinísticas, sem confundir estimativa com fato (RF23)."""
from collections import Counter

def proporcao(acertos,total): return {"numerador":acertos,"denominador":total,"taxa":acertos/total if total else None}
def sentimentos(resultados):
    ids=set();validos=[]
    for r in resultados:
        if r["id"] not in ids: validos.append(r);ids.add(r["id"])
    return {"total":len(validos),"polaridades":dict(Counter(x["polaridade"] for x in validos)),"revisao":sum(x["necessita_revisao"] for x in validos)}
