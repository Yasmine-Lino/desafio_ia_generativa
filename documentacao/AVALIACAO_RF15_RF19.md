# Avaliação complementar — RF15 e RF19

**Projeto:** Central Inteligente de Atendimento — Desafio Prático 02  
**Ambiente de referência:** execução offline em Windows, Python 3.12.10, branch `integracao`  
**Natureza:** conferência dos casos fictícios e das saídas fornecidas durante a auditoria. Não é uma medição de desempenho em produção.

## 1. Objetivo e fontes de evidência

Este registro complementa a matriz RF23 e documenta a conferência de extração, classificação, resumo e fundamentação de respostas. Foram usados:

- `dados/solicitacoes/casos.json` — entradas S01 a S06;
- `dados/gabaritos/desafio2_solicitacoes.json` — categorias, campos e indicação de revisão esperados;
- `dados/gabaritos/desafio2_perguntas.json` — perguntas Q01 a Q08 e fontes de referência;
- `dados/acervo/*.txt` — documentos institucionais fictícios;
- Saída de `python -m src.avaliar_desafio2` compartilhada após execução no Windows;
- Saídas de `src.rag.responder` para Q01 a Q05, incluindo texto da resposta e metadados dos trechos, compartilhadas na auditoria.

As respostas Q01 a Q05 foram comparadas manualmente aos trechos efetivamente exibidos. Não houve execução de API externa para esta conferência.

## 2. RF15 — classificação, entidades e resumos

| Caso | Categoria esperada/obtida | Revisão esperada/obtida | Entidades relevantes | Resultado do resumo |
|---|---|---|---|---|
| S01 | `matricula` / `matricula` | não / não | MAT-0001; 10/10/2026; Ana Exemplo | Reproduz as informações do pedido |
| S02 | `documentacao` / `documentacao` | não / não | DOC-0002; 11/10/2026; Bruno Fictício | Reproduz as informações do pedido |
| S03 | `matricula` / `matricula` | não / não | MAT-0003; 12/10/2026; Carla Teste | Reproduz as informações do pedido |
| S04 | `documentacao` / `documentacao` | não / não | DOC-0004; 13/10/2026; Davi Exemplo | Reproduz as informações do pedido |
| S05 | `matricula` / `matricula` | sim / sim | Protocolo, data e solicitante ausentes | Mantém as ausências, sem inventar valores |
| S06 | `matricula` / `matricula` | sim / sim | MAT-0006; 14/10/2026; Eva Exemplo | Preserva os dois assuntos; requer revisão |

**Indicadores na amostra:**

| Métrica | Numerador | Denominador | Resultado |
|---|---:|---:|---:|
| Categorias iguais ao gabarito | 6 | 6 | 100% |
| Indicação de revisão igual ao gabarito | 6 | 6 | 100% |
| Protocolos presentes corretamente extraídos | 5 | 5 | 100% |
| Datas presentes corretamente extraídas | 5 | 5 | 100% |
| Solicitantes presentes corretamente extraídos | 5 | 5 | 100% |
| Resumos sem acréscimos factuais identificados na conferência | 6 | 6 | 100% |
| Resumos dentro do limite de 100 palavras | 6 | 6 | 100% |

**Observações:** S05 não tem protocolo, data nem solicitante; a ausência é esperada e não entra no denominador de campos presentes. S06 mistura matrícula e segunda via; a categoria principal coincide com o gabarito, mas a revisão é necessária. A análise dos resumos é manual e limitada aos seis exemplos; não constitui uma avaliação independente de cobertura semântica em outros documentos.

## 3. RF19 — respostas e sustentação documental

As cinco respostas respondíveis foram exibidas com seus trechos recuperados. Em todos os casos, a resposta final reproduziu o texto do documento de referência, sem acrescentar afirmações institucionais não presentes no trecho.

| Caso | Pergunta resumida | Documento que sustenta a resposta | Trecho identificado | Auditoria |
|---|---|---|---|---|
| Q01 | O que apresentar para matrícula? | `matricula_01_v1.txt` | `p1:t0`, versão 1, página 1 | Integralmente sustentada |
| Q02 | O que informar no pedido? | `matricula_02_v1.txt` | `p1:t0`, versão 1, página 1 | Integralmente sustentada |
| Q03 | Existe prazo garantido para vagas? | `matricula_03_v1.txt` | `p1:t0`, versão 1, página 1 | Integralmente sustentada |
| Q04 | O que é necessário para segunda via? | `documentacao_04_v1.txt` | `p1:t0`, versão 1, página 1 | Integralmente sustentada |
| Q05 | Pode apresentar comprovante digital? | `documentacao_05_v1.txt` | `p1:t0`, versão 1, página 1 | Integralmente sustentada |

**Conferência de conteúdo:**

- **Q01:** apresentar comprovante de inscrição; o atendimento confirma a documentação antes da decisão.
- **Q02:** informar protocolo e data; dados incompletos são encaminhados para revisão humana.
- **Q03:** consultar a unidade; o documento não garante prazo para vagas.
- **Q04:** identificar o documento e informar o protocolo de atendimento.
- **Q05:** comprovante digital legível é aceito; dados ausentes exigem conferência.

**Indicadores na amostra:**

| Métrica | Numerador | Denominador | Resultado |
|---|---:|---:|---:|
| Fonte esperada recuperada no Top-3 (Q01–Q05) | 5 | 5 | 100% |
| Respostas com todas as afirmações institucionais sustentadas (Q01–Q05) | 5 | 5 | 100% |
| Abstenções corretas (Q06–Q07) | 2 | 2 | 100% |
| Conflito de versões identificado (Q08) | 1 | 1 | 100% |

**Nota metodológica:** o indicador de sustentação é **por resposta**, não por frase: cada uma das cinco respostas só foi contada como correta porque todas as suas afirmações institucionais estavam no trecho de referência exibido. Q06 e Q07 não integram o denominador de respostas fundamentadas, pois são casos de abstenção. Q08 é avaliada separadamente como conflito.

## 4. Observações técnicas e limites

1. **Recuperação não é fundamentação.** Uma fonte aparecer no Top-3 não garante que a resposta a utilize corretamente; por isso a conferência examinou o texto efetivamente produzido.
2. **Q04:** `documentacao_04_v1.txt` apareceu em terceiro na recuperação, com similaridade `0.13608`, abaixo de documentos de matrícula; apesar disso, foi a fonte usada na resposta final. A ordenação lexical merece acompanhamento, sem justificar alteração imediata do algoritmo.
3. **Modo extrativo:** as cinco respostas reproduziram os trechos dos documentos fictícios. Esse comportamento favorece a rastreabilidade nesta amostra, mas não garante desempenho em textos mais extensos ou ambíguos.
4. **Conflito Q08:** as versões de prazo não estabelecem precedência entre si; o resultado registrado foi `conflito de fontes`, sem escolher arbitrariamente um prazo.
5. **Resultados offline:** a avaliação registrou Top-3 `5/5`, abstenção `2/2`, sentimentos `12/12` e conflito Q08 identificado. O último indicador pertence a RF19; sentimentos são contexto da avaliação geral, não uma métrica de RF15/RF19.
6. **Limites:** os percentuais se aplicam somente aos exemplos fictícios examinados. Não houve avaliação de generalização, testes com cidadãos reais nem validação de aprovação humana neste registro.

## 5. Conclusão

Nos casos examinados, **RF15 e RF19 atenderam aos critérios conferidos**: classificação e revisão conforme gabarito, campos presentes extraídos corretamente, resumos sem acréscimos factuais identificados e respostas Q01–Q05 integralmente apoiadas pelos documentos indicados. As abstenções e o conflito também foram tratados conforme os casos de teste. A conclusão não equivale à aprovação integral de todos os requisitos do Desafio 2.

## 6. Reprodutibilidade e controle de alterações

A execução `python -m src.avaliar_desafio2` pode regravar `resultados/metricas/desafio2_offline.json` e gerar índices `indice/avaliacao_400.json` e `indice/avaliacao_800.json`. Esses arquivos não precisam ser incluídos em novo commit apenas para registrar esta auditoria. Este documento registra as saídas já conferidas; nenhuma mudança de código é necessária para adicioná-lo.
