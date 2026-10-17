\# Avaliação do RF04 — Integração com API de modelo de linguagem



\## Objetivo



Implementar um cliente para consultar um modelo de linguagem por API, permitindo configurar as mensagens, controlar o tempo de execução, tratar erros e consultar informações sobre o consumo de tokens.



\## Implementação



Foi criado o arquivo `src/llm\_client.py`, utilizando o provedor Gemini e o modelo `gemini-3.8-flash`, definido no `config.json`.



O cliente permite enviar mensagens com diferentes papéis, incluindo instruções de sistema e mensagens do usuário.



A chave de acesso é carregada do arquivo `.env`, sem ser exibida nos resultados.



Também foram implementados tratamentos para chave ausente, autenticação inválida, limite de requisições, indisponibilidade do serviço, tempo limite e respostas vazias.



\## Testes automáticos



Foram realizados seis testes com respostas simuladas da API:



1\. Chave de acesso ausente.

2\. Autenticação inválida.

3\. Limite de requisições atingido.

4\. Serviço indisponível.

5\. Resposta vazia.

6\. Resposta válida com informações de tokens.



\*\*Resultado:\*\* os seis testes passaram.



\## Teste de integração real



Foi realizada uma consulta ao modelo Gemini com uma pergunta sobre protocolo de atendimento.



Resultados:



\- Modelo: `gemini-3.8-flash`

\- Tempo de resposta: 5,76 segundos

\- Tokens de entrada: 37

\- Tokens de saída: 41

\- Tokens totais: 448

\- Resposta recebida: sim



O número total de tokens foi informado diretamente pela API e pode incluir tokens internos de raciocínio.



O custo estimado não foi calculado porque os preços por token ainda não foram configurados no projeto.



\## Limitações



A implementação atual utiliza somente o provedor Gemini.



O cliente permite configurar o modelo, o limite de tokens e o tempo de espera. A temperatura está registrada no `config.json`, mas não é enviada na chamada atual.



A estimativa financeira depende de uma tabela de preços confirmada.



A integração também não substitui a revisão humana das respostas destinadas aos cidadãos.



\## Conclusão



A integração com a API funcionou no teste real, e os seis testes automáticos foram aprovados.



O cliente pode ser reutilizado nos próximos requisitos do projeto, reduzindo a repetição de código.



\## Arquivos



\- Cliente de API: `src/llm\_client.py`

\- Testes: `testes/teste\_rf04.py`

\- Configuração: `config.json`

