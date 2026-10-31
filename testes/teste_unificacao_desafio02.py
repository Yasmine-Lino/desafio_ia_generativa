from src.backends.indices import criar_indice, buscar_trechos
from src.backends.contratos import adaptar_resposta_lexical, adaptar_resposta_semantica
from src.backends.matriz_evidencias import gerar_matriz
import pytest


def test_indice_lexical_isolado(tmp_path):
    indice = criar_indice("lexical", tmp_path / "lexical.json")
    assert indice.dados["modelo"] == "hashing-lexical-v1"


def test_backend_invalido():
    with pytest.raises(ValueError):
        criar_indice("desconhecido")


def test_adaptador_lexical():
    resposta = adaptar_resposta_lexical({"status": "sem evidência suficiente", "resposta": "Sem resposta", "fontes": []})
    assert resposta.precisa_revisao


def test_adaptador_semantico():
    class Resposta:
        status = "fundamentada"
        resposta = "texto"
        fontes = ["doc"]
        precisa_revisao = False
    assert adaptar_resposta_semantica(Resposta()).fontes == ["doc"]


def test_matriz_nao_inventa_aprovacoes():
    matriz = gerar_matriz({"T01": {"aprovado": True}, "T02": {"aprovado": True, "referencia": "teste real"}})
    assert len(matriz) == 15
    assert matriz[0]["situacao"] == "Não verificado"
    assert matriz[1]["situacao"] == "Passou"

class IndiceLexicalSimulado:
    def buscar(self, pergunta, k):
        assert k == 2
        return [{"id": "c1", "texto": "Trecho", "documento": "edital.pdf", "versao": "1", "pagina": 2, "similaridade": 0.45}]


class IndiceSemanticoSimulado:
    def buscar(self, pergunta, top_k):
        assert top_k == 2
        return [{"chunk_id": "c2", "texto": "Outro trecho", "metadados": {"doc_id": "edital"}, "distancia": 0.12}]


def test_busca_lexical_normalizada():
    itens = buscar_trechos(IndiceLexicalSimulado(), "matricula", quantidade=2)
    assert itens[0]["tipo_pontuacao"] == "cosseno_lexical"
    assert itens[0]["documento"] == "edital.pdf"


def test_busca_semantica_normalizada_sem_confundir_scores():
    itens = buscar_trechos(IndiceSemanticoSimulado(), "matricula", modo="semantico", quantidade=2)
    assert itens[0]["tipo_pontuacao"] == "distancia_chroma"
    assert itens[0]["pontuacao"] == 0.12


@pytest.mark.parametrize("pergunta,quantidade", [("", 1), ("  ", 1), ("ok", 0), ("ok", True)])
def test_busca_rejeita_entradas_invalidas(pergunta, quantidade):
    with pytest.raises(ValueError):
        buscar_trechos(IndiceLexicalSimulado(), pergunta, quantidade=quantidade)


def test_busca_rejeita_modo_desconhecido():
    with pytest.raises(ValueError):
        buscar_trechos(IndiceLexicalSimulado(), "ok", modo="desconhecido")
