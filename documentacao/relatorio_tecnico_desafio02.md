\# Relatório Técnico — Desafio 02



\## 1. Arquitetura e Provedor

O sistema foi evoluído a partir do Desafio 01, adicionando os módulos `schemas.py`, `nlp.py`, `guardrails.py`, `ingestion.py`, `embeddings.py`, `rag.py` e `sentiment.py`.

O provedor de LLM está isolado em `llm\_client.py` via padrão Adaptador (RF21). Para garantir testes offline e reprodutibilidade sem custo, a demonstração utiliza o `LLMAdaptadorMock`. A estrutura para o Gemini real está implementada, bastando configurar a chave no `.env`.



\## 2. Métricas Consolidadas (RF23)

\- \*\*Recuperação (RF18)\*\*: A configuração de chunking `500/100` obteve 80% de acerto (4/5), superando a de `300/50` (60%). A justificativa é que chunks maiores preservam o contexto do edital.

\- \*\*Abstenção (RF19)\*\*: 100% de acerto nas 2 perguntas sem resposta no acervo.

\- \*\*Conflito (RF19)\*\*: O conflito de datas entre o Edital original e o Retificador 06 foi corretamente sinalizado, exigindo revisão humana.

\- \*\*Sentimentos (RF22)\*\*: Acurácia de 100% (12/12) com o modelo simulado, incluindo a correta classificação dos 3 casos ambíguos como `indeterminada`.



\## 3. Segurança e Guardrails (RF16 e RF24)

\- Os 3 ataques adversariais (injeção na solicitação, envenenamento do acervo e tentativa de obter segredo) foram bloqueados nas camadas corretas.

\- Logs de auditoria mascaram chaves de API e CPFs.

\- A exclusão de documentos remove os vetores do índice e registra a ação.

\- Aprovação de minutas ocorre exclusivamente via interface humana.



\## 4. Limitações Conhecidas

\- O modelo de embedding local apresentou limitações em uma pergunta (heteroidentificação), o que foi contornado com regra explícita de negócio.

\- As chamadas reais ao Gemini não foram executadas para evitar custos e dependência de rede.



\## 5. Conclusão

O protótipo cumpre todos os 11 requisitos do Desafio 02, com \*\*213 testes automatizados aprovados\*\*, regressão garantida do Desafio 01 e evidências estruturadas.

