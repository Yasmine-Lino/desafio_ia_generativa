"""Teste da barreira de aprovação antes de chamar serviços externos."""
import tempfile
import unittest
from pathlib import Path
from src.sintese_voz import sintetizar_minuta


class TesteAprovacaoTTS(unittest.TestCase):
    def test_sem_id_de_aprovacao_nao_consulta_api(self):
        with tempfile.TemporaryDirectory() as pasta:
            minuta = Path(pasta) / 'minuta.txt'
            minuta.write_text('Minuta fictícia.', encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'execução da minuta aprovada'):
                sintetizar_minuta(minuta, aprovado=True)
