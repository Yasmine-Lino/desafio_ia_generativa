import unittest

from src.extracao import (
    extrair_dados_basicos,
    montar_resultado,
    preparar_texto
)


class TestesRF05(unittest.TestCase):

    def test_extrair_protocolo_e_data(self):
        texto = (
            "Canal: E-mail\n"
            "Protocolo: 2026-000142\n"
            "Data: 14/10/2026\n"
            "Meu nome é Marcos Silva, e solicito matrícula."
        )

        dados = extrair_dados_basicos(texto)

        self.assertEqual(dados["protocolo"], "2026-000142")
        self.assertEqual(dados["data"], "14/10/2026")
        self.assertEqual(dados["solicitante"], "Marcos Silva")

    def test_campos_ausentes(self):
        texto = "Gostaria de informações sobre matrícula."

        dados = montar_resultado(texto, {
            "assunto": "Matrícula",
            "pedido": "Informações sobre matrícula",
            "categoria": "matrícula",
            "confianca": "média"
        })

        self.assertEqual(dados["protocolo"], "não localizado")
        self.assertIn("protocolo", dados["campos_ausentes"])
        self.assertIn("data", dados["campos_ausentes"])
        self.assertIn("solicitante", dados["campos_ausentes"])
        self.assertTrue(dados["revisao_humana"])

    def test_categoria_invalida(self):
        dados = montar_resultado("Solicitação de teste", {
            "assunto": "Teste",
            "pedido": "Pedido de teste",
            "categoria": "categoria inventada",
            "confianca": "alta"
        })

        self.assertEqual(dados["categoria"], "outros")
        self.assertEqual(dados["confianca"], "baixa")

    def test_protecao_dados(self):
        texto = (
            "Meu nome é Marcos Silva, nasci em 12/08/2008, "
            "CPF 123.456.789-00; RG 1234567-8; "
            "nome da mãe, Maria Silva; "
            "e-mail teste@exemplo.com."
        )

        protegido = preparar_texto(texto)

        self.assertNotIn("123.456.789-00", protegido)
        self.assertNotIn("1234567-8", protegido)
        self.assertNotIn("12/08/2008", protegido)
        self.assertNotIn("Maria Silva", protegido)
        self.assertNotIn("teste@exemplo.com", protegido)
        self.assertNotIn("Marcos Silva", protegido)

    def test_json_valido_com_campos_ausentes(self):
        import json

        dados = montar_resultado("Texto incompleto", {
            "assunto": "",
            "pedido": "",
            "categoria": "outros",
            "confianca": "baixa"
        })

        convertido = json.dumps(dados, ensure_ascii=False)
        recuperado = json.loads(convertido)

        self.assertEqual(recuperado["assunto"], "não localizado")
        self.assertEqual(recuperado["pedido"], "não localizado")


if __name__ == "__main__":
    unittest.main()
