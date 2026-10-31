# Unificação — Integração e Desafio 02

## Base preservada
`desafio_ia_generativa-integracao.zip` é a base. Os arquivos `src/app.py`, `src/rag.py`, `src/embeddings.py`, `src/schemas.py` e `src/guardrails.py` originais não foram sobrescritos.

## Incorporado do segundo ZIP
- `src/alternativo_desafio02/`: implementações alternativas de embeddings, ingestão, RAG, esquemas Pydantic, guardrails, NLP, sentimentos, métricas e revisão humana. **Arquivos de referência; imports internos `src.*` ainda precisam ser adaptados para uso integrado**.
- `dados/desafio02_alternativo/`: acervo e gabaritos isolados. Não incluir documento adversarial no índice de produção.
- `testes_alternativos_desafio02/`: testes RF14–RF24 originais para adaptação; **não fazem parte da suíte principal**.
- `requirements.txt`: dependências opcionais do backend semântico.

## Componentes integrados e testáveis
- `src/backends/indices.py`: seleção explícita lexical/semântico, com caminhos de índices separados.
- `src/backends/contratos.py`: adaptadores de respostas; não migra automaticamente solicitações antigas.
- `src/backends/matriz_evidencias.py`: matriz T01–T15 com estado não verificado por padrão.
- `testes/teste_unificacao_desafio02.py`: testes dos adaptadores e da matriz.

## Limitações e pendências reais
1. O fluxo Streamlit existente permanece inalterado; seleção de backend na interface ainda não foi integrada.
2. A implementação semântica depende de download de modelo e instalação de bibliotecas; não foi validada com execução real nem com índices persistentes.
3. Os contratos Pydantic da alternativa ainda não foram migrados para o fluxo atual.
4. Os testes alternativos precisam ser adaptados para a nova interface; não contam como aprovados.
5. Não há migração de históricos de revisão, nem sincronização de exclusão entre índices; não habilitar o backend semântico em produção sem esses controles.
6. Não foi realizada chamada real a APIs externas.
7. Os arquivos `src/alternativo_desafio02/` usam imports absolutos do projeto original, e portanto não são módulos de substituição direta.

## Execução
```powershell
python -m pip install -r requirements.txt
python -m pytest testes -q
# opcional, para desenvolver a integração semântica:
python -m pip install -r requirements.txt
```

## Próximas etapas
1. Adaptar imports e testar Chroma com dados isolados.
2. Unificar contratos e categorias com validação de dados históricos.
3. Integrar RAG e guardrails, testar conflito e abstenção.
4. Integrar interface, persistência e exclusão completa.
5. Migrar testes RF14–RF24, produzir matriz real T01–T15.
6. Revisar privacidade e publicar somente após regressão.

## Segunda etapa — recuperacao padronizada
- `src/backends/indices.py` agora fornece `buscar_trechos`, normalizando identificador, texto, documento e metadados.
- O campo `tipo_pontuacao` distingue cosseno lexical de distancia Chroma. **Nao usar limiar unico para os dois.**
- `src/alternativo_desafio02/embeddings.py` verifica dimensao do modelo e `resetar()` respeita o nome real da colecao.
- Testes com indices simulados validam o contrato sem baixar modelos nem instalar ChromaDB.
- **Nao foi validada indexacao semantica real**, nem foram integrados UI, migracao de contratos, exclusao em ambos os indices ou RF14-RF24.
