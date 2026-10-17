# RF07 — Síntese de voz e acessibilidade

## Objetivo

Gerar uma versão falada de uma minuta institucional aprovada por uma pessoa, para ampliar a acessibilidade da comunicação.

## Implementação

Foi criado o arquivo `src/sintese_voz.py`, responsável pela geração do áudio.

O programa utiliza:
- Provedor: Google Gemini
- Modelo: gemini-2.5-flash-preview-tts
- Voz: Kore
- Idioma: português brasileiro
- Entonação solicitada: institucional, cordial e com ritmo moderado
- Formato de saída: WAV

A síntese depende de confirmação de aprovação humana, informada pelo argumento `--aprovado`.

Quando a minuta contém a expressão "não localizado", o programa acrescenta um aviso ao início do texto falado.

## Teste realizado

Foi utilizada uma minuta fictícia, salva em:

`resultados/minutas/rf07_minuta_teste.txt`

O teste não representa uma comunicação oficial nem substitui a minuta definitiva que será produzida no RF09.

O arquivo de áudio foi gerado em:

`resultados/audios/rf07_minuta_falada.wav`

As informações técnicas da execução foram registradas em:

`resultados/audios/rf07_informacoes.json`

## Revisão humana

Situação: APROVADO PARA O TESTE DO RF07.

A revisão foi realizada por escuta completa do áudio gerado.

Resultado informado pela revisora:
- O aviso inicial sobre informações não localizadas foi lido corretamente.
- O conteúdo falado correspondeu à minuta de teste.
- Não foram identificadas omissões relevantes.
- Não foram identificados acréscimos relevantes.
- A voz foi considerada adequada e compreensível.

## Acessibilidade

A versão falada permite que o conteúdo seja ouvido, oferecendo uma alternativa à leitura do documento escrito.

Esse recurso pode auxiliar pessoas com dificuldades de leitura e pessoas que preferem receber informações por áudio.

## Limitações

A síntese de voz depende da disponibilidade da API.

O modelo pode apresentar diferenças de pronúncia, entonação ou leitura de números e siglas.

A confirmação de aprovação no programa é declarada pelo operador e não constitui um sistema de autenticação.

A correspondência entre o texto aprovado e o áudio precisa ser conferida por uma pessoa.

O áudio não substitui a versão escrita nem garante acessibilidade para todas as pessoas, incluindo aquelas com deficiência auditiva.

## Integração futura

Quando o RF09 estiver implementado, a síntese deverá receber a minuta institucional definitiva somente após a revisão e aprovação humana.

O sistema não realiza envio automático.
