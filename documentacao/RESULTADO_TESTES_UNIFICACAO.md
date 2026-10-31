# Resultado de testes nesta execução

Ambiente: Linux, Python 3.13, dependências disponíveis no ambiente.

- `python -m pytest testes/teste_unificacao_desafio02.py -q`: **5 aprovados**.
- `python -m pytest testes -q --tb=short`: **149 aprovados e 4 falharam**.

Falhas observadas:
1. `testes/teste_conformidade_final.py::test_revisao_audio_final_corresponde_a_minuta`: divergência de hash.
2. `testes/teste_desafio2.py::ClienteOpenAITestes::test_cliente_openai_simulado`: `OPENAI_API_KEY` ausente.
3. `testes/teste_desafio2.py::AuditoriaProvedoresT12::test_recuperacao_auditada_t12`: `src.provedor_desafio2` não resolvido pelo teste.
4. `testes/teste_rf11_sintese_voz.py::TestesAuditoriaVozRF11::test_gravacao_real_wav_json_com_http_simulado`: falta `--id-execucao-minuta`.

Essas falhas são compatíveis com as observadas em testes anteriores em Linux; **não foram corrigidas ou omitidas**. No Windows da usuária, a base anterior havia apresentado 148 testes aprovados. Isso não valida automaticamente esta versão unificada.

Os testes originais RF14–RF24 do segundo ZIP foram preservados para adaptação, mas não foram executados como parte da suíte integrada.

## Validacao posterior no Windows - 31/10/2026

Ambiente: Windows, Python 3.12.

Comando executado:

`python -m pytest testes testes_alternativos_desafio02 -q --tb=short`

Resultado: **250 testes aprovados, 0 falhas, 1 FutureWarning**, em 80,58 segundos.

O aviso se refere ao metodo `get_sentence_embedding_dimension` da biblioteca
sentence-transformers, que sera renomeado futuramente.

Os resultados anteriores no Linux foram mantidos acima como historico.
A validacao atual confirma a execucao conjunta das suites principal e alternativa.

Limitacoes:
- O adaptador Gemini alternativo nao realiza chamadas reais a API.
- O caso Q08 de contradicao usa uma regra especifica com fontes simuladas.
- Os arquivos de teste RF20 e RF23 estao vazios, portanto nao comprovam
  cobertura automatizada propria desses requisitos.
