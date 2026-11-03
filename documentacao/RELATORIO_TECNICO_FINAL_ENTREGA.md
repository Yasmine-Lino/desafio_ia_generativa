# Relat?rio t?cnico final ? Desafio Pr?tico 02

## 1. Objetivo

Neste desafio, demos continuidade ? Central Inteligente de Atendimento desenvolvida no Desafio 01. O objetivo foi integrar extra??o estruturada, classifica??o de solicita??es, busca de documentos, RAG, revis?o humana e an?lise de sentimentos.

O prot?tipo ? executado localmente e utiliza documentos e solicita??es fict?cias. Nenhuma resposta institucional ? enviada automaticamente.

## 2. Arquitetura e funcionamento

O projeto foi desenvolvido em Python, com interface Streamlit. As principais partes s?o:

- `src/app.py`: interface de atendimento, revis?o e sentimentos.
- `src/nlp.py` e `src/schemas.py`: compreens?o e valida??o dos dados.
- `src/guardrails.py`: verifica??es de seguran?a.
- `src/embeddings.py`: indexa??o e recupera??o de documentos.
- `src/rag.py`: elabora??o de respostas fundamentadas no acervo.
- `src/fluxo_desafio2.py`: integra??o do processamento e da revis?o.
- `src/sentiment.py`: classifica??o de sentimentos.
- `src/avaliar_desafio2.py`: avalia??o offline.
- `avaliar_sustentacao_rf23.py`: verifica??o de sustenta??o textual.

O fluxo recebe a solicita??o, extrai as informa??es, consulta o acervo, apresenta a minuta e suas fontes e aguarda a decis?o humana.

## 3. Provedores e configura??o

O projeto possui componentes para utiliza??o de provedores externos, incluindo Gemini e OpenAI, al?m de processamento offline/local.

A avalia??o final apresentada neste relat?rio foi realizada offline. Os testes com respostas simuladas n?o devem ser confundidos com execu??es reais de APIs.

O ?ndice utilizado na avalia??o local possui recupera??o por hashing lexical. Essa abordagem permite executar testes reproduz?veis sem depender de uma API externa, mas n?o equivale a um modelo sem?ntico de embeddings.

## 4. Testes e m?tricas

Na execu??o final, foram realizados 149 testes automatizados, todos aprovados.

| Avalia??o | Resultado |
|---|---|
| Testes automatizados | 149/149 |
| Recupera??o Top-3 | 5/5 ? 100% |
| Absten??o sem evid?ncia | 2/2 ? 100% |
| Sentimentos offline | 12/12 ? 100% |
| Conflito Q08 | Detectado |
| Sustenta??o textual por afirma??o | 14/20 ? 70% |

A avalia??o de sentimentos incluiu tr?s avalia??es positivas, tr?s negativas, tr?s neutras e tr?s indeterminadas.

A sustenta??o textual foi calculada comparando as afirma??es extra?das das respostas com os trechos documentais citados. Das 20 afirma??es avaliadas, 14 tiveram correspond?ncia textual confirmada.

Essa m?trica n?o comprova equival?ncia sem?ntica nem garante que todas as afirma??es estejam factualmente corretas. A propor??o de respostas com todas as afirma??es sustentadas, exigida separadamente pelo RF23, n?o foi medida por esse indicador.

Os resultados detalhados est?o em `resultados/metricas/desafio2_offline.json` e `resultados/metricas/rf23_sustentacao.json`.

## 5. Revis?o humana e auditoria

A interface permite registrar decis?es de aprova??o, rejei??o e encaminhamento para revis?o, com justificativa e identifica??o da execu??o.

Durante a demonstra??o, foram registrados os tr?s tipos de decis?o. As evid?ncias est?o na pasta `documentacao/evidencias`.

O sistema tamb?m registrou a exclus?o de `documentacao_04_v1.txt` do ?ndice, preservando o documento original. A aus?ncia no ?ndice persistente foi verificada posteriormente.

## 6. Privacidade e seguran?a

Foram utilizados dados fict?cios no contexto do desafio. O projeto possui testes de valida??o, prote??o contra instru??es maliciosas, tratamento de falhas e revis?o humana.

As credenciais n?o devem ser inclu?das no pacote de entrega. Arquivos `.env`, ambientes virtuais e segredos precisam permanecer fora do ZIP.

A revis?o humana ? obrigat?ria antes da aprova??o institucional, e o envio autom?tico permanece desativado.

## 7. Custos e recursos

As avalia??es finais offline n?o utilizaram chamadas pagas de gera??o para cada teste, portanto n?o h? custo de tokens de API a atribuir a essa execu??o.

Os testes automatizados foram conclu?dos em aproximadamente 4,262 segundos na execu??o registrada. Esse tempo n?o representa a lat?ncia de uma chamada real a um provedor externo.

Custos de execu??es anteriores com APIs s? devem ser informados quando houver registros verific?veis de uso e pre?os aplic?veis.

## 8. Limita??es

- O desempenho offline n?o representa a qualidade de APIs externas.
- A recupera??o por hashing lexical possui limita??es sem?nticas.
- A sustenta??o textual de 70% n?o equivale ? valida??o factual completa.
- Algumas respostas dependem da qualidade e da cobertura do acervo.
- Fontes contradit?rias e informa??es insuficientes exigem revis?o humana.
- As m?tricas foram obtidas com conjuntos pequenos de dados fict?cios.

## 9. Uso de intelig?ncia artificial no desenvolvimento

Foram utilizadas ferramentas de IA como apoio para analisar requisitos, discutir alternativas, revisar trechos de c?digo, interpretar erros, orientar testes e auxiliar na documenta??o.

As sugest?es foram avaliadas durante o desenvolvimento, com ajustes e verifica??es por meio da execu??o do projeto, testes automatizados e confer?ncia dos resultados.

O uso de IA n?o substituiu a necessidade de testar o funcionamento, interpretar as m?tricas e assumir responsabilidade pelas decis?es e pelo material entregue.

O registro complementar est? em `documentacao/registro_uso_ia.md`.

## 10. Conclus?o

O Desafio 02 integrou os principais componentes de atendimento, recupera??o documental, RAG, sentimentos e revis?o humana. Os 149 testes automatizados foram aprovados.

A avalia??o identificou resultados satisfat?rios nos casos offline de recupera??o, absten??o e sentimentos, al?m de limita??es na sustenta??o textual. Essas limita??es foram mantidas no relat?rio para apresentar os resultados sem ocultar falhas.
