# RF12 — Privacidade e minimização de dados

## Dados utilizados

Os exemplos deste desafio usam dados fictícios. A ficha e o áudio contêm dados como nome, CPF, RG, data de nascimento, nome da mãe, e-mail e informações de matrícula.

Nome, CPF, RG, data de nascimento e nome da mãe podem identificar o solicitante. E-mail e telefone permitem contato. Protocolo, curso e pedido ajudam a localizar e entender o atendimento.

Para classificar a solicitação e preparar uma minuta, não é necessário enviar ao modelo todos os dados de identificação.

## Medidas aplicadas

Em `src/extracao.py`, o projeto tenta remover ou mascarar dados pessoais reconhecidos antes de enviar texto ao modelo. Em `src/minuta.py`, são selecionados os campos necessários para redigir a minuta.

A chave de acesso à API fica no `.env`, excluído pelo Git. O `.env.example` não deve conter uma chave real. O envio automático permanece desativado e as minutas dependem de revisão humana.

Os registros de auditoria guardam metadados e referências aos artefatos, sem incluir o conteúdo integral da solicitação nem credenciais.

## Limitações e riscos

A remoção depende dos padrões reconhecidos pelo código e pode deixar passar dados em formatos inesperados. O áudio e o PDF enviados ao provedor também podem conter dados pessoais.

Em um atendimento real, a equipe deve avaliar quais informações são estritamente necessárias, as condições de processamento do provedor e a possibilidade de processamento local. Os arquivos originais devem ter acesso restrito e prazo de retenção definido.

A revisão humana continua necessária antes de usar qualquer resultado em um atendimento institucional.