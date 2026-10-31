# Relatorio Tecnico - Desafio 02

## 1. Integracao

O projeto principal foi preservado e recebeu uma implementacao alternativa
organizada em `src/alternativo_desafio02/`, com testes separados em
`testes_alternativos_desafio02/`.

Foram integrados modulos de validacao de dados, NLP, guardrails, ingestao,
embeddings, RAG, sentimentos, privacidade e auditoria.

## 2. Resultados dos testes

Em 31/10/2026, no Windows com Python 3.12, foi executado:

`python -m pytest testes testes_alternativos_desafio02 -q --tb=short`

Resultado: **250 testes aprovados, nenhuma falha e 1 aviso**.

Resultados especificos verificados durante a integracao:

- RF16: 19 testes aprovados.
- RF19: 4 testes aprovados.
- RF21: 9 testes aprovados.
- RF24: 6 testes aprovados.

No diagnostico do RF19, foram indexados 44 chunks.
O RAG respondeu corretamente a 4 de 5 perguntas respondiveis
e se absteve corretamente nas 2 perguntas sem resposta.

## 3. Arquitetura e seguranca

A implementacao alternativa utiliza embeddings locais e indice ChromaDB.
O RF19 passou a preparar o acervo quando encontra um indice vazio.

A auditoria alternativa registra eventos em JSONL e mascara os padroes
de CPF e chaves de API cobertos pelos testes.

Os testes do RF24 verificaram a exclusao de chunks do indice
e o registro de decisoes de revisao humana.

O documento adversarial do acervo e utilizado para testes de seguranca
e nao deve ser incluido na indexacao normal.

## 4. Limitacoes conhecidas

- O provedor mock funciona nos testes, mas o adaptador Gemini alternativo
  ainda nao executa chamadas reais a API.
- O caso de contradicao Q08 utiliza uma regra especifica com fontes
  simuladas; nao comprova deteccao generica de contradicoes.
- Uma das cinco perguntas respondiveis do RF19 ficou sem evidencia suficiente.
- Os arquivos `teste_rf20.py` e `teste_rf23.py` estao vazios.
  Portanto, nao ha cobertura automatizada propria demonstrada para eles.
- O mascaramento de dados atende aos padroes testados, mas nao substitui
  uma solucao completa de protecao de dados pessoais.

## 5. Conclusao

A integracao foi validada pela execucao conjunta de 250 testes,
sem falhas nessa execucao.

Os resultados demonstram o funcionamento das partes cobertas pelos testes,
mas nao comprovam implementacao integral de todos os requisitos do desafio.
