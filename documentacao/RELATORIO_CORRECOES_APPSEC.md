# Correções AppSec — branch integracao (pacote entregue)

## Escopo e método

Foi inspecionado o pacote ZIP recebido, incluindo estrutura de 241 arquivos, 96 arquivos Python (~12 mil linhas), módulos principal e alternativo, testes, dados, gabaritos, configuração e documentação. Alterações limitadas aos pontos confirmados no relatório anterior. **Não foram usadas credenciais ou chamadas a provedores externos.**

## Observações anteriores, na ordem

| ID | Situação | Arquivo | Evidência / ressalva |
|---|---|---|---|
| S01 — Fontes fabricadas | Corrigido | `src/alternativo_desafio02/rag.py` | Removida a condição Q08 que gerava DOC01/DOC03 artificiais. Perguntas passam pela busca real. A qualidade da detecção de conflitos ainda depende dos resultados recuperados. |
| S02 — Saída bloqueada tratada como fundamentada | Corrigido | `src/alternativo_desafio02/rag.py` | Decisões BLOQUEAR ou REVISAR retornam SEM_EVIDENCIA, resposta `None`, revisão obrigatória; nenhum segredo detectado é apresentado. |
| S03 — Path traversal em solicitação | Corrigido | `src/alternativo_desafio02/nlp.py` | IDs limitados a `sol` + dois dígitos; caminho resolvido e validado dentro da pasta de solicitações. |
| S04 — Citações verificadas apenas por formato | Mitigado | `src/alternativo_desafio02/rag.py` | Cada frase exige referência `[DOCxx]` presente na busca e sobreposição lexical mínima com trecho daquele documento. Isso **não prova suporte semântico**; paráfrases válidas podem ser encaminhadas à revisão e falsidades com palavras comuns ainda podem passar. Para garantia forte, é necessária revisão humana ou verificador semântico dedicado. |
| SQL/NoSQL, comandos, LDAP, XPath, template injection | Sem alteração | — | Auditoria anterior não confirmou ponto explorável; não se inventaram correções. |
| Autenticação e implantação | Pendente de contexto | Interface e infraestrutura | Protótipo local previsto no PDF; implantação pública exigiria controles adicionais. |
| Dependências/CVEs | Não verificado dinamicamente | `requirements.txt` | Não houve resolução transitiva nem consulta a base de CVEs; nenhuma vulnerabilidade específica pode ser afirmada. |

## Conformidade RF14–RF24

A correção de segurança contribui principalmente para RF16 e RF19. **Não transforma automaticamente os requisitos classificados como parciais em atendidos.** Mantêm-se as ressalvas da matriz anterior: RF14, RF15, RF16, RF19, RF20, RF21, RF23 e RF24 necessitam evidências integradas e/ou execução funcional adicional; RF17, RF18 e RF22 possuem evidências de implementação, mas não foram revalidados dinamicamente neste ambiente. A matriz T01–T15 não foi reexecutada por completo com dependências externas.

## Validação

- Compilação sintática de `src/`: OK.
- Testes específicos de correção (sem rede e com substitutos para Chroma/embeddings): **7/7 OK**; script `python documentacao/validar_correcoes_appsec.py`.
- Suíte principal: **140 testes tentados; 3 erros de ambiente**, sem evidência de falha causada por estas alterações. O ambiente não possui `chromadb`, `sentence_transformers` e chave de API para teste de cliente; houve também erro de importação/patch em um teste. Portanto **não** foi possível repetir os 145/145 testes do Windows relatados anteriormente.
- Testes do módulo alternativo com modelo vetorial real e Streamlit não executados neste ambiente.

## Conflitos resolvidos

1. O caso Q08 precisava continuar detectando conflito, mas fontes artificiais eram incompatíveis com rastreabilidade: a detecção foi mantida somente sobre resultados reais do índice.
2. Uma resposta com dado bloqueado poderia ser saneada e continuar como fundamentada: foi adotado o comportamento mais seguro, abstendo e exigindo revisão.
3. O guardrail aceitava o formato da citação, mas não possuía o contexto de recuperação: a validação contextual foi adicionada no RAG, sem alterar a API pública de `validar_saida`.

## Recomendações ainda abertas

Executar a suíte completa no ambiente original com dependências instaladas, revisar manualmente a sustentação semântica das afirmações e completar a matriz de conformidade e demonstração funcional. Não executar `git push` automaticamente: o pacote é uma cópia corrigida, não um commit no repositório remoto.
