import sys,types,unittest
from pathlib import Path
from unittest.mock import Mock
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
# Lightweight doubles for unavailable Chroma/model deps; production modules remain unchanged.
emb=types.ModuleType('src.alternativo_desafio02.embeddings');emb.IndiceVetorial=type('IndiceVetorial',(),{});sys.modules[emb.__name__]=emb
ing=types.ModuleType('src.alternativo_desafio02.ingestion');ing.DIR_ACERVO=Path('.');ing.indexar_acervo=lambda **kw:None;ing.preparar_chunks=lambda **kw:[];sys.modules[ing.__name__]=ing
from src.alternativo_desafio02.rag import responder,StatusResposta,_citacoes_conferem_com_fontes
from src.alternativo_desafio02.nlp import carregar_solicitacao
class Idx:
 def __init__(self,rows):self.rows=rows;self.called=0
 def buscar(self,consulta,top_k=12):self.called+=1;return self.rows
row={'texto':'Documentos para matricula incluem RG e CPF.','similaridade':.95,'distancia':.05,'chunk_id':'DOC01-1','metadados':{'doc_id':'DOC01','titulo':'Documentos','versao':'1','data_publicacao':'01/01/2026','secao':'Matricula'}}
class Fixes(unittest.TestCase):
 def test_no_fake_conflict(self):
  idx=Idx([]);r=responder('Quando comecam aulas de agropecuaria em santa terezinha?',idx);self.assertEqual(idx.called,1);self.assertEqual(r.status,StatusResposta.SEM_EVIDENCIA);self.assertFalse(r.fontes)
 def test_blocked_output(self):
  llm=Mock();llm.completar.return_value='[DOC01] OPENAI_API_KEY=FICTICIA'
  r=responder('Quais documentos para matricula?',Idx([dict(row)]),llm=llm)
  self.assertTrue(r.precisa_revisao);self.assertNotEqual(r.status,StatusResposta.FUNDAMENTADA);self.assertNotIn('FICTICIA',r.resposta or '')
 def test_unknown_source(self):
  llm=Mock();llm.completar.return_value='[DOC99] Documentos para matricula incluem RG e CPF.'
  r=responder('Quais documentos para matricula?',Idx([dict(row)]),llm=llm);self.assertTrue(r.precisa_revisao)
 def test_unsupported_claim(self):
  llm=Mock();llm.completar.return_value='[DOC01] A prefeitura vai distribuir bicicletas gratuitas.'
  r=responder('Quais documentos para matricula?',Idx([dict(row)]),llm=llm);self.assertTrue(r.precisa_revisao)
 def test_supported_claim(self):
  llm=Mock();llm.completar.return_value='[DOC01] Documentos para matricula incluem RG e CPF.'
  r=responder('Quais documentos para matricula?',Idx([dict(row)]),llm=llm);self.assertEqual(r.status,StatusResposta.FUNDAMENTADA)
 def test_traversal(self):
  for x in ('../../segredo','sol01/../../segredo','sol01\\..\\segredo','/tmp/segredo'):
   with self.subTest(x=x),self.assertRaises(ValueError):carregar_solicitacao(x)
 def test_valid_case(self):
  self.assertIn('solicit',carregar_solicitacao('sol01').lower())
if __name__=='__main__':unittest.main(verbosity=2)
