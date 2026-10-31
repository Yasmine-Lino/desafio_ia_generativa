"""
RF20 - Assistente de documentos em Streamlit.

- Interface local para fluxo integrado.
- Selecao/inclusao de documentos, indexacao, entrada da solicitacao.
- Visualizacao de ficha estruturada, resumo, categoria, minuta e fontes.
- Registro de aprovacao, rejeicao ou pedido de revisao com justificativa.
"""

import sys
from pathlib import Path

# Garante que a raiz do projeto esteja no sys.path quando o Streamlit rodar
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import streamlit as st
from src.ingestion import indexar_acervo, DIR_ACERVO
from src.rag import responder, StatusResposta
from src.nlp import gerar_ficha
from src.embeddings import IndiceVetorial

st.set_page_config(page_title="Central Inteligente - Desafio 02", layout="wide")

if "historico_revisoes" not in st.session_state:
    st.session_state.historico_revisoes = []
if "indice" not in st.session_state:
    st.session_state.indice = None
if "indice_pronto" not in st.session_state:
    st.session_state.indice_pronto = False


class LLMMock:
    """LLM simulado para permitir a demonstracao do fluxo sem chave de API."""
    def completar(self, prompt: str, **kwargs) -> str:
        if "Resuma" in prompt:
            return "Cidadao solicita informacoes sobre o processo seletivo das ETECs."
        if "Classifique" in prompt:
            return "inscricao"
        if "entidades" in prompt:
            return '{"entidades": [{"tipo": "orgao", "valor": "SECITECI", "origem": "literal"}], "ausentes": []}'
        return "SEM_EVIDENCIA"


with st.sidebar:
    st.header("1. Base de Conhecimento")
    if st.button("Indexar Acervo"):
        with st.spinner("Indexando..."):
            try:
                res = indexar_acervo()
                st.session_state.indice = IndiceVetorial()
                st.session_state.indice_pronto = True
                st.success(f"Acervo indexado! {res['chunks_no_indice']} trechos disponiveis.")
            except Exception as e:
                st.error(f"Erro ao indexar: {e}")

    if st.session_state.indice_pronto:
        st.info("Indice carregado e pronto para consulta.")
    else:
        st.warning("Indice nao gerado nesta sessao.")

    st.markdown("---")
    st.header("2. Modo de Operacao")
    st.write("LLM simulado para testes offline. Integracao com Gemini/Groq prevista no RF21.")


st.title("Central Inteligente de Atendimento")
st.markdown("Desafio 02 — Extracao, RAG, Guardrails e Revisao Humana")

tab1, tab2, tab3 = st.tabs(["Atender Solicitacao", "Painel", "Historico"])

with tab1:
    st.header("Entrada da Solicitacao")
    texto = st.text_area("Cole o texto da solicitacao do cidadao:", height=150)

    if st.button("Processar Solicitacao", type="primary"):
        if not texto.strip():
            st.warning("Digite uma solicitacao.")
        elif not st.session_state.indice_pronto:
            st.error("Indexe o acervo primeiro (menu lateral).")
        else:
            with st.spinner("Processando..."):
                llm = LLMMock()
                try:
                    ficha = gerar_ficha(texto, llm)
                except Exception as e:
                    ficha = None
                    st.error(f"Erro no NLP: {e}")

                try:
                    r = responder(texto, st.session_state.indice, llm=llm)
                except Exception as e:
                    r = None
                    st.error(f"Erro no RAG: {e}")

                if ficha and r:
                    st.session_state.solicitacao_atual = {
                        "texto": texto, "ficha": ficha, "resposta_rag": r,
                    }

    if "solicitacao_atual" in st.session_state:
        sol = st.session_state.solicitacao_atual
        st.markdown("---")
        st.subheader("Resultado da Analise")

        col1, col2 = st.columns(2)
        with col1:
            st.info(f"Categoria: {sol['ficha'].categoria}")
            st.text_area("Resumo", sol["ficha"].resumo, height=100, disabled=True)
        with col2:
            status = sol["resposta_rag"].status
            if status == StatusResposta.FUNDAMENTADA:
                st.success("Resposta fundamentada")
                st.write(sol["resposta_rag"].resposta)
            elif status == StatusResposta.SEM_EVIDENCIA:
                st.warning("Sem evidencia suficiente no acervo")
            else:
                st.error("Conflito de fontes — requer revisao humana")

        if sol["resposta_rag"].fontes:
            with st.expander("Ver fontes recuperadas"):
                for f in sol["resposta_rag"].fontes:
                    st.markdown(f"**{f.doc_id}** v{f.versao} ({f.data_publicacao}) — sim: {1.0 - f.distancia:.2f}")
                    st.text(f.trecho[:300] + "...")

        st.markdown("### Decisao do Operador")
        justificativa = st.text_input("Justificativa (obrigatoria para rejeitar ou revisar):")
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Aprovar", type="primary"):
                st.session_state.historico_revisoes.append(
                    {"status": "aprovada", "justificativa": justificativa, "texto": sol["texto"]}
                )
                st.success("Minuta aprovada e registrada.")
        with c2:
            if st.button("Rejeitar"):
                if not justificativa:
                    st.error("Justificativa obrigatoria para rejeitar.")
                else:
                    st.session_state.historico_revisoes.append(
                        {"status": "rejeitada", "justificativa": justificativa, "texto": sol["texto"]}
                    )
                    st.error("Minuta rejeitada.")
        with c3:
            if st.button("Enviar para Revisao"):
                st.session_state.historico_revisoes.append(
                    {"status": "revisao", "justificativa": justificativa, "texto": sol["texto"]}
                )
                st.warning("Enviado para revisao manual.")

with tab2:
    st.header("Painel de Indicadores")
    total = len(st.session_state.historico_revisoes)
    st.metric("Total de decisoes", total)
    if total:
        aprov = sum(1 for r in st.session_state.historico_revisoes if r["status"] == "aprovada")
        rej = sum(1 for r in st.session_state.historico_revisoes if r["status"] == "rejeitada")
        rev = sum(1 for r in st.session_state.historico_revisoes if r["status"] == "revisao")
        st.bar_chart({"Aprovadas": aprov, "Rejeitadas": rej, "Revisao": rev})

with tab3:
    st.header("Historico de Decisoes")
    if not st.session_state.historico_revisoes:
        st.info("Nenhuma decisao registrada ainda.")
    else:
        for i, h in enumerate(st.session_state.historico_revisoes, 1):
            st.write(f"**{i}.** {h['status'].upper()} — {h['justificativa'] or '(sem justificativa)'}")