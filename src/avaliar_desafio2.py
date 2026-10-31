"""Executa avaliação offline reproduzível sem alegar testes de API real."""
import json
from pathlib import Path
from .embeddings import Indice
from .nlp import ficha
from .sentiment import classificar
from .metrics import proporcao, sentimentos
from .rag import responder
from .guardrails import avaliar_texto

def ler(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def executar():
    arquivos=sorted(Path("dados/acervo").glob("*.txt"))
    indice=Indice("indice/desafio2_avaliacao.json");indice.indexar(arquivos)
    casos=ler("dados/solicitacoes/casos.json")
    fichas=[]
    for c in casos:
        try:
            x=ficha(c["texto"]);fichas.append({"id":c["id"],"obtido":x["categoria"],"resumo":x["resumo"],"entidades":x["entidades"],"revisao":x["estrutura"]["necessita_revisao"]})
        except Exception as e:fichas.append({"id":c["id"],"erro":str(e)})
    perguntas=ler("dados/gabaritos/desafio2_perguntas.json");rag=[]
    for p in perguntas:
        r=responder(p["pergunta"],indice)
        refs={x["documento"] for x in r["trechos"]}
        rag.append({"id":p["id"],"tipo":p["tipo"],"esperado":p["fontes_referencia"],"obtido":list(refs),"status":r["status"],"acerto_recuperacao":bool(refs.intersection(p["fontes_referencia"]))})
    comparacao=[]
    for tamanho,sobreposicao in ((400,60),(800,120)):
        ix=Indice(f"indice/avaliacao_{tamanho}.json")
        ix.indexar(arquivos,tamanho,sobreposicao)
        por_pergunta=[]
        for q in perguntas[:5]:
            encontrados={x["documento"] for x in ix.buscar(q["pergunta"],3)}
            por_pergunta.append({"id":q["id"],"acerto":bool(encontrados.intersection(q["fontes_referencia"])),"top3":sorted(encontrados)})
        comparacao.append({"tamanho_caracteres":tamanho,"sobreposicao_caracteres":sobreposicao,"top_k":3,"perguntas":por_pergunta,"taxa":proporcao(sum(x["acerto"] for x in por_pergunta),len(por_pergunta))})
    sent=[classificar(x) for x in ler("dados/avaliacoes/avaliacoes.json")]
    gab={x["id"]:x["polaridade"] for x in ler("dados/gabaritos/desafio2_sentimentos.json")}
    ataques=[{"id":x["id"],"decisao":avaliar_texto(x["texto"])} for x in ler("dados/gabaritos/desafio2_adversariais.json")]
    respondiveis=[x for x in rag if x["tipo"]=="respondível"]
    sem=[x for x in rag if x["tipo"]=="sem_resposta"]
    saida={"execucao":"offline-local","fichas":fichas,"rag":rag,"comparacao_chunking":comparacao,"sentimentos":sent,"ataques":ataques,"metricas":{"recuperacao_top3":proporcao(sum(x["acerto_recuperacao"] for x in respondiveis),len(respondiveis)),"abstencao":proporcao(sum(x["status"]=="sem evidência suficiente" for x in sem),len(sem)),"sentimentos":proporcao(sum(x["polaridade"]==gab[x["id"]] for x in sent),len(sent)),"totais":sentimentos(sent)}}
    p=Path("resultados/metricas/desafio2_offline.json");p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(saida,ensure_ascii=False,indent=2),encoding="utf-8")
    return saida
if __name__=="__main__":print(json.dumps(executar()["metricas"],ensure_ascii=False,indent=2))
