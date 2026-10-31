"""
Testes do RF16 - Guardrails, moderacao e limites.

Cobre T04 (tres entradas adversariais: instrucoes nao executadas,
segredo nao revelado) e T05 (fora de escopo, arquivo excessivo,
limite de chamadas).
"""

import json
import unittest

from src.guardrails import (
    LIMITE_TEXTO_SOLICITACAO,
    MAX_RETRIES,
    TAMANHO_MAX_ARQUIVO_MB,
    Camada,
    Decisao,
    OrcamentoExecucao,
    TAG_DOC_FIM,
    TAG_DOC_INICIO,
    montar_contexto_seguro,
    tratar_documento_recuperado,
    validar_entrada,
    validar_saida,
)


class TestT04AtaquesAdversariais(unittest.TestCase):
    """T04: as tres entradas adversariais devem ser bloqueadas."""

    @classmethod
    def setUpClass(cls):
        with open("dados/gabaritos/adversariais.json", encoding="utf-8") as f:
            cls.ataques = {a["id"]: a for a in json.load(f)["ataques"]}

    def test_adv01_injecao_na_solicitacao_bloqueada(self):
        r = validar_entrada(self.ataques["adv01"]["texto_ataque"])
        self.assertEqual(r.decisao, Decisao.BLOQUEAR)
        self.assertEqual(r.camada, Camada.ENTRADA)

    def test_adv01_nao_autoriza_aprovacao(self):
        """A instrucao nao pode ser executada: nao deve haver saida do tipo 'aprovado'."""
        r = validar_entrada(self.ataques["adv01"]["texto_ataque"])
        # O guardrail nao produz saida; apenas bloqueia. Nao ha como "aprovar".
        self.assertEqual(r.decisao, Decisao.BLOQUEAR)
        self.assertIsNone(r.texto_saneado)

    def test_adv02_acervo_envenenado_bloqueado(self):
        with open(self.ataques["adv02"]["documento_ficticio"], encoding="utf-8") as f:
            texto = f.read()
        r = tratar_documento_recuperado(texto)
        self.assertEqual(r.decisao, Decisao.BLOQUEAR)
        self.assertEqual(r.camada, Camada.PROCESSAMENTO)

    def test_adv02_conteudo_e_delimitado(self):
        with open(self.ataques["adv02"]["documento_ficticio"], encoding="utf-8") as f:
            texto = f.read()
        r = tratar_documento_recuperado(texto)
        self.assertIn(TAG_DOC_INICIO, r.texto_saneado)
        self.assertIn(TAG_DOC_FIM, r.texto_saneado)

    def test_adv03_segredo_bloqueado(self):
        r = validar_entrada(self.ataques["adv03"]["texto_ataque"])
        self.assertEqual(r.decisao, Decisao.BLOQUEAR)

    def test_nenhum_segredo_aparece_na_saida_do_bloqueio(self):
        """O motivo do bloqueio nao deve reproduzir a senha ou chave pedida."""
        for ataque in self.ataques.values():
            if ataque["id"] == "adv02":
                continue
            r = validar_entrada(ataque["texto_ataque"])
            self.assertNotIn("SENHA_REAL", r.motivo)
            self.assertNotIn("sk-", r.motivo)

    def test_contexto_seguro_delimita_e_sinaliza(self):
        with open(self.ataques["adv02"]["documento_ficticio"], encoding="utf-8") as f:
            texto = f.read()
        r = montar_contexto_seguro(["texto normal", texto, "outro normal"])
        self.assertEqual(r.decisao, Decisao.REVISAR)
        self.assertIn(TAG_DOC_INICIO, r.texto_saneado)


class TestT05LimitesERecursos(unittest.TestCase):
    """T05: fora de escopo, arquivo excessivo e limite de chamadas."""

    def test_texto_longo_bloqueado(self):
        r = validar_entrada("a" * (LIMITE_TEXTO_SOLICITACAO + 1))
        self.assertEqual(r.decisao, Decisao.BLOQUEAR)

    def test_extensao_invalida_bloqueada(self):
        r = validar_entrada("conteudo sobre inscricao", nome_arquivo="malware.exe")
        self.assertEqual(r.decisao, Decisao.BLOQUEAR)

    def test_arquivo_excessivo_bloqueado(self):
        r = validar_entrada(
            "conteudo sobre inscricao",
            nome_arquivo="doc.pdf",
            tamanho_bytes=(TAMANHO_MAX_ARQUIVO_MB + 1) * 1024 * 1024,
        )
        self.assertEqual(r.decisao, Decisao.BLOQUEAR)

    def test_fora_de_escopo_revisar(self):
        r = validar_entrada("Quero saber a previsao do tempo para amanha.")
        self.assertEqual(r.decisao, Decisao.REVISAR)

    def test_dentro_de_escopo_permite(self):
        r = validar_entrada("Quero informacoes sobre a inscricao no curso de Enfermagem.")
        self.assertEqual(r.decisao, Decisao.PERMITIR)

    def test_teto_de_chamadas_respeitado(self):
        orc = OrcamentoExecucao(max_chamadas=3)
        for _ in range(3):
            self.assertEqual(orc.pode_chamar().decisao, Decisao.PERMITIR)
            orc.registrar()
        self.assertEqual(orc.pode_chamar().decisao, Decisao.BLOQUEAR)

    def test_teto_de_tokens_respeitado(self):
        orc = OrcamentoExecucao(max_tokens=100)
        orc.registrar(tokens=150)
        self.assertEqual(orc.pode_chamar().decisao, Decisao.BLOQUEAR)

    def test_retry_maximo_um(self):
        orc = OrcamentoExecucao()
        self.assertTrue(orc.registrar_falha_transitoria())  # 1 retry permitido
        self.assertFalse(orc.registrar_falha_transitoria())  # 2o nao
        self.assertEqual(MAX_RETRIES, 1)


class TestCamadaSaida(unittest.TestCase):
    def test_saida_com_chave_e_removida(self):
        r = validar_saida("A chave e GEMINI_API_KEY=abc123xyz e o resto.")
        self.assertEqual(r.decisao, Decisao.BLOQUEAR)
        self.assertNotIn("abc123xyz", r.texto_saneado)
        self.assertIn("[REMOVIDO]", r.texto_saneado)

    def test_saida_com_caminho_absoluto_removido(self):
        r = validar_saida(r"Salvo em C:\\Users\\adria\\dados\\arquivo.txt")
        self.assertEqual(r.decisao, Decisao.BLOQUEAR)
        self.assertIn("[REMOVIDO]", r.texto_saneado)

    def test_saida_limpa_permite(self):
        r = validar_saida("O prazo de inscricao e 13/05/2026. [DOC02]")
        self.assertEqual(r.decisao, Decisao.PERMITIR)

    def test_saida_institucional_sem_citacao_revisar(self):
        r = validar_saida("O prazo de inscricao e 13/05/2026.", exigir_citacao=True)
        self.assertEqual(r.decisao, Decisao.REVISAR)


if __name__ == "__main__":
    unittest.main()