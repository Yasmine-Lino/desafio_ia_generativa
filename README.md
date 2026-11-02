# Desafios Práticos 1 e 2 — IA Generativa

Projeto desenvolvido no **Módulo 01 — IA Generativa**, do curso FIC Dev IA.

## Integrantes da Equipe

- **Adriano Froes da Costa** - [GitHub: AdrianoFroes](https://github.com/AdrianoFroes)
- **Líbia Canhete Alves e Cruz** - [GitHub: libia-alves](https://github.com/libia-alves)
- **Yasmine Lino Franco** - [GitHub: Yasmine-Lino](https://github.com/Yasmine-Lino)

------------------------------------------------------------------------


## 1. Sobre o projeto

Este repositório contém uma **Central Inteligente de Atendimento e Comunicação Institucional**, desenvolvida para simular atividades de uma secretaria pública.

O projeto utiliza técnicas de inteligência artificial generativa para apoiar o tratamento de solicitações de cidadãos, incluindo processamento de textos, áudios, documentos e imagens, além da elaboração de materiais institucionais.

Os **13 requisitos funcionais (RF01 a RF13)** foram implementados, com testes automatizados, registros de execução e documentação.

**Atenção:** os conteúdos gerados por inteligência artificial são sugestões e precisam passar por revisão humana antes de qualquer utilização institucional. O sistema não realiza envio automático de respostas aos cidadãos.

## 2. Tecnologias e pré-requisitos

- Python 3.12
- Git
- Acesso à internet para instalação das dependências
- Bibliotecas Python definidas em `requirements.txt`
- Credenciais de serviços externos de IA, apenas quando necessárias

Dependências principais:

```text
openai==3.33.0
python-dotenv==1.2.4
requests==2.34.2
pymupdf==1.28.2
pytest==9.1.1
```

O projeto utiliza integrações com serviços como Gemini, Groq e Hugging Face, conforme a funcionalidade executada.

A inicialização básica e os testes automatizados não exigem credenciais reais.

## 3. Organização do projeto

| Diretório ou arquivo | Descrição |
|---|---|
| `src/` | Código-fonte Python |
| `testes/` | Testes automatizados |
| `dados/` | Dados de entrada, exemplos e arquivos processados |
| `prompts/` | Prompts utilizados nos experimentos |
| `resultados/` | Resultados, minutas, imagens, áudios e logs |
| `documentacao/` | Documentação técnica e registros de revisão |
| `config.json` | Configurações gerais do sistema |
| `.env.example` | Exemplo das variáveis de ambiente |
| `requirements.txt` | Dependências Python |

Alguns arquivos de entrada e saída podem ser gerados durante a execução e não estar versionados no Git.

## 4. Instalação e execução

As instruções abaixo contemplam Windows, Linux e macOS.

Antes de começar, instale o **Git** e o **Python 3.12** no sistema operacional utilizado.

### 4.1. Windows — PowerShell

**Passo 1 — Clonar o repositório**

```powershell
git clone https://github.com/Yasmine-Lino/desafio_ia_generativa.git
cd desafio_ia_generativa
```

**Passo 2 — Criar o ambiente virtual**

```powershell
py -3.12 -m venv .venv
```

**Passo 3 — Ativar o ambiente virtual**

```powershell
.\.venv\Scripts\Activate.ps1
```

**Passo 4 — Instalar as dependências**

```powershell
python -m pip install -r requirements.txt
```

**Passo 5 — Executar a inicialização do projeto**

```powershell
python -m src.main
```

Caso o PowerShell bloqueie a ativação do ambiente virtual, é possível executar diretamente o Python desse ambiente:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.main
```

### 4.2. Linux — Terminal

**Passo 1 — Clonar o repositório**

```bash
git clone https://github.com/Yasmine-Lino/desafio_ia_generativa.git
cd desafio_ia_generativa
```

**Passo 2 — Criar o ambiente virtual**

```bash
python3.12 -m venv .venv
```

**Passo 3 — Ativar o ambiente virtual**

```bash
source .venv/bin/activate
```

**Passo 4 — Instalar as dependências**

```bash
python -m pip install -r requirements.txt
```

**Passo 5 — Executar a inicialização**

```bash
python -m src.main
```

**Observação:** dependendo da distribuição Linux, pode ser necessário instalar separadamente o suporte a ambientes virtuais (`venv`) para Python 3.12.

### 4.3. macOS — Terminal

**Passo 1 — Clonar o repositório**

```bash
git clone https://github.com/Yasmine-Lino/desafio_ia_generativa.git
cd desafio_ia_generativa
```

**Passo 2 — Criar o ambiente virtual**

```bash
python3.12 -m venv .venv
```

**Passo 3 — Ativar o ambiente virtual**

```bash
source .venv/bin/activate
```

**Passo 4 — Instalar as dependências**

```bash
python -m pip install -r requirements.txt
```

**Passo 5 — Executar a inicialização**

```bash
python -m src.main
```

**Observação:** o Python 3.12 precisa estar instalado e disponível no terminal. Dependendo da instalação do macOS, pode ser necessário instalar essa versão separadamente.

## 5. Configuração das APIs

O arquivo `.env.example` apresenta as variáveis de ambiente previstas:

```dotenv
GEMINI_API_KEY=
OPENAI_API_KEY=
GROQ_API_KEY=
HF_TOKEN=
```

Para utilizar funcionalidades que dependem dessas APIs, crie uma cópia chamada `.env`.

**Windows — PowerShell**

```powershell
Copy-Item .env.example .env
```

**Linux e macOS**

```bash
cp .env.example .env
```

Abra o arquivo `.env` e preencha as credenciais correspondentes aos serviços que pretende utilizar. Na configuração local atual, são utilizadas `GEMINI_API_KEY` e `OPENAI_API_KEY`; `GROQ_API_KEY` e `HF_TOKEN` permanecem no `.env.example` para funcionalidades que utilizem esses provedores.

**Cuidados de segurança:**

- Nunca publique chaves de API no GitHub.
- Não inclua credenciais diretamente no código-fonte.
- Não compartilhe o conteúdo do arquivo `.env`.
- Verifique as permissões, os limites de uso e as cotas disponíveis de cada provedor.

As configurações gerais do sistema estão no arquivo `config.json`.

## 6. Execução dos testes automatizados

Com o ambiente virtual ativado, execute:

```bash
python -m unittest discover -s testes -p "teste_*.py"
```

O comando é o mesmo para Windows, Linux e macOS.

Na última execução realizada durante o desenvolvimento, o projeto apresentou:

```text
Ran 139 tests

OK
```

Os testes incluem simulações de erros e situações excepcionais. Por isso, algumas mensagens de falha podem aparecer durante a execução sem indicar problemas no resultado final.

Os testes foram desenvolvidos para validar os comportamentos sem necessidade de realizar chamadas reais às APIs externas.

## 7. Requisitos funcionais e evidências

O projeto contempla os requisitos **RF01 a RF13**, com implementações em `src/`, testes em `testes/` e registros complementares em `documentacao/` e `resultados/`.

Entre as evidências disponíveis estão:

- **RF03 — Testes de segurança contra instruções maliciosas:** `documentacao/avaliacao_rf03.md` e `resultados/logs/rf03_injecao.json`.
- **RF09 — Elaboração e revisão de minuta institucional:** `documentacao/revisao_rf09.md` e arquivos em `resultados/minutas/`.
- **RF12 — Privacidade e minimização de dados:** `src/privacidade.py`, `testes/teste_rf12.py` e `documentacao/revisao_rf12.md`.
- **RF13 — Avaliação de qualidade e revisão humana:** `src/avaliacao_qualidade.py`, `src/executar_avaliacao_rf13.py`, `testes/teste_rf13.py`, `documentacao/revisao_rf13.md` e `resultados/logs/rf13_avaliacao.json`.

### Avaliação de qualidade — RF13

A avaliação considera cinco critérios:

1. Fidelidade
2. Completude
3. Formato
4. Linguagem
5. Segurança

Foram avaliados dois casos independentes, com os seguintes resultados:

| Caso | Pontuação | Resultado |
|---|---|---|
| RF03 — Injeção de prompt | 10/10 | Aprovado |
| RF09 — Minuta original | 8/10 | Correção manual necessária |

A **taxa de aprovação inicial foi de 50%**.

A minuta do RF09 foi corrigida e aprovada posteriormente por revisão humana. Essa correção não foi contabilizada como um novo caso.

### Modelos e custos

| Atividade | Modelo ou ferramenta |
|---|---|
| Comparação de prompts (RF02), extração (RF05), OCR (RF08) e minuta (RF09) | Gemini 3.8 Flash (`gemini-3.8-flash`, definido em `config.json`) |
| Transcrição de áudio (RF06) | Gemini 3.5 Transcribe |
| Síntese de voz (RF07) | Gemini 2.5 Flash Preview TTS |
| Geração e revisão de imagem (RF10) | Ferramenta de imagens do ChatGPT |

A imagem foi gerada pela interface do ChatGPT porque a tentativa com o Gemini 2.5 Flash Image retornou HTTP 429 (sem cota gratuita disponível).

**Custos:** as execuções usaram a cota gratuita da API Gemini. O projeto registra tempo e tokens de cada chamada quando o provedor informa. Exemplos: minuta RF09 com 836 tokens em 3,38 s e OCR RF08 com 2.273 tokens em 60,79 s. Não foi possível consolidar um custo financeiro confiável, pois os preços por modelo e modalidade não foram configurados nem confirmados. O custo real depende do volume de solicitações, da modalidade e das condições comerciais do provedor. Antes de uma implantação, seria necessário definir limites de consumo e monitoramento financeiro. Detalhes em `documentacao/relatorio_tecnico_final.md` (seções 3 e 10).

## 8. Limitações e cuidados

Este projeto é um **protótipo educacional**, não um sistema de produção de uma secretaria pública.

As principais limitações e precauções são:

- Modelos de IA podem produzir informações incorretas, incompletas ou não confirmadas.
- Serviços externos podem apresentar indisponibilidade, limites de uso ou ausência de créditos.
- Os resultados devem ser verificados por uma pessoa responsável.
- Dados pessoais e informações sigilosas exigem tratamento adequado, observando as exigências aplicáveis da LGPD.
- A geração de materiais não representa autorização para publicação ou envio automático.
- A execução foi testada no ambiente de desenvolvimento Windows. As instruções para Linux e macOS foram incluídas para facilitar a portabilidade, mas ainda não foram validadas nesses sistemas.

## 9. Situação do desenvolvimento

Os requisitos **RF01 a RF13 foram implementados e publicados no repositório**.

A suíte automatizada apresentou **139 testes aprovados** na última execução.

As evidências, limitações e revisões estão registradas na documentação do projeto.

## 10. Curso

**FIC Dev IA — Módulo 01: IA Generativa.**


## Demonstração offline e identidade visual (complemento da entrega)

As minutas `.txt` permanecem inalteradas como evidências de geração e revisão.
As versões de **apresentação** em PDF incluem `dados/originais/brasao.png`,
identificação de documento fictício e aviso de que não são comunicações oficiais.
O brasão é usado apenas para demonstração acadêmica; não indica aprovação do GOV.MT.

```bash
python -m src.gerar_minuta_pdf --versao ambas
python -m src.demonstracao
python -m src.demonstracao --registrar
python -m pytest -q
```

A demonstração é **offline**: verifica a presença dos artefatos já produzidos,
não chama modelos, não recria respostas e não simula inferências. A opção
`--registrar` cria um log JSONL verdadeiro **da própria conferência offline**,
sem afirmar que as chamadas históricas à API foram reexecutadas.
O comando `python -m src.main` continua sendo o ponto de entrada de
inicialização/configuração, e não um pipeline automático de produção.

O áudio definitivo RF07 foi gerado a partir de `resultados/minutas/rf09_minuta_revisada.txt`, está salvo em `resultados/audios/rf07_minuta_rf09_aprovada.wav` e foi aprovado por escuta humana em 17/10/2026. O ensaio `rf07_minuta_falada.wav` foi preservado separadamente. O hash do texto usado na síntese é conferido pelo verificador.

**Pacote de entrega:** `.env.example` deve ser incluído; `.env` verdadeiro,
`.venv`, caches e credenciais não devem ser incluídos. Os arquivos fictícios
originais e os gabaritos locais são evidências necessárias para a avaliação.


## Complemento de conformidade RF06, RF07, RF08 e RF11

- **RF06:** a nova transcrição `dados/processados/rf06_nova_transcricao_20261017_160731.txt` foi comparada à referência confirmada por escuta humana do áudio original e aprovada em 17/10/2026. A referência foi derivada de transcrição anterior, portanto a limitação de independência histórica permanece explicitada; não se afirma que ela existia antes da primeira inferência.
- **RF07:** o áudio definitivo da minuta revisada foi gerado, conferido por escuta e aprovado. A aprovação e o hash da minuta são mantidos nos metadados de revisão e de geração. O campo `revisao_audio_pendente` nos metadados de geração representa o estado no instante em que a síntese terminou e foi preservado sem adulteração.
- **RF08:** os seis campos críticos do gabarito (`codigo_matricula`, `data_nascimento`, `cpf`, `rg`, `data_matricula` e `inicio_curso`) foram confirmados visualmente no PDF original antes da nova extração. O texto bruto foi preservado; a versão corrigida recebeu aprovação humana. As correções posteriores não são contabilizadas como acertos originais do OCR.
- **RF11:** o histórico central contém cinco eventos reais: execução e decisão humana de RF06, execução e decisão humana de RF08, e execução de RF07. O histórico anterior incompleto permanece uma limitação; nenhum evento antigo foi inventado. RF10 mantém nota de proveniência própria, ainda não integrada ao log central.
- `python -m src.verificar_pendencias` verifica os arquivos, os hashes, a ordem temporal documentada e os vínculos de aprovação sem chamar APIs nem alterar a auditoria.

## Conferência definitiva das evidências (sem apresentação)

Execute `python -m src.verificar_pendencias` e `python -m src.demonstracao` para conferir o pacote sem chamadas à API. Consulte `documentacao/matriz_conformidade_pdf.md` para a correspondência de **cada requisito do enunciado** com arquivos de evidência e limitações. A execução de testes não comprova, por si só, que existiam gabaritos anteriores às inferências ou logs históricos que não foram coletados.

O áudio RF07 da minuta revisada foi gerado e aprovado por escuta em 17/10/2026; os metadados originais ainda registram revisão pendente no instante da geração, o que é historicamente correto.

## Desafio 2 (Aulas 08 a 14)

### Objetivo

Nesta etapa, a Central Inteligente de Atendimento foi ampliada para
consultar documentos ficticios, organizar solicitacoes, buscar informacoes
no acervo e apresentar respostas com fontes. Tambem foram adicionadas
revisao humana e analise de sentimentos.

O projeto continua sendo um prototipo local, sem envio automatico de respostas.

### Funcionalidades

- Extracao estruturada e validacao de JSON.
- Resumo, classificacao de solicitacoes e identificacao de entidades.
- Regras de seguranca para entradas e documentos.
- Indice local persistente com vetores de hashing lexical.
- Busca de trechos com similaridade e identificacao das fontes.
- RAG extrativo com resposta fundamentada ou abstencao.
- Interface Streamlit para documentos, atendimento e revisao humana.
- Classificacao de sentimentos com painel de resultados.

### Arquivos principais

| Arquivo ou pasta | Finalidade |
|---|---|
| dados/acervo/ | Documentos ficticios |
| dados/solicitacoes/ | Solicitacoes ficticias |
| dados/avaliacoes/ | Avaliacoes de atendimento |
| dados/gabaritos/desafio2_*.json | Gabaritos e testes |
| src/schemas.py | Validacao de dados |
| src/nlp.py | Resumo, categorias e entidades |
| src/guardrails.py | Regras de seguranca |
| src/ingestion.py | Leitura e divisao de documentos |
| src/embeddings.py | Indice persistente |
| src/rag.py | Respostas fundamentadas |
| src/fluxo_desafio2.py | Fluxo de atendimento e revisao |
| src/app.py | Interface Streamlit |
| src/sentiment.py | Classificacao de sentimentos |
| src/metrics.py | Indicadores |
| src/avaliar_desafio2.py | Avaliacao offline |
| testes/teste_desafio2.py | Testes automatizados |

### Instalacao

Na pasta do projeto, ative o ambiente virtual, se estiver utilizando um,
e instale as dependencias com:

    python -m pip install -r requirements.txt

### Execucao

Para iniciar a interface no Windows PowerShell:

    $env:PYTHONPATH = (Get-Location).Path
    python -m streamlit run src/app.py

Acesse http://localhost:8501 no navegador.

Na aba Documentos e atendimento, selecione os documentos e use
Indexar documentos para criar ou atualizar o indice. Depois, digite
uma solicitacao ficticia e clique em Processar solicitacao.

Na aba Revisao, escolha uma decisao, informe a justificativa e
registre a avaliacao humana.

Na aba Sentimentos, consulte os resultados das avaliacoes ficticias.

O indice fica armazenado em indice/acervo.json. Para recria-lo,
execute novamente a indexacao pela interface.

### Testes

Testes automatizados:

    python -m unittest discover -s testes -p "teste_desafio2.py" -v

Avaliacao offline:

    python -m src.avaliar_desafio2

Comparacao de chunking:

    python -m src.comparar_chunking

### Resultados verificados em 30/10/2026

| Avaliacao | Resultado |
|---|---|
| Testes automatizados | 9 de 9 aprovados |
| Recuperacao Top-3 | 5 de 5 (100%) |
| Abstencao | 2 de 2 (100%) |
| Sentimentos | 12 de 12 (100%) |
| Consultas manuais do RAG | 5 de 5 com resultado esperado |
| Revisao humana | Decisao revisar registrada pela interface |

Nas 12 avaliacoes ficticias, foram identificadas tres positivas,
tres negativas, tres neutras e tres indeterminadas. Tres casos
foram encaminhados para revisao.

Os percentuais representam apenas os conjuntos locais avaliados,
nao uma garantia de acerto em qualquer situacao.

### Validacao de fontes contraditorias - Q08

Foi realizado um teste com duas versoes ficticias de um documento,
uma informando prazo de 5 dias uteis e outra de 10 dias uteis.

O RAG recuperou os dois trechos e retornou `conflito de fontes`,
indicando a necessidade de revisao humana, sem escolher um prazo.

Esse cenario foi incluido nos testes automatizados como
`test_fontes_contraditorias`.

A verificacao atual cobre prazos numericos divergentes entre
versoes do mesmo documento. Outros tipos de contradicao ainda
nao foram validados.


### RF19 - Implementacao alternativa

Foi realizada uma avaliacao complementar do RAG da implementacao alternativa.

| Indicador | Resultado |
|---|---:|
| Perguntas respondiveis (T08) | 4/5 (80%) |
| Abstencao (T09) | 2/2 (100%) |
| Identificacao de conflito (T10) | 1/1 (100%) |
| Testes integrados | 27 aprovados |
| Subtestes | 2 aprovados |

A pergunta Q03, sobre heteroidentificacao da cota L1, permaneceu
sem evidencias suficientes e foi registrada como ponto de melhoria.

Na pergunta Q08, o sistema identificou a divergencia entre o edital
original e o Retificador 06, sinalizando a necessidade de revisao humana.

A execucao integrada apresentou um aviso de depreciacao na biblioteca
de embeddings, sem falhas nos testes.

Relatorio detalhado:
`documentacao/AVALIACAO_RF19_ALTERNATIVO.md`

### Limitacoes

O indice utiliza hashing lexical com 1024 dimensoes e similaridade
de cosseno. Nao e um modelo de embeddings semanticos treinado.

O RAG e extrativo e utiliza trechos do acervo. Foi acrescentada
uma reclassificacao lexical para melhorar a escolha das fontes
em algumas perguntas, mas ela nao elimina as limitacoes da busca.

A classificacao de sentimentos utiliza regras locais. Os resultados
nao devem ser tratados como caracteristicas pessoais dos autores.

O adaptador de provedor remoto depende de configuracao e credenciais.
Nao foi demonstrada equivalencia de qualidade com o fluxo local.

### Privacidade e revisao humana

O projeto utiliza dados ficticios, nao realiza envio automatico
e exige revisao humana antes de aprovar respostas institucionais.

A interface permite excluir documentos do indice. A exclusao
de resultados derivados e as regras de retencao ainda precisam
de verificacao especifica.

### Evidencias e pendencias

O PDF do Desafio 2 exige, entre outros itens:

- Seis documentos ficticios em dois formatos.
- Seis solicitacoes e respectivos gabaritos.
- Oito perguntas RAG, incluindo duas sem resposta e uma com conflito.
- Tres entradas adversariais.
- Comparacao de duas configuracoes de chunking.
- Matriz de testes T01 a T15 e regressao de texto e audio ou OCR.
- Evidencias de aprovacao, rejeicao ou revisao humana.
- Auditoria, exclusao de documentos e teste de troca de provedor.
- Relatorio tecnico e registro do uso de IA no desenvolvimento.

Os testes realizados ate agora nao comprovam todos esses itens.
As evidencias precisam ser conferidas antes de declarar o desafio
integralmente concluido.

Consulte documentacao/RELATORIO_DESAFIO2.md para a documentacao
tecnica complementar, quando disponivel.

### Resultado final do Desafio 2

Avaliacao local realizada com dados ficticios, sem chamadas reais
as APIs de IA nos testes finais.

Resultados:
- 144 testes automatizados aprovados.
- 6 solicitacoes ficticias avaliadas.
- Recuperacao RAG Top-3: 5/5.
- Abstencao por falta de evidencia: 2/2.
- Classificacao de sentimentos: 12/12.
- 3 entradas adversariais encaminhadas para revisao.
- Decisoes humanas registradas: aprovada, rejeitada e revisar.
- Testes automatizados de exclusao de documentos.

Para executar os testes:
python -m pytest testes -q

Para abrir a interface:
$env:PYTHONPATH = (Get-Location).Path
python -m streamlit run src/app.py

O relatorio completo e a matriz T01 a T15 estao em:
documentacao/RELATORIO_DESAFIO2.md

Limitacoes: busca por hashing lexical, provedores testados
com simulacoes e metricas calculadas em conjunto ficticio pequeno.


### Integração com a revisão do Adriano


## Integração do Desafio 2 — Adriano, Líbia e Yasmine

A integração reuniu as implementações da equipe sem substituir o projeto principal.

A implementação alternativa foi organizada em `src/alternativo_desafio02/`,
com testes próprios em `testes_alternativos_desafio02/`.

Foram integrados módulos de validação, NLP, guardrails, ingestão,
embeddings, RAG, sentimentos, privacidade e auditoria.

### Como executar os testes da integração

Na pasta principal do projeto, com o ambiente virtual ativado:

    python -m pytest testes testes_alternativos_desafio02 -q --tb=short

Os resultados anteriores de 9 e 144 testes permanecem no README
como registros históricos da implementação principal.

A execução conjunta mais recente, realizada em 31/10/2026,
aprovou 250 testes das duas implementações.

### Resultados da integração

Em 31/10/2026, utilizando Windows e Python 3.12, a execução conjunta
dos testes apresentou:

- 250 testes aprovados.
- Nenhuma falha.
- Um aviso de depreciação.
- RF16: 19 testes aprovados.
- RF19: 4 testes aprovados.
- RF21: 9 testes aprovados.
- RF24: 6 testes aprovados.

No diagnóstico do RF19, foram indexados 44 chunks. O RAG respondeu
corretamente a 4 de 5 perguntas respondíveis e se absteve corretamente
nas 2 perguntas sem resposta.

### Limitações identificadas

- O adaptador Gemini alternativo ainda não realiza chamadas reais à API.
- A detecção de contradições Q08 foi testada em um cenário específico.
- Uma pergunta respondível do RF19 ficou sem evidência suficiente.
- Os arquivos de testes RF20 e RF23 da implementação alternativa estão vazios.
- O mascaramento de dados cobre os padrões testados, não todos os dados pessoais.

A aprovação dos testes não comprova que todos os requisitos estejam concluídos.

### Documentação da integração

- `documentacao/RELATORIO_DESAFIO2.md`
- `documentacao/relatorio_tecnico_desafio02.md`

### Atualizacao de fechamento — 02/11/2026

Esta secao registra as verificacoes mais recentes e complementa os resultados
historicos acima. Os numeros de execucoes anteriores foram mantidos como
historico e nao devem ser somados entre si.

| Verificacao | Resultado observado | Interpretacao |
|---|---:|---|
| Suíte `testes_alternativos_desafio02/` | 100 aprovados | Testes automatizados alternativos executados no Windows com Python 3.12.10. |
| Auditoria RF21 (`teste_rf21_auditoria.py`) | 10 aprovados | Testes automatizados do registro e tratamento de eventos. |
| Regressao T15 | 1 teste + 2 subtestes aprovados | Entradas texto e OCR percorreram o fluxo automatizado; a decisao de revisao do teste e simulada. |
| Compilacao de `avaliar_sentimentos_real.py` | Aprovada | Verificacao sintatica; nao executa chamadas a API. |
| Tentativa real Gemini RF22 | 0 classificacoes validas em 12 tentativas | Foram observados HTTP 503, HTTP 429 e timeout; acuracia nao calculavel (0/0). |

#### RF22 — conjunto de sentimentos A01–A12

O conjunto utilizado em `dados/avaliacoes/avaliacoes.json` possui os IDs
`A01` a `A12`. O gabarito correspondente e
`dados/gabaritos/desafio2_sentimentos.json`, tambem com IDs `A01` a `A12`.
O gabarito alternativo em `dados/desafio02_alternativo/gabaritos/sentimentos.json`
referencia arquivos `aval01.txt` a `aval12.txt`, que nao existem no pacote, e
nao deve ser usado para avaliar o conjunto A01–A12.

O script `src/alternativo_desafio02/avaliar_sentimentos_real.py` foi ajustado
para usar o gabarito correspondente e interromper a execucao se os IDs nao
coincidirem. A tentativa real anterior do Gemini nao produziu classificacoes
validas. Portanto, o resultado e **nao calculavel (0/0)**, e nao 0% nem 100%.
Os testes com mocks/regras locais validam somente o comportamento local e nao
substituem uma execucao real do provedor.

#### RF23, T11 e T14 — limites das evidencias

A matriz T01–T15 deve distinguir teste automatizado de demonstracao manual.
A regressao T15 aprovada nao comprova uma decisao humana real pela interface.
A existencia dos testes de revisao e exclusao tambem nao substitui a evidencia
manual de T11 (operador registrando decisao e justificativa) e T14 (exclusao,
log e busca posterior sem o documento). Esses dois criterios permanecem
pendentes de demonstracao manual documentada.

A proporcao de respostas RAG com todas as afirmacoes sustentadas ainda nao foi
medida com numerador e denominador. Os resultados Top-3 e de abstencao nao
podem ser usados como substitutos dessa metrica RF23.

#### Publicacao e pacote

O commit `650b743` foi criado na branch `integracao` em 02/11/2026. Isso nao
comprova publicacao na branch `main`. A publicacao deve ser confirmada na
maquina que possui o repositorio Git e acesso ao remoto, seguindo o checklist
de entrega. O ZIP recebido para esta atualizacao nao contem a pasta `.git`;
portanto, nao permite verificar o estado remoto nem executar `git push`.

### Material de apresentação

- `documentacao/SLIDE_RESUMO_CANVA.pptx`: slide-resumo em formato PowerPoint, que pode ser importado no Canva.
- `documentacao/ROTEIRO_APRESENTACAO_VIDEO.md`: roteiro organizado pelos seis blocos e tempos da seção 14 do PDF.

O PDF exige apresentação de até 15 minutos, mas não especifica gravação de vídeo, duração ou formato. O roteiro pode ser usado como apoio à apresentação ou gravação complementar. O slide-resumo não substitui uma apresentação completa de 15 minutos.


### Evid?ncia complementar ? T14 (02/11/2026)

A exclus?o manual do documento `documentacao_04_v1.txt` foi demonstrada.
Um trecho foi removido do ?ndice, o arquivo original foi preservado
e o evento foi registrado na auditoria.

Ap?s recarregar o ?ndice, a busca n?o encontrou o documento exclu?do.
Os demais documentos continuaram dispon?veis.

Evid?ncia: `resultados/logs/exclusoes_desafio2.jsonl`.
Situa??o: demonstra??o manual conclu?da.
