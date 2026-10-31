"""Interface Streamlit local do Desafio 2 (RF20/22/24)."""
from pathlib import Path
import json
import streamlit as st
from src.embeddings import Indice
from src.exclusao_desafio2 import excluir_documento
from src.fluxo_desafio2 import executar, revisar
from src.sentiment import classificar
from src.metrics import sentimentos

st.set_page_config(page_title="Central de Atendimento - Desafio 2",layout="wide")
st.title("Central Inteligente de Atendimento — Desafio 2")
st.caption("Protótipo local. Respostas de IA exigem revisão humana; não há envio automático.")
indice=Indice()
t1,t2,t3=st.tabs(["Documentos e atendimento","Revisão","Sentimentos"])
with t1:
    st.write(f"Índice: {len(indice.dados['itens'])} trechos | versão {indice.dados['versao_indice']} | modelo {indice.dados['modelo']}")
    arquivos=sorted(Path("dados/acervo").glob("*.txt"))+sorted(Path("dados/acervo").glob("*.pdf"))
    selecionados=st.multiselect("Documentos para indexar",[str(x) for x in arquivos],default=[str(x) for x in arquivos if x.suffix.lower()==".txt"])
    if st.button("Indexar documentos"):
        try: indice.indexar(selecionados);st.success("Índice atualizado")
        except Exception as e:st.error(str(e))
    excluir=st.selectbox("Excluir documento do índice",[""]+sorted({x["documento"] for x in indice.dados["itens"].values()}))
    if st.button("Confirmar exclusão") and excluir:
        try:
            evento = excluir_documento(indice, excluir)
            if "ultimo" in st.session_state:
                ids_anteriores = {x["id"] for x in st.session_state["ultimo"]["rag"]["trechos"]}
                ids_atuais = set(indice.dados["itens"])
                if not ids_anteriores.issubset(ids_atuais):
                    del st.session_state["ultimo"]
            st.success(f"Trechos removidos: {evento['trechos_removidos']}. Exclusão registrada.")
        except Exception as e:
            st.error(str(e))
    entrada=st.text_area("Solicitação fictícia")
    if st.button("Processar solicitação"):
        try:st.session_state["ultimo"]=executar(entrada,indice)
        except Exception as e:st.error(str(e))
    if "ultimo" in st.session_state:
        r=st.session_state["ultimo"]
        st.subheader("Ficha e resumo");st.json(r["ficha"])
        st.subheader("Resposta e fontes");st.write(r["rag"]["status"]);st.write(r["rag"]["resposta"]);st.json(r["rag"]["trechos"])
with t2:
    if "ultimo" not in st.session_state:st.info("Processe uma solicitação primeiro")
    else:
        r=st.session_state["ultimo"];st.write("Estado:",r["status"])
        decisao=st.selectbox("Decisão",["revisar","rejeitada","aprovada"])
        motivo=st.text_input("Justificativa")
        if st.button("Registrar decisão"):
            try:st.success(str(revisar(r,decisao,motivo)))
            except Exception as e:st.error(str(e))
with t3:
    caminho=Path("dados/avaliacoes/avaliacoes.json")
    if caminho.exists():
        avaliacoes=json.loads(caminho.read_text(encoding="utf-8"))
        saidas=[classificar(x) for x in avaliacoes]
        st.json(sentimentos(saidas));st.dataframe(saidas)
        st.bar_chart(sentimentos(saidas)["polaridades"])
    else:st.info("Avaliações fictícias não encontradas")
