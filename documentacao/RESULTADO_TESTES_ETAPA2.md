# Testes — etapa 2

Ambiente de execução: Linux, Python 3.13. Resultado **não equivale à validação no Windows/Python 3.12**.

- `python -m pytest testes/teste_unificacao_desafio02.py -q`: **12 aprovados**.
- `python -m pytest testes -q --tb=short`: **156 aprovados, 4 falhas**.
- Falhas herdadas da etapa anterior: `test_revisao_audio_final_corresponde_a_minuta` (hash), `test_cliente_openai_simulado` (variável OPENAI_API_KEY), `test_recuperacao_auditada_t12` (referência a módulo), `test_gravacao_real_wav_json_com_http_simulado` (ID de execução de minuta).
- Os testes de integração semântica utilizam índices simulados. Não foi executado ChromaDB com modelo real.
- Não foram alterados testes legados para mascarar falhas.
