# RF10 — Geração ou edição de imagem

## Objetivo

Produzir uma peça visual de orientação relacionada ao caso fictício de matrícula utilizado no RF09.

## Ferramenta utilizada

ChatGPT, por meio de sua ferramenta integrada de geração de imagens.

Modelo: modelo de geração de imagens do ChatGPT; identificação técnica não disponibilizada.

Data da geração: 17/10/2026.

## Justificativa da escolha

Inicialmente foi testada a API Gemini com o modelo
gemini-2.5-flash-image.

A solicitação retornou HTTP 429, informando limite zero para
a cota gratuita de geração.

Para evitar cobrança e preservar o objetivo pedagógico,
a geração foi realizada pela ferramenta de imagens do ChatGPT.

O programa Python não realizou a geração da imagem.
Ele foi utilizado para validar os arquivos e registrar a proveniência.

## Prompt

Arquivo: prompts/rf10_geracao_imagem.txt

O prompt documenta sujeito, composição, estilo, iluminação,
proporção, cores, conteúdo e restrições.

## Arquivos produzidos

Imagem inicial:
resultados/imagens/rf10_cartaz_matricula.png

Imagem revisada:
resultados/imagens/rf10_cartaz_matricula_revisado.png

Registro de proveniência:
resultados/imagens/rf10_proveniencia.json

## Revisão visual

### Texto

A primeira imagem apresentava a orientação:
"Regularize documentos pendentes".

Essa redação poderia sugerir a existência de pendências confirmadas.

Como o RF05 não identificou quais documentos estavam pendentes,
foi produzida uma versão revisada com a orientação:
"Verifique se há documentos pendentes".

### Símbolos e objetos

Foram utilizados ícones educacionais, livros, computador,
documentos e materiais escolares.

Não foram utilizados brasões ou logotipos oficiais.

### Pessoas e mãos

Não há pessoas reais ou representações de mãos.
Não foi necessário utilizar imagem de pessoa real.

### Coerência visual

A peça utiliza linguagem institucional e elementos
relacionados à educação e à matrícula.

### Identificação de conteúdo sintético

O cartaz apresenta a identificação:
"Imagem gerada por inteligência artificial — material ilustrativo."

## Decisão humana

A versão revisada foi aprovada após conferência visual.

Tipo de decisão: aprovação com ajuste.

A imagem inicial foi preservada para comparação.

A aprovação não representa publicação oficial.

## Limitações

A geração foi realizada pela interface do ChatGPT,
não por uma chamada automatizada no programa Python.

A identificação técnica exata do modelo de imagens
não foi disponibilizada.

A validação automatizada atual verifica a existência,
a extensão e a assinatura inicial dos arquivos PNG,
mas não avalia integralmente a integridade ou a qualidade visual.

A avaliação de textos e coerência visual dependeu de revisão humana.

## Conclusão

O RF10 produziu uma peça visual sintética relacionada ao caso
fictício de matrícula.

A primeira versão foi corrigida após revisão crítica,
e a versão revisada foi aprovada.

Foram documentados a ferramenta, o prompt, a data,
a tentativa malsucedida com Gemini e a proveniência.
