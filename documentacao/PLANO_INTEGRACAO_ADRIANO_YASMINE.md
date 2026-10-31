# Integração das branches revisao-adriano e dev-yasmine

## Base e escopo

Base: ZIP `desafio_ia_generativa-dev-yasmine (1).zip`. Fonte de revisão: ZIP `desafio_ia_generativa-revisao-adriano(1).zip`. Esta pasta é uma cópia de integração, não um merge executado no GitHub. A branch publicada `dev-yasmine` não foi modificada.

## Incorporado

- `documentacao/privacidade_lgpd.md` e `documentacao/avaliacao_rf13.md` do Adriano, mantidos como documentação histórica; não substituem as evidências atuais.
- `resultados/imagens/rf10_cartaz_matricula_revisado_v2.png` preservado como alternativa, sem mudar a imagem aprovada nem os metadados.
- `src/audio.py`: `normalizar_texto` e `comparar_transcricao` do Adriano, sem mudar `transcrever_audio`.
- `src/image_generation.py`: `carregar_proveniencia` para leitura e validação sem escrita, migração ou aprovação automática.
- `.gitignore`: regras para arquivos de resolução de conflitos e backups.
- `testes/teste_integracao_adriano.py`: testes de regressão das adições.

## Decisões de conflito

- `src/audit.py`: manter implementação da Yasmine, pois `registrar_execucao(dados, ...)` exige campos validados; a versão Adriano usa outra assinatura. Substituir causaria regressão.
- `src/llm_client.py`: manter implementação da Yasmine, com tentativas para erros transitórios; a versão Adriano depende da assinatura incompatível de auditoria. A refatoração `_consultar_llm_sem_auditoria` **não foi transplantada** sem adaptação e testes de integração com falhas reais/simuladas.
- `src/main.py`: preservar inicialização atual; registro RF01 depende da política de auditoria, não ativar sem caso de teste.
- `src/comparacao_vision.py`: preservar gabarito e filtros da Yasmine; arquivos de referência são diferentes.
- `src/minuta.py`, `src/extracao.py`, `src/sintese_voz.py`, `src/vision.py`, `src/prompt_seguro.py`, `src/comparacao_prompts.py`: preservar implementações atuais com validações e testes já associados. Nenhuma substituição automática.
- `requirements.txt`: manter versões da Yasmine; `pymupdf==1.28.2` atende ao intervalo `>=1.24,<2` do Adriano.
- `config.json` e `config_desafio2.json`: manter separados; não expor chaves nem ativar envio automático.
- `README.md`: preservar documentação da Yasmine e apontar para este relatório.

## Validação e limitações

Os testes de regressão devem ser executados em um ambiente com as dependências do `requirements.txt`. Os ZIPs não contêm o histórico Git necessário para criar um merge real. A seleção visual da imagem RF10 e a revisão humana final continuam pendentes; não atribuir aprovação automática. Antes da integração foi detectada falha de hash em `testes/teste_conformidade_final.py::test_revisao_audio_final_corresponde_a_minuta` na cópia ZIP; isso é uma divergência dos artefatos do ZIP, não uma falha introduzida pela integração. Os 144 testes relatados anteriormente no computador Windows não foram reproduzidos nesta cópia.

## Aplicação segura no Git local (Windows)

1. Confirmar `git status` e criar uma branch nova a partir de `dev-yasmine`: `git switch dev-yasmine`; `git switch -c integracao-adriano-yasmine`.
2. Fazer backup da pasta local ou usar o ZIP desta integração para comparar os arquivos alterados. **Não sobrescrever automaticamente** o projeto com este ZIP, porque há modificações locais do Desafio 1.
3. Copiar seletivamente os arquivos da lista "Incorporado"; inspecionar `git diff` e verificar dados pessoais.
4. Executar `python -m pytest testes -q` e investigar qualquer falha de baseline antes de mesclar.
5. Somente após aprovação humana: `git add` dos arquivos selecionados, `git commit`, `git push -u origin integracao-adriano-yasmine`, abrir Pull Request para revisão. Não mesclar na `main` sem autorização da equipe.

## Execução de testes nesta cópia

- `python -m pytest testes/teste_integracao_adriano.py -q`: **4 passed**.
- `python -m pytest testes -q`: **144 passed, 4 failed** neste ambiente.
- Falhas: `testes/teste_conformidade_final.py::test_revisao_audio_final_corresponde_a_minuta` (hash do áudio/minuta); `testes/teste_desafio2.py::ClienteOpenAITestes::test_cliente_openai_simulado` (OPENAI_API_KEY ausente); `testes/teste_desafio2.py::AuditoriaProvedoresT12::test_recuperacao_auditada_t12` (módulo não exposto como atributo de `src` no teste); `testes/teste_rf11_sintese_voz.py::TestesAuditoriaVozRF11::test_gravacao_real_wav_json_com_http_simulado` (SystemExit: 1).
- As falhas não devem ser ocultadas nem corrigidas apenas para inflar a contagem. É necessário verificar o ambiente e comparar com o baseline do Git local antes de concluir a integração.
