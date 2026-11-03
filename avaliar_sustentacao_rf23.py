import json
import re
import unicodedata
from pathlib import Path

from src.embeddings import Indice
from src.rag import responder

def normalizar(texto):
    texto = unicodedata.normalize("NFKD", str(texto).lower())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", texto).strip()

def dividir_afirmacoes(texto):
    return [
        x.strip()
        for x in re.split(r"(?<=[.!?])\s+|\n+", texto or "")
        if len(x.strip()) >= 12
    ]

def texto_fonte(trecho):
    for campo in ("texto", "conteudo", "content"):
        valor = trecho.get(campo)
        if isinstance(valor, str) and valor.strip():
            return valor
    return ""

perguntas = json.loads(
    Path("dados/gabaritos/desafio2_perguntas.json").read_text(encoding="utf-8")
)

indice = Indice("indice/desafio2_avaliacao.json")
indice.indexar(sorted(Path("dados/acervo").glob("*.txt")))

resultados = []
total = 0
sustentadas = 0
sem_texto_fonte = 0

for caso in perguntas:
    resultado = responder(caso["pergunta"], indice)
    resposta = resultado.get("resposta") or ""
    trechos = resultado.get("trechos") or []

    afirmacoes = dividir_afirmacoes(resposta)
    fontes = [texto_fonte(t) for t in trechos]
    fontes = [f for f in fontes if f]

    avaliacoes = []
    for afirmacao in afirmacoes:
        texto = normalizar(afirmacao)
        suporte = any(texto in normalizar(f) for f in fontes)
        total += 1
        sustentadas += int(suporte)

        if not fontes:
            sem_texto_fonte += 1

        avaliacoes.append({
            "afirmacao": afirmacao,
            "sustentada_textualmente": suporte
        })

    resultados.append({
        "id": caso["id"],
        "status": resultado.get("status"),
        "fontes": [t.get("documento") for t in trechos],
        "afirmacoes": avaliacoes
    })

saida = {
    "metodo": "correspondencia textual normalizada nos trechos citados",
    "tipo": "avaliacao offline conservadora",
    "afirmacoes_avaliadas": total,
    "afirmacoes_sustentadas_textualmente": sustentadas,
    "taxa_sustentacao_textual": round(sustentadas / total, 4) if total else None,
    "afirmacoes_sem_texto_fonte_disponivel": sem_texto_fonte,
    "observacao": (
        "Nao representa validacao semantica ou factual completa. "
        "Se os trechos nao incluirem o texto documental, "
        "a sustentacao nao pode ser confirmada por este metodo."
    ),
    "casos": resultados
}

destino = Path("resultados/metricas/rf23_sustentacao.json")
destino.parent.mkdir(parents=True, exist_ok=True)
destino.write_text(
    json.dumps(saida, ensure_ascii=False, indent=2),
    encoding="utf-8"
)

print(json.dumps({
    "afirmacoes_avaliadas": total,
    "afirmacoes_sustentadas": sustentadas,
    "taxa_sustentacao_textual": saida["taxa_sustentacao_textual"],
    "sem_texto_fonte": sem_texto_fonte,
    "arquivo": str(destino)
}, ensure_ascii=False, indent=2))
