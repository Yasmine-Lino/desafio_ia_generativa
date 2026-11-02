"""Interface Streamlit local do Desafio 2 (RF20/22/24)."""
from pathlib import Path
import hashlib
import json
import streamlit as st
from src.embeddings import Indice
from src.exclusao_desafio2 import excluir_documento
from src.fluxo_desafio2 import executar, revisar, executar_rag_provedor
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
    arquivos_indexados = {x["documento"]: x["hash"] for x in indice.dados["itens"].values()}
    if any(
        Path(nome).name not in arquivos_indexados
        or arquivos_indexados[Path(nome).name] != hashlib.sha256(Path(nome).read_bytes()).hexdigest()
        for nome in selecionados
    ):
        st.warning("Índice desatualizado ou documentos ainda não indexados. Clique em Indexar documentos.")
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
    entrada=st.text_area("Solicitacao ficticia")

    modo=st.selectbox(
        "Modo de processamento",
        ["Extrativo (local)", "OpenAI", "Gemini"],
        index=0,
    )

    if st.button("Processar solicitacao"):
        try:
            resultado=executar(entrada,indice)
            st.session_state["ultimo"]=resultado
            st.session_state.pop("ultima_geracao_externa",None)

            if modo in ("OpenAI","Gemini"):
                if resultado["status"] == "revisar":
                    st.warning(
                        "Solicitacao exige revisao. "
                        "O provedor externo nao sera chamado."
                    )
                else:
                    externo=executar_rag_provedor(
                        entrada,
                        indice,
                        modo=modo.lower(),
                    )
                    st.session_state["ultima_geracao_externa"]=externo

        except Exception as erro:
            st.error(str(erro))

    if "ultima_geracao_externa" in st.session_state:
        externo=st.session_state["ultima_geracao_externa"]
        st.subheader("Geracao com provedor externo")
        st.write("Provedor:",externo["provedor_solicitado"])
        st.write("Estado:",externo["status"])

        if externo.get("geracao"):
            st.write(externo["geracao"].get("texto",""))
        else:
            st.warning(
                "Geracao nao realizada. "
                "Consulte as evidencias e revise a solicitacao."
            )
    if "ultimo" in st.session_state:
        r=st.session_state["ultimo"]
        st.subheader("Ficha e resumo");st.json(r["ficha"])
        st.subheader("Minuta preliminar (extrativa) e fontes");st.write(r["rag"]["status"]);st.write(r["rag"]["resposta"] or "Não localizado");st.json(r["rag"]["trechos"])
with t2:
    if "ultimo" not in st.session_state:
        st.info("Processe uma solicitacao primeiro")
    else:
        r = st.session_state["ultimo"]
        externo = st.session_state.get("ultima_geracao_externa")

        if externo is not None:
            st.warning(
                "A geracao externa ainda nao esta vinculada "
                "ao registro de revisao humana. "
                "Nao e possivel aprova-la nesta interface."
            )
            st.write(
                "Provedor externo:",
                externo["provedor_solicitado"],
            )
            st.write("Estado da geracao:", externo["status"])
        else:
            st.write("Estado:", r["status"])
            decisao = st.selectbox(
                "Decisao",
                ["revisar", "rejeitada", "aprovada"],
            )
            motivo = st.text_input("Justificativa")

            if st.button("Registrar decisao"):
                try:
                    st.success(str(revisar(r, decisao, motivo)))
                except Exception as erro:
                    st.error(str(erro))
with t3:
    caminho = Path("dados/avaliacoes/avaliacoes.json")

    if caminho.exists():
        avaliacoes = json.loads(caminho.read_text(encoding="utf-8"))
        saidas = [classificar(x) for x in avaliacoes]

        ids = set()
        unicos = []

        for item in saidas:
            if item["id"] not in ids:
                unicos.append(item)
                ids.add(item["id"])

        polaridade = st.selectbox(
            "Filtrar por sentimento",
            ["Todas", "positiva", "negativa", "neutra", "indeterminada"],
        )

        revisao = st.selectbox(
            "Filtrar por revisao",
            ["Todas", "Necessita revisao", "Nao necessita revisao"],
        )

        filtrados = [
            item for item in unicos
            if (polaridade == "Todas" or item["polaridade"] == polaridade)
            and (
                revisao == "Todas"
                or (
                    revisao == "Necessita revisao"
                    and item["necessita_revisao"]
                )
                or (
                    revisao == "Nao necessita revisao"
                    and not item["necessita_revisao"]
                )
            )
        ]

        total = len(unicos)
        quantidade = len(filtrados)
        percentual = quantidade / total * 100 if total else 0

        st.write(
            f"Avaliacoes filtradas: {quantidade} de {total} "
            f"({quantidade}/{total} = {percentual:.1f}%)"
        )

        if filtrados:
            resumo = sentimentos(filtrados)
            st.json(resumo)
            st.dataframe(filtrados)
            st.bar_chart(resumo["polaridades"])
        else:
            st.info("Nenhuma avaliacao encontrada para os filtros selecionados.")
    else:
        st.info("Avaliacoes ficticias nao encontradas")
