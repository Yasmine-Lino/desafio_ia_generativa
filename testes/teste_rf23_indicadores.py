import json
from pathlib import Path

from streamlit.testing.v1 import AppTest

from src.metrics import proporcao, sentimentos
from src.sentiment import classificar


def carregar_avaliacoes():
    caminho = Path("dados/avaliacoes/avaliacoes.json")
    return json.loads(caminho.read_text(encoding="utf-8"))


def iniciar_app():
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / "src" / "app.py"), default_timeout=30)
    app.run()
    assert not app.exception
    return app


def indicador(app):
    textos = [
        elemento.value
        for elemento in app.get("markdown")
        if "Avaliacoes filtradas:" in elemento.value
    ]
    assert len(textos) == 1
    return textos[0]


def test_t13_total_avaliacoes():
    avaliacoes = carregar_avaliacoes()
    saidas = [classificar(item) for item in avaliacoes]

    assert len(avaliacoes) == 12
    assert sentimentos(saidas)["total"] == 12


def test_t13_duplicatas():
    saidas = [
        classificar({"id": "A01", "texto": "Atendimento bom"}),
        classificar({"id": "A01", "texto": "Atendimento bom"}),
        classificar({"id": "A02", "texto": "Atendimento ruim"}),
    ]

    resumo = sentimentos(saidas)

    assert resumo["total"] == 2
    assert sum(resumo["polaridades"].values()) == 2


def test_t13_conjunto_vazio():
    resumo = sentimentos([])
    percentual = proporcao(0, 0)

    assert resumo["total"] == 0
    assert resumo["polaridades"] == {}
    assert resumo["revisao"] == 0

    assert percentual["numerador"] == 0
    assert percentual["denominador"] == 0
    assert percentual["taxa"] is None


def test_t13_indicador_inicial():
    app = iniciar_app()

    assert "12 de 12" in indicador(app)
    assert "12/12" in indicador(app)


def test_t13_filtro_polaridade():
    app = iniciar_app()

    app.selectbox[2].set_value("positiva").run()

    assert not app.exception

    avaliacoes = carregar_avaliacoes()
    positivas = sum(
        classificar(item)["polaridade"] == "positiva"
        for item in avaliacoes
    )

    assert f"{positivas} de 12" in indicador(app)
    assert f"{positivas}/12" in indicador(app)


def test_t13_filtro_revisao():
    app = iniciar_app()

    app.selectbox[3].set_value("Necessita revisao").run()

    assert not app.exception

    avaliacoes = carregar_avaliacoes()
    revisoes = sum(
        classificar(item)["necessita_revisao"]
        for item in avaliacoes
    )

    assert f"{revisoes} de 12" in indicador(app)
    assert f"{revisoes}/12" in indicador(app)


def test_t13_filtros_combinados():
    app = iniciar_app()

    app.selectbox[2].set_value("positiva").run()
    app.selectbox[3].set_value("Necessita revisao").run()

    assert not app.exception
    assert "0 de 12" in indicador(app)
    assert "0/12" in indicador(app)

    mensagens = [
        elemento.value
        for elemento in app.info
    ]

    assert any(
        "Nenhuma avaliacao encontrada" in mensagem
        for mensagem in mensagens
    )

def test_t13_arquivo_vazio_na_interface(monkeypatch):
    caminho = Path("dados/avaliacoes/avaliacoes.json")
    leitura_original = Path.read_text

    def leitura_simulada(self, *args, **kwargs):
        if self.as_posix().endswith(caminho.as_posix()):
            return "[]"
        return leitura_original(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", leitura_simulada)

    app = iniciar_app()

    assert "0 de 0" in indicador(app)
    assert "0/0" in indicador(app)
    assert "0.0%" in indicador(app)

    mensagens = [elemento.value for elemento in app.info]

    assert any(
        "Nenhuma avaliacao encontrada" in mensagem
        for mensagem in mensagens
    )
