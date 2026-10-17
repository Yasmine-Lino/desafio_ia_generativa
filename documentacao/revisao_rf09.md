# RF09 — Geração de Minuta Institucional

## Objetivo

Gerar uma minuta institucional a partir de uma solicitação fictícia, utilizando informações disponíveis e exigindo revisão humana antes de qualquer utilização oficial.

## Implementação

Arquivo principal: src/minuta.py

Prompt: prompts/rf09_minuta_institucional.txt

Integração com IA: src/llm_client.py

Modelo utilizado: gemini-3.8-flash.

## Fontes utilizadas

- dados/originais/entrada_texto.txt
- dados/processados/rf05_extracao.json

O contexto enviado ao modelo foi limitado aos campos necessários à elaboração da resposta.

Dados pessoais desnecessários, como CPF, RG e data de nascimento, não foram incluídos no contexto enviado para gerar a minuta.

## Resultado da geração

Tempo de execução: 3,38 segundos.

Tokens totais: 836.

Arquivo original: resultados/minutas/rf09_minuta.txt

Arquivo revisado: resultados/minutas/rf09_minuta_revisada.txt

Metadados: resultados/minutas/rf09_informacoes.json

## Avaliação da minuta

A resposta apresentou linguagem formal e respeitosa.

Foram identificados corretamente o assunto, o protocolo e a data.

O modelo não afirmou que a matrícula estava efetivada.

Não foi inventada uma relação de documentos pendentes.

As fontes utilizadas foram indicadas.

A minuta permaneceu identificada como rascunho não enviado.

## Revisão humana

Situação: aprovada com ajuste.

Data registrada: 16/10/2026 às 23h51, horário -04:00.

A revisão humana substituiu uma frase que poderia sugerir compromisso de resposta futura por uma redação condicionada à verificação pelo setor responsável.

A versão original gerada pela IA foi preservada para comparação.

## Pendências institucionais

- Confirmar a situação da matrícula.
- Verificar a existência de documentos pendentes.
- Identificar o setor responsável pela resposta.

A aprovação humana da redação não representa a confirmação administrativa dessas informações.

## Controle de envio

Revisão humana realizada: sim.

Minuta aprovada: sim, com ajuste.

Envio automático: desativado.

Resposta enviada ao cidadão: não.

## Conclusão

O RF09 produziu uma minuta institucional baseada nos dados disponíveis, sem inventar decisões ou documentos.

A versão revisada foi aprovada por conferência humana e permanece como rascunho, aguardando eventual utilização institucional autorizada.
