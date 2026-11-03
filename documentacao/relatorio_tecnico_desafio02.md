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

## 6. Atualizacao de evidencias em 02/11/2026

A equipe informou a aprovacao de 100 testes da suite alternativa no Windows,
10 testes especificos de auditoria RF21 e a regressao T15 com 1 teste e 2
subtestes aprovados. A compilacao de `avaliar_sentimentos_real.py` tambem foi
verificada. Esses resultados nao substituem as demonstracoes manuais previstas
na matriz T01–T15.

A tentativa real de classificacao de sentimentos pelo Gemini nao foi concluida:
12 tentativas terminaram em HTTP 503, HTTP 429 ou timeout, sem classificacoes
validas. A acuracia real e nao calculavel (0/0). Foi identificada divergencia
de identificadores: a entrada usa A01–A12 e o gabarito alternativo antigo usa
aval01–aval12, alem de apontar para arquivos TXT ausentes. O script foi
atualizado para usar `dados/gabaritos/desafio2_sentimentos.json`, validar os
IDs e representar acuracia sem amostras como nula. Nao foi feita nova chamada
real apos essa correcao.

Permanecem pendentes: demonstracao manual de T11 e T14; medicao da proporcao
de respostas RAG com todas as afirmacoes sustentadas; consolidacao de RF23 com
numeradores e denominadores; e publicacao confirmada na branch `main`.


## 7. Atualização final — 02/11/2026

Na execução Windows informada pela equipe, a suíte integrada apresentou **292 testes aprovados, nenhuma falha, 36 avisos de depreciação e 2 subtestes aprovados**. Também foram informados 18 testes focados em segurança/unificação e 6 testes específicos de prompt injection aprovados. A correção final adiciona validação dos textos gerados por provedor externo antes de retorná-los ao fluxo.

No RF22, a execução real com Gemini não produziu classificação válida: foram 12 tentativas com erros HTTP 503, HTTP 429 ou timeout. A acurácia real é não calculável (0/0). Os testes com mocks não foram contabilizados como execução real. O conjunto A01–A12 deve ser comparado somente com o gabarito de mesmos identificadores.

A comparação de chunking reportada teve Top-3 = 5/5 para 300/50 e 600/100. A abstenção reportada foi 2/2 nas perguntas sem evidência; o caso contraditório foi tratado separadamente. O índice é baseado em hashing lexical e cosseno, não em embedding semântico treinado. A métrica de respostas com todas as afirmações sustentadas permanece pendente.

A interface existe, mas as capturas preliminares não comprovam por si só consulta completa com fontes, aprovação/rejeição persistidas ou exclusão seguida de ausência na busca. T11 e T14 permanecem parciais até demonstração manual. O commit `06a8c62` foi enviado para `origin/main`, com sincronização confirmada em 02/11/2026.
