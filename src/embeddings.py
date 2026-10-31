"""Índice vetorial local persistente por hashing de termos (RF17).

Modelo determinístico lexical, sem semântica profunda; similaridade cosseno
não é confiança de verdade. Nenhuma chave ou conexão externa é necessária.
"""
import hashlib
import json
import math
import re
from pathlib import Path
from .ingestion import documento

MODELO="hashing-lexical-v1"
DIMENSAO=1024

def vetor(texto):
    v=[0.0]*DIMENSAO
    for termo in re.findall(r"\w+",texto.casefold()):
        h=int(hashlib.sha256(termo.encode()).hexdigest()[:8],16)
        v[h%DIMENSAO]+=1.0
    norma=math.sqrt(sum(x*x for x in v)) or 1.0
    return [x/norma for x in v]

class Indice:
    def __init__(self,caminho="indice/acervo.json"):
        self.caminho=Path(caminho); self.dados={"modelo":MODELO,"dimensao":DIMENSAO,"versao_indice":1,"itens":{}}
        if self.caminho.exists():
            self.dados=json.loads(self.caminho.read_text(encoding="utf-8"))
            if (self.dados["modelo"],self.dados["dimensao"])!=(MODELO,DIMENSAO):
                raise ValueError("Modelo de embedding mudou: reindexe em índice novo")
    def salvar(self):
        self.caminho.parent.mkdir(parents=True,exist_ok=True)
        self.caminho.write_text(json.dumps(self.dados,ensure_ascii=False,indent=2),encoding="utf-8")
    def indexar(self,arquivos,tamanho=600,sobreposicao=100):
        for arq in arquivos:
            partes=documento(arq,tamanho,sobreposicao)
            if not partes: continue
            nome=partes[0]["documento"]
            self.dados["itens"]={k:v for k,v in self.dados["itens"].items() if v["documento"]!=nome}
            for p in partes:
                p["vetor"]=vetor(p["texto"]);self.dados["itens"][p["id"]]=p
        self.dados["versao_indice"]+=1;self.salvar()
    def excluir(self,nome):
        self.dados["itens"]={k:v for k,v in self.dados["itens"].items() if v["documento"]!=nome}
        self.dados["versao_indice"]+=1;self.salvar()
    def buscar(self,pergunta,k=3):
        q=vetor(pergunta);itens=[]
        for p in self.dados["itens"].values():
            s=sum(a*b for a,b in zip(q,p["vetor"]))
            if s>0:itens.append({k:v for k,v in p.items() if k!="vetor"}|{"similaridade":round(s,5)})
        return sorted(itens,key=lambda x:x["similaridade"],reverse=True)[:k]
