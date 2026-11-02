from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest


def criar_resultado(status="pendente"):
    return {
        "id": "teste-rf20",
        "status": status,
        "ficha": {"estrutura": {"assunto": "Teste"}},
        "rag": {
            "status": "fundamentada (extrativa)",
            "resposta": "Resposta ficticia",
            "trechos": [],
        },
    }


def iniciar_interface():
    app = AppTest.from_file(Path(__file__).resolve().parent.parent / "src" / "app.py", default_timeout=15)
    app.run()
    assert not app.exception
    return app


def test_rf20_interface_inicializa():
    app = iniciar_interface()

    assert len(app.tabs) == 3
    assert app.selectbox[1].value == "Extrativo (local)"


def test_rf20_modo_extrativo_nao_chama_provedor():
    app = iniciar_interface()

    with (
        patch("src.fluxo_desafio2.executar", return_value=criar_resultado()),
        patch("src.fluxo_desafio2.executar_rag_provedor") as externo,
    ):
        app.button[2].click().run()

    assert not app.exception
    externo.assert_not_called()


def test_rf20_bloqueia_provedor_quando_exige_revisao():
    app = iniciar_interface()

    app.selectbox[1].set_value("OpenAI")

    with (
        patch(
            "src.fluxo_desafio2.executar",
            return_value=criar_resultado("revisar"),
        ),
        patch("src.fluxo_desafio2.executar_rag_provedor") as externo,
    ):
        app.button[2].click().run()

    assert not app.exception
    externo.assert_not_called()
import pytest


@pytest.mark.parametrize("provedor", ["OpenAI", "Gemini"])
def test_rf20_seleciona_provedor_sem_chamada_real(provedor):
    app = iniciar_interface()
    app.selectbox[1].set_value(provedor).run()

    resposta_externa = {
        "status": "revisar",
        "provedor_solicitado": provedor.lower(),
        "geracao": {
            "texto": "Resposta simulada para teste",
        },
        "envio_automatico": False,
    }

    with (
        patch("src.fluxo_desafio2.executar", return_value=criar_resultado("pendente")),
        patch(
            "src.fluxo_desafio2.executar_rag_provedor",
            return_value=resposta_externa,
        ) as gerar_externo,
    ):
        app.button[2].click().run()

    assert not app.exception
    gerar_externo.assert_called_once()
    assert gerar_externo.call_args.kwargs["modo"] == provedor.lower()
    assert any(
        "Resposta simulada para teste" in elemento.value
        for elemento in app.markdown
    )
def test_rf20_geracao_externa_nao_permite_aprovacao():
    app = iniciar_interface()
    app.selectbox[1].set_value("OpenAI").run()

    resposta_externa = {
        "status": "revisar",
        "provedor_solicitado": "openai",
        "geracao": {"texto": "Resposta simulada"},
        "envio_automatico": False,
    }

    with (
        patch(
            "src.fluxo_desafio2.executar",
            return_value=criar_resultado("pendente"),
        ),
        patch(
            "src.fluxo_desafio2.executar_rag_provedor",
            return_value=resposta_externa,
        ),
    ):
        app.button[2].click().run()

    assert not app.exception

    mensagens = [elemento.value for elemento in app.warning]
    assert any(
        "Nao e possivel aprova-la" in mensagem
        for mensagem in mensagens
    )

    assert not any(
        botao.label == "Registrar decisao"
        for botao in app.button
    )
