"""Leitura textual do acervo e chunking com metadados (RF17/18)."""
import hashlib
from pathlib import Path
from .guardrails import validar_arquivo

def ler_documento(caminho):
    p=validar_arquivo(caminho)
    if p.suffix.lower()==".txt": return [(1,p.read_text(encoding="utf-8-sig"))]
    import fitz
    with fitz.open(p) as pdf:
        return [(i+1,pagina.get_text()) for i,pagina in enumerate(pdf)]

def dividir(texto,tamanho=600,sobreposicao=100):
    if tamanho<=0 or not 0<=sobreposicao<tamanho: raise ValueError("Parâmetros de chunk inválidos")
    return [texto[i:i+tamanho] for i in range(0,len(texto),tamanho-sobreposicao) if texto[i:i+tamanho].strip()]

def documento(caminho,tamanho=600,sobreposicao=100):
    p=Path(caminho); bruto=p.read_bytes(); hash_doc=hashlib.sha256(bruto).hexdigest()
    titulo=p.stem; partes=titulo.rsplit('_v',1)
    versao=partes[-1] if len(partes)==2 and partes[-1].isdigit() else "1"
    itens=[]
    for pagina,txt in ler_documento(p):
        for n,chunk in enumerate(dividir(txt,tamanho,sobreposicao)):
            identificador=f"{p.name}:p{pagina}:t{n}"
            itens.append({"id":identificador,"documento":p.name,"titulo":titulo,"versao":versao,"hash":hash_doc,"pagina":pagina,"secao":f"Página {pagina}","texto":chunk})
    return itens
