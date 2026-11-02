# Avaliação do RF19 — Implementação alternativa

## 1. Objetivo

Registrar os resultados dos testes do RAG da implementação alternativa do Desafio Prático 2, incluindo recuperação de informações, abstenção e identificação de conflitos entre documentos.

## 2. Resultados da avaliação

Foram avaliadas oito perguntas, divididas em três categorias.

| Categoria | Resultado | Taxa |
|---|---:|---:|
| Perguntas respondíveis | 4/5 | 80% |
| Perguntas sem resposta | 2/2 | 100% |
| Pergunta com fontes contraditórias | 1/1 | 100% |

## 3. Análise dos resultados

### T08 — Perguntas respondíveis

Das cinco perguntas que deveriam ter resposta no acervo, quatro foram respondidas com evidências suficientes.

A pergunta Q03, sobre o procedimento de heteroidentificação da cota L1, ainda não encontrou evidências suficientes.

### T09 — Abstenção

As duas perguntas sem resposta no acervo foram identificadas corretamente.

O sistema não apresentou uma resposta sem sustentação documental e encaminhou os casos para revisão.

### T10 — Conflito entre fontes

A pergunta Q08 apresentou divergência entre o edital original e o Edital Retificador 06.

- Edital original (DOC01): início das aulas em 21/07/2026.
- Retificador 06 (DOC03): alteração para 05/10/2026.
- Publicação do retificador: 03/08/2026.

O sistema identificou a divergência, apresentou as fontes e sinalizou a necessidade de revisão humana.

## 4. Testes automatizados

O arquivo `testes_alternativos_desafio02/teste_rf19.py` foi executado com quatro testes aprovados.

Também foi realizada uma execução integrada dos seguintes arquivos:

- teste_rf19.py
- teste_t15_regressao_integrada.py
- teste_desafio2_exclusao.py
- teste_desafio2.py
- teste_conformidade_final.py

Resultado:

- 27 testes aprovados.
- 2 subtestes aprovados.
- Nenhuma falha.
- 1 aviso de depreciação da biblioteca de embeddings.

## 5. Conclusão

A implementação alternativa apresentou resultados positivos na identificação de respostas, abstenções e conflitos entre documentos.

A taxa de acerto nas perguntas respondíveis foi de 80%. A pergunta Q03 permanece como ponto de melhoria, pois o sistema ainda não conseguiu recuperar evidências suficientes.

Os testes automatizados executados foram aprovados, mas isso não representa aprovação integral de todos os requisitos do Desafio Prático 2.
