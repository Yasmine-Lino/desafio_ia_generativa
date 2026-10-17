# RF08 — Visão e OCR

## Objetivo

Extrair o conteúdo de um documento digitalizado, comparar a transcrição com uma referência conferida no documento original e registrar as divergências para revisão humana.

## Documento e implementação

Foi usada a ficha fictícia `dados/originais/entrada_pdf-imagem.pdf`, com uma página digitalizada.

O módulo `src/vision.py` converte a página em imagem com PyMuPDF e solicita a extração ao Gemini. A execução registrada usou o modelo `gemini-3.8-flash`, levou 19,28 segundos e contabilizou 3.709 tokens.

O módulo `src/comparacao_vision.py` compara o OCR com o gabarito. A comparação ignora diferenças de maiúsculas, acentos e pontuação nos campos.

## Resultado da comparação

A comparação registrou similaridade de 0,9989. Dos 24 campos comparados, 23 coincidiram e um divergiu: a data da matrícula.

O OCR bruto registrou `14/01/2026`; a conferência do PDF e o gabarito registraram `14/10/2026`. A transcrição revisada foi corrigida para refletir a data conferida. O OCR bruto foi preservado.

O gabarito foi elaborado após a execução do OCR, com conferência do documento original. Por isso, esta comparação documenta a revisão do caso, mas não constitui uma avaliação independente feita antes da execução.

## Arquivos

- `dados/processados/rf08_texto_bruto.txt`: transcrição original do OCR, preservada.
- `dados/gabaritos/rf08_texto.txt`: transcrição de referência conferida no PDF.
- `dados/processados/rf08_comparacao.json`: métricas e campos divergentes.
- `dados/processados/rf08_texto_revisado.txt`: transcrição conferida e corrigida.
- `dados/processados/rf08_informacoes.json`: dados da execução e da revisão humana.

Os arquivos de texto e os metadados do caso ficam excluídos do Git por conterem dados do formulário. O exemplo é fictício; documentos reais exigiriam proteção adicional.

## Revisão humana e limitações

A divergência na data foi conferida no PDF e corrigida no texto revisado. A aprovação se aplica à transcrição revisada, não ao OCR bruto sem correção.

A similaridade geral não garante que os campos críticos estejam corretos. Nomes, datas e números devem ser conferidos individualmente antes de qualquer uso. O gabarito deste caso foi feito após o OCR e não deve ser apresentado como referência independente.