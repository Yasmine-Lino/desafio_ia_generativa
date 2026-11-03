# Central Inteligente de Atendimento — Desafios Práticos 1 e 2

Projeto do **Módulo 01 — IA Generativa**, curso FIC Dev IA.

**Equipe:** Adriano Froes da Costa ([GitHub](https://github.com/AdrianoFroes)), Líbia Canhete Alves e Cruz ([GitHub](https://github.com/libia-alves)) e Yasmine Lino Franco ([GitHub](https://github.com/Yasmine-Lino)).

## 1. Sobre o projeto

Este repositório reúne as atividades dos **Desafios Práticos 1 e 2**. O primeiro desafio trabalhou funcionalidades de IA generativa para documentos, textos, áudio, imagens, geração de minutas e revisão humana (RF01–RF13). O **Desafio 2 (RF14–RF24)** amplia a central com processamento de solicitações, indexação de documentos, busca, RAG, avaliação de sentimentos, auditoria e interface Streamlit.

É um **protótipo educacional**, com documentos e solicitações fictícios. As respostas são sugestões para revisão: **não há envio automático ao cidadão**.

## 2. O que foi desenvolvido no Desafio 2

| Componente | O que faz | Arquivo principal |
|---|---|---|
| Estruturação e validação | Extrai informações e valida os dados da solicitação | `src/schemas.py`, `src/nlp.py` |
| Segurança | Avalia entradas e instruções suspeitas | `src/guardrails.py` |
| Documentos | Lê, divide e prepara o acervo | `src/ingestion.py` |
| Índice e busca | Mantém índice persistente e recupera trechos | `src/embeddings.py` |
| RAG | Responde com base nos trechos recuperados ou se abstém | `src/rag.py` |
| Atendimento e revisão | Processa solicitações e registra decisão humana | `src/fluxo_desafio2.py` |
| Interface | Apresenta documentos, atendimento, revisão e sentimentos | `src/app.py` |
| Sentimentos | Classifica avaliações fictícias | `src/sentiment.py` |
| Avaliação offline | Executa casos e calcula métricas | `src/avaliar_desafio2.py` |
| Sustentação textual | Verifica correspondência entre afirmações e trechos citados | `avaliar_sustentacao_rf23.py` |

**Limitação importante:** o índice local utiliza *hashing lexical* e similaridade, e não embeddings semânticos de um modelo treinado. O RAG é predominantemente extrativo.

## 3. Requisitos e materiais de avaliação

Os requisitos do Desafio 2 são tratados nas áreas RF14–RF24: estruturação e validação, processamento de solicitações, segurança, indexação, comparação de chunking, RAG, interface, provedores/auditoria, sentimentos, avaliação integrada e privacidade/revisão. A relação detalhada de cada requisito e dos testes **T01–T15** está em:

- `documentacao/MATRIZ_RF23_T01_T15_ATUALIZADA.md` — matriz de avaliação;
- `documentacao/matriz_conformidade_pdf.md` — relação com o enunciado;
- `documentacao/RELATORIO_TECNICO_FINAL_ENTREGA.md` — relatório técnico consolidado;
- `documentacao/registro_uso_ia.md` — registro de uso de IA como apoio ao desenvolvimento;
- `documentacao/evidencias/` — capturas de revisão humana e exclusão documental.

Esses arquivos são complementares ao código e aos resultados. A existência de um teste não deve ser confundida com uma demonstração manual, nem com uma chamada real à API.

## 4. Organização do repositório

```text
src/                     Código da aplicação e das avaliações
testes/                  Testes automatizados
dados/acervo/            Documentos fictícios usados no RAG
dados/solicitacoes/      Solicitações fictícias
dados/avaliacoes/        Avaliações de sentimentos
dados/gabaritos/         Referências e resultados esperados
indice/                  Índices persistentes e comparações
resultados/metricas/     Métricas e avaliações em JSON
resultados/logs/         Auditoria e exclusões
resultados/minutas/      Minutas e decisões de revisão
documentacao/            Relatórios, matrizes e evidências
config.json              Configuração geral
.env.example             Modelo de variáveis de ambiente
requirements.txt         Dependências Python
```

## 5. Instalação no Windows

Ambiente utilizado nos testes: **Windows com Python 3.12**. Git e acesso à internet são necessários para obter o projeto e instalar dependências. No PowerShell:

```powershell
git clone https://github.com/Yasmine-Lino/desafio_ia_generativa.git
cd desafio_ia_generativa
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Se a ativação estiver bloqueada, use ` .\.venv\Scripts\python.exe ` diretamente para executar os comandos Python. As instruções para outros sistemas não foram validadas nesta entrega.

### APIs externas (opcionais)

O fluxo local e os testes offline não exigem credenciais reais. Para funcionalidades que utilizem provedores externos, copie `.env.example` para `.env` e configure apenas as chaves necessárias, conforme os componentes utilizados. O projeto possui integrações e experimentos com Gemini, OpenAI e outros provedores no Desafio 1.


## 6. Executar a interface do Desafio 2

Com o ambiente ativado, na raiz do projeto:

```powershell
python -m streamlit run src/app.py
```

Abra `http://localhost:8501`.

1. Em **Documentos e atendimento**, confira os documentos do acervo, indexe quando necessário e processe uma solicitação fictícia.
2. Confira a resposta preliminar, o estado da consulta e os documentos citados como fontes.
3. Em **Revisão**, selecione `aprovada`, `rejeitada` ou `revisar`, informe uma justificativa e registre a decisão. Uma solicitação sem evidência suficiente não deve ser aprovada.
4. Em **Sentimentos**, consulte a classificação das avaliações fictícias.

O índice usado na interface fica em `indice/acervo.json`. Se precisar reconstruí-lo, use a indexação da própria interface. Isso pode modificar o estado do índice e afetar uma demonstração de exclusão anterior.

### Exemplo de solicitação

```text
Protocolo: 2026/001
Data: 02/11/2026
Solicitante: Maria Silva
Assunto: Quais são os documentos necessários para realizar uma matrícula?
Descrição: Solicito orientação sobre matrícula.
```

O campo `Assunto:` é priorizado como pergunta para o RAG, evitando misturar o protocolo e outros dados administrativos com a busca documental.

## 7. Executar os testes e avaliações

Na raiz do projeto, com o ambiente virtual ativado:

```powershell
# Suíte principal
python -m unittest discover -s testes -p "teste*.py" -v

# Avaliação offline: RAG, abstenção, sentimentos e conflito
python -m src.avaliar_desafio2

# Avaliação adicional de sustentação textual
python avaliar_sustentacao_rf23.py
```

Os resultados ficam em `resultados/metricas/desafio2_offline.json` e `resultados/metricas/rf23_sustentacao.json`. A avaliação offline pode criar ou atualizar índices de avaliação na pasta `indice/`.

## 8. Resultados verificados na execução final de 02/11/2026

| Avaliação | Resultado | Observação |
|---|---:|---|
| Suíte principal de testes | **149/149 aprovados** | `unittest`, 4,262 s |
| Recuperação Top-3 | **5/5 (100%)** | Referência esperada entre os documentos recuperados |
| Abstenção sem evidência | **2/2 (100%)** | Não inventar resposta quando falta evidência |
| Sentimentos offline | **12/12 (100%)** | Comparação com gabarito local |
| Distribuição de sentimentos | 3 positivas, 3 negativas, 3 neutras, 3 indeterminadas | 3 casos sinalizados para revisão |
| Conflito Q08 | **Detectado** | Fontes divergentes exigem revisão |
| Sustentação **textual por afirmação** | **14/20 (70%)** | Correspondência normalizada com trechos citados |

**Como interpretar:** 70% é a taxa de **afirmações** com correspondência textual confirmada, não a proporção de **respostas** com todas as afirmações sustentadas. Essa última métrica, no formato estrito do RF23, ainda precisa de avaliação própria. Ausência de correspondência literal não prova falsidade da afirmação. Os 100% são resultados do conjunto pequeno de avaliação **offline**, não estimativas de desempenho em produção.

A tentativa de avaliação das 12 classificações por **Gemini real** não produziu respostas válidas devido a erros de serviço/cota/tempo (HTTP 429, HTTP 503 e timeout). **Não há acurácia real de Gemini calculável nesse experimento**. Os 12/12 referem-se exclusivamente ao classificador local.

Os resultados históricos de outras suítes e da implementação alternativa estão nos relatórios de `documentacao/`; não devem ser somados aos 149 testes da suíte principal.

## 9. Revisão humana, exclusão e evidências

As decisões `aprovada`, `rejeitada` e `revisar` foram registradas no arquivo `resultados/minutas/revisoes_desafio2.jsonl`, com justificativa e identificação da execução. As capturas manuais estão em:

- `documentacao/evidencias/T11_aprovacao.png`
- `documentacao/evidencias/T11_rejeicao.png`
- `documentacao/evidencias/T11_revisao.png`

Foi registrada a remoção de `documentacao_04_v1.txt` do índice, **preservando o documento original**. O registro fica em `resultados/logs/exclusoes_desafio2.jsonl`. A ausência no índice persistente foi conferida e há capturas em:

- `documentacao/evidencias/T14_exclusao.png`
- `documentacao/evidencias/T14_ausencia_indice.png`
- `documentacao/evidencias/T14_ausencia_busca.png`

A captura de busca demonstra ausência naquela consulta; a verificação do índice é a evidência adicional de remoção persistente. A reindexação posterior pode restaurar o documento no índice.

## 10. Provedores, custos e auditoria

O Desafio 1 inclui experimentos com modelos externos e geração de materiais. O Desafio 2 foi avaliado principalmente pelo fluxo local, além de testes de integração e simulações de erros de provedores. **Testes simulados não comprovam disponibilidade nem qualidade de uma API real.**

A avaliação offline não gera consumo de tokens de API. Em execuções anteriores do Desafio 1 houve registro de tempo e tokens quando disponíveis, mas não foi consolidado um custo financeiro verificável para toda a solução. Consulte `documentacao/relatorio_tecnico_final.md` e o relatório consolidado de entrega.

Os logs registram eventos de processamento, decisões humanas e exclusão. Não há envio automático de respostas institucionais.

## 11. Privacidade, segurança e limitações

- Utilizar apenas dados fictícios ou devidamente autorizados e observar a LGPD.
- Não incluir credenciais, arquivos `.env`, ambientes virtuais ou dados sensíveis no pacote.
- Manter a revisão humana obrigatória para respostas e materiais institucionais.
- Tratar respostas sem evidência e documentos contraditórios como casos de revisão.
- Reconhecer limitações da recuperação lexical, dos conjuntos pequenos de teste e das APIs externas.
- O resultado de sustentação textual não equivale a verificação factual completa.
- O protótipo não está validado para operação real em órgão público.

## 12. Documentação final e uso de IA

A documentação do projeto está organizada para facilitar a conferência dos requisitos do desafio. Os principais arquivos são a **matriz de testes T01–T15**, disponível em `documentacao/MATRIZ_RF23_T01_T15_ATUALIZADA.md`, e o **relatório técnico final**, em `documentacao/RELATORIO_TECNICO_FINAL_ENTREGA.md`.

Os gabaritos, resultados das avaliações, registros de execução e capturas de tela estão organizados nas respectivas pastas do projeto.

O arquivo `documentacao/registro_uso_ia.md` apresenta como ferramentas de inteligência artificial foram utilizadas durante o desenvolvimento, incluindo apoio na análise dos requisitos, identificação de problemas, sugestões de melhorias, testes e documentação. As alterações e os resultados foram conferidos durante a execução do projeto.

---

**Curso:** FIC Dev IA — Módulo 01: IA Generativa.  
**Escopo:** protótipo acadêmico desenvolvido com dados fictícios, com resultados, evidências e limitações documentados.
