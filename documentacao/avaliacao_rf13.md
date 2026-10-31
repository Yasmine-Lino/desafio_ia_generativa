# RF13 — Avaliação de qualidade e revisão humana

## Como avaliamos

A avaliação considera fidelidade às fontes, completude, formato, linguagem e segurança. Cada resultado recebe uma decisão humana antes de qualquer uso. Uma divergência em dados críticos, como protocolo, nome ou data, impede o uso automático.

A amostra abaixo contém dois casos. Ela é pequena e não representa uma medição geral de desempenho do sistema.

## Caso RF06 — Transcrição de áudio

**Esperado:** transcrição fiel ao áudio, especialmente nos campos que identificam a solicitação.

**Resultado observado:** a comparação com o texto de referência indicou similaridade de 0,9534 e correspondência exata normalizada falsa.

**Gravidade:** alta, porque divergências em protocolo, nomes ou datas podem afetar o atendimento.

**Decisão:** rejeitada para uso automático. A transcrição requer conferência dos campos críticos antes de ser usada. A revisão humana registrada como geral não substitui essa conferência específica.

## Caso RF09 — Minuta de resposta

**Esperado:** preparar um rascunho com os dados disponíveis, sem afirmar que a matrícula foi efetivada nem inventar documentos pendentes.

**Resultado observado:** a minuta informou que os documentos pendentes precisam ser confirmados pelo setor responsável, identificou as fontes e permaneceu como rascunho. O envio automático continuou desativado.

**Gravidade:** baixa na amostra avaliada. A informação ausente foi sinalizada, sem ser inventada.

**Decisão:** aprovada pela equipe como minuta. A aprovação não autoriza envio automático.

## Indicador da amostra

Nesta amostra, 1 de 2 casos foi aprovado para a finalidade avaliada: **50%**. O RF06 foi rejeitado para uso automático e o RF09 foi aprovado como rascunho revisado.

Esse percentual descreve somente os dois casos acima. Não deve ser interpretado como taxa geral de aprovação ou como garantia de qualidade em outros documentos.

## Limitações e riscos restantes

A amostra é pequena. A similaridade automática não identifica, por si só, se uma divergência altera um dado importante. A revisão humana precisa conferir explicitamente os campos críticos.

O resultado do RF08 foi revisado visualmente, mas o projeto ainda precisa registrar uma comparação quantitativa com um gabarito independente. Portanto, ele não foi incluído no indicador acima.

As saídas permanecem sujeitas à revisão humana. Nenhuma minuta deve ser enviada sem autorização e conferência do setor responsável.