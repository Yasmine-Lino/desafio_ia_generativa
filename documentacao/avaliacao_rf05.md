\# Avaliação do RF05 — Extração de informações



\## Objetivo



Extrair informações de uma solicitação recebida por texto e organizar os dados em formato JSON.



\## Implementação



Foi criado o arquivo `src/extracao.py`, utilizando o cliente Gemini desenvolvido no RF04.



O programa lê o arquivo `entrada\_texto.txt`, identifica informações básicas e utiliza a IA para interpretar o assunto, o pedido e a categoria.



Antes da consulta à API, alguns dados pessoais são ocultados para reduzir a exposição de informações desnecessárias.



O resultado mantém o texto original para conferência e indica os campos que não foram encontrados.



\## Testes realizados



Foram realizados cinco testes automáticos, verificando:



\- Extração de protocolo e data.

\- Identificação de campos ausentes.

\- Tratamento de categoria inválida.

\- Proteção básica de dados pessoais.

\- Geração de JSON válido.



Todos os cinco testes passaram.



Também foi realizada uma consulta real ao Gemini utilizando o arquivo de entrada do projeto.



\## Resultado da extração



O programa identificou o protocolo `2026-000142` e a data `14/10/2026`.



O assunto foi relacionado à efetivação de matrícula e à documentação pendente.



O pedido foi identificado como a solicitação de matrícula no curso Técnico em Enfermagem e a pergunta sobre quais documentos ainda precisam ser apresentados.



A categoria atribuída foi `matrícula`, com confiança `alta`.



Como o texto não informa quais documentos estão pendentes, o programa registrou `não localizado`.



O arquivo gerado foi validado como JSON.



\## Cuidados e limitações



A proteção de dados pessoais implementada é básica e ainda precisa ser melhorada para utilização em situações reais.



A confiança é atribuída pelo modelo e não representa uma medida estatística de precisão.



O JSON gerado contém o texto original e, por isso, deve permanecer armazenado localmente, sem publicação no GitHub.



A revisão humana continua obrigatória.



\## Conclusão



O RF05 funcionou nos testes realizados.



O programa conseguiu organizar as informações principais da solicitação, identificar um campo ausente e gerar um JSON válido.



A implementação poderá ser aproveitada nas próximas etapas do projeto.



\## Arquivos



\- Código: `src/extracao.py`

\- Testes: `testes/teste\_rf05.py`

\- Entrada: `dados/originais/entrada\_texto.txt`

\- Resultado local: `dados/processados/rf05\_extracao.json`

