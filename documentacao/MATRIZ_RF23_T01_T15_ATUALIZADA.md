# Matriz de evidências RF23 — T01 a T15

**Projeto:** Central Inteligente de Atendimento — Desafio Prático 02
**Referência:** enunciado oficial, seção 11, páginas 10–11.
**Base da auditoria:** ZIP `desafio_ia_generativa-integracao(3).zip` e execuções Windows compartilhadas pela equipe.
**Regra de avaliação:** "parcial" não significa falha de código; indica que ainda não foi apresentada evidência suficiente de todos os passos exigidos. Resultados históricos não foram reexecutados nesta atualização.

| ID | Entrada / cenário | Resultado esperado | Resultado obtido ou evidência disponível | Evidência | Situação |
|---|---|---|---|---|---|
| T01 | JSON com tipo incorreto e campo ausente | Rejeitar esquema inválido e impedir minuta | Existem validadores e testes de esquema; bloqueio até a minuta não demonstrado nesta coleta | `src/schemas.py`; `testes/teste_desafio2.py` | Parcial |
| T02 | Data impossível ou dado ausente do original | Bloquear incoerência e solicitar revisão | Regras e testes locais disponíveis; falta registrar caso completo esperado × obtido | `src/schemas.py`; testes de validação | Parcial |
| T03 | Seis solicitações S01–S06 | Resumo fiel, categoria e entidades confrontados com gabarito | Avaliação histórica: 6/6 casos e 30/30 campos selecionados; resumo e todas as entidades não foram integralmente medidos | `resultados/metricas/t03_solicitacoes.json`; `dados/gabaritos/desafio2_solicitacoes.json` | Parcial |
| T04 | Três ataques X01–X03 | Não executar instruções nem revelar segredos | Testes locais de bloqueio e revisão documentados; falta matriz por ataque com saída final | `dados/gabaritos/desafio2_adversariais.json`; `src/guardrails.py`; `documentacao/RELATORIO_DESAFIO2.md` | Parcial |
| T05 | Fora de escopo, arquivo excessivo e limite de chamadas | Bloqueio/revisão e limites respeitados | Código e testes de limites; faltam saídas reunidas dos três cenários | `src/guardrails.py`; `src/limite_chamadas_desafio2.py` | Parcial |
| T06 | Reinício e reindexação do mesmo acervo | Reutilizar índice sem duplicar trechos | Testes locais disponíveis; falta registrar contagens e persistência em uma evidência reproduzível | `src/embeddings.py`; testes do índice | Parcial |
| T07 | Duas configurações e cinco perguntas | Comparar top-k e calcular acerto | Histórico: chunks 300/50 e 600/100; Top-3 = 5/5 em ambas | `resultados/metricas/comparacao_chunking.json` | Evidência histórica disponível |
| T08 | Cinco perguntas respondíveis | Respostas e citações verificadas contra fontes | Recuperação Top-3 histórica = 5/5; isso não mede sustentação de todas as afirmações | `resultados/metricas/desafio2_offline.json`; `src/rag.py` | Parcial |
| T09 | Duas perguntas sem evidência | Abster-se e encaminhar à revisão | Abstenção histórica = 2/2; encaminhamento completo requer conferência do fluxo | `resultados/metricas/desafio2_offline.json` | Parcial |
| T10 | Fontes contraditórias | Aplicar prioridade ou sinalizar conflito e revisão | Q08: conflito identificado; teste de duas versões de prazo disponível | `testes/teste_ajustes_conformidade_desafio2.py`; `dados/acervo/prazo_matricula_v1.txt`; `dados/acervo/prazo_matricula_v2.txt` | Evidência de conflito disponível; revisão a conferir |
| T11 | Aprovar e rejeitar pela interface | Persistir estados e justificativas, sem envio automático | Registros de decisões documentados; comprovação prática na interface deve ser preservada | `src/app.py`; `resultados/minutas/revisoes_desafio2.jsonl` | Parcial |
| T12 | Troca de provedor e falha | Preservar índice, tratar e auditar falha | Testes com provedores simulados; falta evidência consolidada do índice antes/depois | `src/provedor_desafio2.py`; `src/fluxo_desafio2.py`; `testes/teste_desafio2.py` | Parcial |
| T13 | Filtro, duplicata e conjunto vazio | Totais e denominadores corretos, sem divisão por zero | Métricas e testes existem; resultados dos três subcasos não reunidos | `src/metrics.py`; testes de métricas | Parcial |
| T14 | Excluir documento e derivados | Trechos ausentes da busca e exclusão auditada | Testes automatizados de exclusão disponíveis; falta anexar execução e registro completo | `src/exclusao_desafio2.py`; `testes/teste_desafio2_exclusao.py` | Parcial |
| T15 | Reexecutar entrada textual e OCR anteriores | Entradas seguem até minuta e revisão | **Windows: 1 teste e 2 subtestes aprovados (texto e OCR)**; extração, RAG, status, revisão simulada e auditoria verificados. Não demonstra aprovação humana real nem qualidade integral da minuta | `testes/teste_t15_regressao_integrada.py` (novo arquivo local); saída pytest informada pela equipe | Regressão automatizada aprovada; aceite integral pendente de demonstração |

## Execução recente — T15 e regressão conjunta

Ambiente informado: Windows, Python 3.12.10, pytest 9.1.1.

```powershell
.\.venv\Scripts\python.exe -m pytest testes/teste_rf05.py testes/teste_rf08.py testes/teste_conformidade_final.py testes/teste_t15_regressao_integrada.py -v --tb=short
```

**Resultado observado:** `12 passed, 2 subtests passed in 2.14s`. O teste T15 isolado também passou: `1 passed, 2 subtests passed in 2.52s`.

**O que T15 efetivamente testa:** leitura das entradas anteriores, indexação temporária do acervo TXT, chamada de `executar`, presença de resumo e pedido, status e resposta RAG, bloqueio de envio automático, chamada de `revisar(..., "revisar", ...)` e IDs coerentes nos logs. A decisão de revisão é **simulada pelo teste**, não tomada por operador real na interface.

## Métricas e limitações que não devem ser confundidas

- **T03:** 30/30 refere-se a cinco campos escolhidos em seis solicitações; não representa acurácia geral de todas as entidades ou fatos essenciais.
- **T07:** 5/5 refere-se à recuperação Top-3 nas cinco perguntas para cada configuração, não à correção de toda resposta.
- **T08:** a proporção de respostas institucionais com **todas** as afirmações sustentadas ainda precisa ser medida, com numerador e denominador, conforme RF23.
- **T09:** 2/2 é a taxa de abstenção do conjunto fictício avaliado.
- **T15:** o PDF não exige gerar novos arquivos de áudio/OCR, mas exige reexecutar casos anteriores até minuta e revisão.

## Pendências prioritárias para o fechamento

1. Demonstrar T15 e T11 pela interface com minuta verificável e decisão humana real, preservando evidência sem dados sensíveis.
2. Registrar saídas específicas de T01–T06 e T12–T14, com entrada, esperado, obtido e log.
3. Medir sustentação integral das afirmações em T08/RF23 e completar avaliação de resumos e entidades em T03/RF15.
4. Conferir README, relatório e matriz para não declarar cobertura integral quando a evidência é parcial.

**Nota:** esta matriz é um documento de auditoria, não um registro fabricado de testes. A existência de um arquivo de teste ou de uma função não foi tratada como aprovação do cenário completo.


## Atualização de execução — 02/11/2026 (Windows)

- Suíte integrada executada com `python -m pytest testes testes_alternativos_desafio02 -q --tb=short`: **292 passed, 36 warnings, 2 subtests passed**. Os avisos são de depreciação do Pandas/Streamlit.
- Testes focados de segurança/unificação: **18 passed**. Testes específicos de prompt injection: **6 passed**.
- O fluxo externo passou a validar a resposta gerada com os guardrails antes de devolvê-la. Resposta vazia ou bloqueada resulta em encaminhamento para revisão.
- RF22 real: **0 classificações válidas/12 tentativas**; HTTP 503, HTTP 429 e timeout. Acurácia real **não calculável (0/0)**.
- T11 e T14 continuam **parciais** até capturas e registros de execução manual que comprovem decisões pela interface e exclusão seguida de ausência na busca. As capturas preliminares disponíveis mostram a interface, mas não comprovam esses resultados.
- RF23: manter separados os indicadores medidos (por exemplo, recuperação Top-3 5/5 e abstenção 2/2) da métrica de afirmações integralmente sustentadas, ainda pendente.
- Commit `06a8c62` publicado na branch `main`; push confirmado em 02/11/2026.
