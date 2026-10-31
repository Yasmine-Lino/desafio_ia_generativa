# Relatorio tecnico - Desafio Pratico 02

## 1. Objetivo

O Desafio 2 continua o projeto Central Inteligente de Atendimento e
Comunicacao Institucional, desenvolvido no Desafio 1.

Nesta etapa, o objetivo foi acrescentar a consulta a documentos
institucionais ficticios, a organizacao das solicitacoes, a busca
de informacoes com fontes e a analise de sentimentos.

O sistema e um prototipo local. As respostas nao sao enviadas
automaticamente e dependem de revisao humana.

## 2. Arquitetura

O projeto foi organizado em modulos Python para separar as etapas:

1. Entrada e validacao das solicitacoes.
2. Extracao estruturada, resumo e classificacao.
3. Aplicacao das regras de seguranca.
4. Leitura e indexacao dos documentos ficticios.
5. Recuperacao dos trechos e resposta fundamentada.
6. Revisao humana pela interface Streamlit.
7. Classificacao de sentimentos e calculo dos indicadores.

A interface principal esta em src/app.py.

## 3. Dados utilizados

Foram criados seis arquivos TXT ficticios para o acervo, divididos
entre os temas matricula e documentacao.

Tambem foram utilizados arquivos JSON com solicitacoes, avaliacoes,
perguntas de teste e gabaritos.

As 12 avaliacoes de atendimento foram divididas em:
tres positivas, tres negativas, tres neutras e tres indeterminadas.

Os dados foram preparados para demonstracao e testes locais.

## 4. Busca e RAG

A indexacao utiliza vetores de hashing lexical com 1024 dimensoes,
armazenados em um indice persistente.

A recuperacao utiliza similaridade de cosseno. O sistema apresenta
trechos do acervo e suas fontes para conferencia.

O RAG utilizado e extrativo: a resposta e baseada no texto
recuperado. Quando nao existe evidencia suficiente, o sistema
deve se abster e encaminhar o caso para revisao.

Foi acrescentada uma regra local de reclassificacao para melhorar
a selecao de fontes em algumas perguntas sobre documentos.

Essa abordagem nao equivale a um modelo de embeddings semanticos
treinado e pode falhar em perguntas com vocabulario diferente.

## 5. Provedor de geracao

O projeto possui um modulo para separar a configuracao do provedor
do restante do fluxo.

A demonstracao validada nesta etapa foi feita principalmente
com processamento local.

No Desafio 2, a OpenAI foi configurada como provedora principal,
com o modelo gpt-4.1-mini. O Gemini foi mantido como alternativa
selecionavel manualmente.

A selecao e a auditoria dos provedores foram verificadas com
testes simulados. A equivalencia de qualidade entre eles nao
foi comprovada, e o fluxo principal continua extrativo.

## 6. Interface Streamlit

A interface foi testada manualmente.

Na aba Documentos e atendimento, foi possivel processar uma
solicitacao ficticia, visualizar a ficha estruturada e consultar
a resposta com fontes.

Na aba Revisao, foi registrada a decisao revisar, acompanhada
de justificativa sobre os campos ausentes da solicitacao.

Na aba Sentimentos, foram visualizadas as classificacoes
e os totais das 12 avaliacoes.

## 7. Resultados dos testes

| Avaliacao | Resultado |
|---|---|
| Testes automatizados (ultima execucao) | 15 de 15 aprovados |
| Recuperacao Top-3 | 5 de 5 (100%) |
| Abstencao correta | 2 de 2 (100%) |
| Sentimentos | 12 de 12 (100%) |
| Consultas manuais do RAG | 5 de 5 esperadas |

Os testes automatizados foram executados com unittest.

As metricas foram calculadas sobre conjuntos pequenos e
preparados para o desafio. Os percentuais nao representam
garantia de desempenho em outros documentos ou solicitacoes.

## 8. Privacidade e revisao humana

O projeto utiliza dados ficticios e nao deve armazenar
credenciais nos arquivos publicados.

As respostas institucionais dependem de avaliacao humana.
O sistema permite registrar a decisao e a justificativa.

A exclusao de documentos do indice, a retencao dos dados
e a limpeza dos resultados derivados precisam ser
verificadas em testes especificos.

## 9. Custos

Os testes locais de busca, regras e classificacao de
sentimentos nao exigiram chamadas pagas a um provedor.

Nao foi medida uma estimativa de custo de geracao remota
para o fluxo completo do Desafio 2.

Por isso, nao foi informado um custo por solicitacao.

## 10. Limitacoes e pendencias

O projeto ainda precisa de uma conferencia completa com
os requisitos RF14 a RF24 e os testes T01 a T15.

Entre os pontos que precisam de comprovacao estao:

- Uso de dois formatos no acervo.
- Comparacao documentada de chunking.
- Ampliacao do tratamento de contradicoes alem de prazos divergentes entre versoes do mesmo documento.
- Execucao dos tres testes adversariais.
- Matriz completa de testes e regressao de audio ou OCR.
- Demonstracao de aprovacao e rejeicao pela interface.
- Integracao dos provedores remotos ao fluxo principal e a interface,
  alem de testes de falhas reais das APIs.
- Exclusao do documento e de seus resultados derivados.
- Medicao de afirmacoes integralmente sustentadas.

Essas pendencias nao devem ser consideradas concluidas
apenas porque os testes locais executados passaram.

## 11. Uso de IA no desenvolvimento

Foi utilizado o ChatGPT como apoio para planejar etapas,
escrever e revisar trechos de codigo, interpretar erros
e organizar a documentacao.

As sugestoes foram aplicadas e ajustadas durante os testes.
Entre os ajustes realizados estiveram a selecao de fontes
do RAG, a revisao dos testes automatizados e a organizacao
do README.

Ainda e necessario completar o registro detalhado exigido
pelo PDF, incluindo pelo menos tres solicitacoes relevantes,
as sugestoes aceitas, modificadas ou rejeitadas e os erros
encontrados durante o desenvolvimento.

## 12. Conclusao

A evolucao do projeto permitiu testar um atendimento
local com busca em documentos, respostas fundamentadas,
revisao humana e analise de sentimentos.

Os resultados foram satisfatorios nos exemplos avaliados,
mas ainda existem verificacoes obrigatorias pendentes.

Antes da entrega final, e necessario conferir as evidencias
e demonstrar os cenarios previstos no enunciado.

## 13. Comparacao de chunking - RF18

Foram testadas duas configuracoes sobre as mesmas cinco perguntas.

| Configuracao | Chunk | Sobreposicao | Top-k | Acertos |
|---|---:|---:|---:|---:|
| 1 | 300 | 50 | 3 | 5/5 |
| 2 | 600 | 100 | 3 | 5/5 |

Foi escolhida a configuracao de 600 caracteres com sobreposicao de 100 caracteres.

As duas configuracoes tiveram 100% de acerto no Top-3 neste conjunto de cinco perguntas. Os resultados de recuperacao foram iguais, portanto nao foi demonstrada vantagem de uma configuracao sobre a outra.

O teste utiliza hashing lexical e um acervo ficticio pequeno. Os resultados nao representam desempenho geral de busca semantica.

Evidencia: resultados/metricas/comparacao_chunking.json

## Validacao complementar - fontes contraditorias (Q08)

Foi realizado um teste com dois documentos ficticios sobre o mesmo prazo de analise:

| Documento | Prazo informado |
|---|---|
| prazo_teste_v1.txt | 5 dias uteis |
| prazo_teste_v2.txt | 10 dias uteis |

O RAG recuperou os dois documentos e identificou os prazos divergentes.
Em vez de escolher uma das informacoes, retornou o status
`conflito de fontes` e indicou a necessidade de revisao humana.

O teste foi incluido em `testes/teste_desafio2.py`, com o nome
`test_fontes_contraditorias`.

Na ultima execucao, os 9 testes automatizados passaram.

**Limitacao:** a verificacao implementada identifica prazos numericos
divergentes em versoes do mesmo documento. Ela nao identifica
automaticamente todos os tipos de contradicao entre fontes.


## Resultado do teste T03

Foram avaliadas seis solicitacoes ficticias (S01 a S06),
comparando os resultados com um gabarito preparado a partir
dos textos originais.

Campos avaliados:
- Categoria principal
- Protocolo
- Data
- Solicitante
- Necessidade de revisao humana

Resultados:
- Solicitacoes aprovadas: 6 de 6
- Campos corretos: 30 de 30
- Concordancia com o gabarito: 100%

O caso S05 foi encaminhado para revisao por falta de dados.
O caso S06 foi encaminhado para revisao por conter demandas
de matricula e segunda via.

O percentual representa apenas os seis exemplos e os cinco
campos avaliados. Nao foram medidas a qualidade dos resumos
nem todas as listas de entidades.

Evidencias:
- dados/solicitacoes/casos.json
- dados/gabaritos/desafio2_solicitacoes.json
- src/avaliar_t03.py
- resultados/metricas/t03_solicitacoes.json

Execucao: python -m src.avaliar_t03

## Resultado do teste T04

Foram testadas tres tentativas de instrucao adversarial
previstas no gabarito do projeto.

Casos avaliados:
- X01: tentativa de ignorar instrucoes e enviar resposta automaticamente.
- X02: tentativa de revelar uma chave por meio de texto do acervo.
- X03: tentativa de revelar a API_KEY do sistema.

Tambem foram testados:
- X04: variacao de ataque sem acentos.
- NORMAL: solicitacao comum, sem tentativa de ataque.

Resultados:
- Identificacao local: 5 de 5 verificacoes corretas.
- Teste X02 com RAG simulado: aprovado.
- Testes automatizados apos as correcoes: 13 de 13 aprovados.

Durante os testes, foram corrigidas as expressoes
regulares de src/guardrails.py para reconhecer textos
com e sem acentos.

No teste do RAG, um trecho adversarial foi retornado
por um indice simulado com similaridade de 0.99.
O sistema descartou esse trecho, nao utilizou fontes
na resposta e informou que nao havia evidencia suficiente.

Esses resultados demonstram o comportamento nos casos
testados, mas nao garantem protecao contra todas as
formas possiveis de ataque adversarial.

Evidencias:
- dados/gabaritos/desafio2_adversariais.json
- src/guardrails.py
- src/rag.py
- testes/teste_desafio2.py

Execucao dos testes:
python -m unittest discover -s testes -p "teste_desafio2.py" -v


## Resultado do teste T12

O teste T12 avaliou a selecao de provedores e o tratamento
de falhas no Desafio 2.

A OpenAI foi configurada como provedora principal, utilizando
o modelo gpt-4.1-mini. O Gemini ficou disponivel como alternativa
selecionada manualmente.

Foram realizadas simulacoes para verificar:
- Se a OpenAI era selecionada por padrao.
- Se o Gemini podia ser selecionado manualmente.
- Se uma falha da OpenAI era identificada.
- Se o sistema evitava trocar de provedor automaticamente.
- Se uma nova tentativa com Gemini podia ser realizada.
- Se os sucessos e as falhas eram registrados na auditoria.
- Se o envio automatico continuava desativado.

Resultados:
- Auditoria de sucesso e falha: 8 de 8 verificacoes corretas.
- Recuperacao controlada com Gemini: 8 de 8 verificacoes corretas.
- Testes automatizados apos a inclusao do T12: 15 de 15 aprovados.

O teste automatizado de recuperacao foi incluido em
`testes/teste_desafio2.py`, com o nome
`test_recuperacao_auditada_t12`.

A auditoria foi implementada em `src/fluxo_desafio2.py`,
na funcao `executar_provedor`, utilizando registros JSONL.

Os testes de recuperacao utilizaram respostas simuladas,
sem chamadas reais as APIs. A integracao dos provedores
ao fluxo principal da interface ainda precisa ser verificada.

O sistema nao faz envio automatico e a revisao humana
continua obrigatoria antes de qualquer uso institucional.

Evidencias:
- config_desafio2.json
- src/openai_client_desafio2.py
- src/provedor_desafio2.py
- src/fluxo_desafio2.py
- testes/teste_desafio2.py

Execucao dos testes:
`python -m unittest discover -s testes -p "teste_desafio2.py" -v`

## 14. Consolidacao final dos testes

Esta secao atualiza os resultados das etapas anteriores.
Os numeros menores registrados nas secoes anteriores representam
execucoes realizadas durante o desenvolvimento.

### Resultados finais conhecidos

| Verificacao | Resultado |
|---|---|
| Testes automatizados com pytest | 144 aprovados |
| Solicitacoes ficticias | 6 processadas |
| T03 - campos avaliados | 30/30 corretos |
| Recuperacao RAG Top-3 | 5/5 |
| Abstencao sem evidencia | 2/2 |
| Sentimentos | 12/12 |
| Entradas adversariais principais | 3 encaminhadas para revisao |
| Revisao humana pela interface | aprovada, rejeitada e revisar |

Os percentuais foram obtidos com dados ficticios e conjuntos pequenos.
Nao representam desempenho garantido em ambiente real.

A solicitacao S06, que mistura matricula e segunda via,
foi reavaliada e passou a exigir revisao humana.

### Matriz de acompanhamento T01 a T15

| Teste | Cenario | Situacao documentada |
|---|---|---|
| T01 | Validacao de esquema e campos invalidos | Testes automatizados |
| T02 | Datas invalidas e informacoes inventadas | Testes automatizados |
| T03 | Seis solicitacoes e gabarito | 30/30 campos corretos |
| T04 | Tres entradas adversariais | Revisao e testes de bloqueio de trechos |
| T05 | Escopo, tamanho e limite de chamadas | Testes locais |
| T06 | Persistencia e reindexacao | Testes locais |
| T07 | Comparacao de chunking | 5/5 nas duas configuracoes |
| T08 | Cinco perguntas com fontes | 5/5 em recuperacao Top-3 |
| T09 | Duas perguntas sem resposta | 2/2 abstencoes |
| T10 | Fontes contraditorias | Teste controlado de prazos divergentes |
| T11 | Interface e revisao humana | Tres decisoes registradas |
| T12 | Troca de provedor e falhas | Testes simulados e auditados |
| T13 | Sentimentos | 12/12 no conjunto ficticio |
| T14 | Exclusao e resultados derivados | Testes automatizados de exclusao |
| T15 | Regressao de texto e audio/OCR | Verificacao automatizada; conferir evidencias |

A matriz resume os testes realizados. A aprovacao automatizada
nao substitui a conferencia das evidencias exigidas pelo enunciado.

### Revisao humana - T11

Foram registradas tres decisoes na interface Streamlit:
- revisar: solicitacao incompleta, com justificativa;
- aprovada: resposta conferida com documento de referencia;
- rejeitada: resposta recusada para teste do fluxo.

Os registros foram gravados em
`resultados/minutas/revisoes_desafio2.jsonl`, contendo
identificador, decisao, justificativa, horario e indicacao
de participacao da IA.

Nao houve envio automatico de resposta.

### Exclusao e privacidade - T14

Foram executados testes automatizados do mecanismo de exclusao
de documentos e limpeza de resultados derivados.

O comportamento demonstrado vale para os cenarios testados.
Nao foi comprovada uma politica completa de retencao
ou eliminacao de todas as copias e backups.

### Limitacoes que permanecem

- O indice utiliza hashing lexical, nao embeddings semanticos treinados.
- A deteccao de contradicoes cobre casos especificos.
- Os testes dos provedores foram simulados, sem demonstracao de
  equivalencia entre APIs reais.
- Nao houve medicao completa de custo remoto por solicitacao.
- A qualidade geral fora do conjunto ficticio nao foi medida.
- A evidencia completa de regressao multimodal e a medicao de
  afirmacoes integralmente sustentadas devem ser conferidas
  antes de declarar atendimento integral ao enunciado.
