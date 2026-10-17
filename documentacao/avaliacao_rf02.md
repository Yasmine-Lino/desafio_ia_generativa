# Avaliação do RF02 — Comparação de prompts

## Objetivo

Comparar três formas de elaborar prompts para gerar uma resposta institucional sobre uma solicitação de manutenção predial.

## Configuração

- Provedor: Gemini
- Modelo: gemini-3.8-flash
- Limite de saída: 1024 tokens
- Nível de raciocínio: low
- Temperatura: padrão do modelo

## Resultados

| Prompt | Fidelidade | Informações inventadas | Tempo total |
|---|---|---|---|
| A — Zero-shot | Parcial | Sim | 9,93 s |
| B — Estruturado | Alta | Não identificadas | 41,70 s |
| C — Metaprompting | Parcial | Sim | 36,57 s |

## Análise

O Prompt A apresentou uma resposta institucional adequada, mas acrescentou uma avaliação técnica e orçamentária que não constava nos dados fornecidos.

O Prompt B apresentou as informações do protocolo, a situação do pedido e indicou o prazo como "Não localizado", sem inventar etapas ou decisões.

O Prompt C produziu uma resposta organizada, mas também acrescentou informações não confirmadas sobre avaliação técnica e canais de acompanhamento. Seu tempo total inclui a geração do prompt.

## Prompt escolhido

Foi escolhido o Prompt B, estruturado manualmente.

Apesar do maior tempo de resposta nesta execução, ele apresentou maior fidelidade aos dados disponíveis. Para atendimento institucional, é importante evitar informações inventadas, especialmente sobre o andamento e os prazos de solicitações.

A comparação foi realizada em uma execução por abordagem. Portanto, os tempos e resultados não representam uma média de desempenho.

## Arquivos do experimento

- Prompts utilizados: pasta `prompts/`
- Respostas e relatório JSON: pasta `resultados/logs/`
- Matriz comparativa: arquivo CSV gerado junto ao relatório.