"""Exclusao controlada de resultados derivados do Desafio 2.
Nao apaga documentos originais nem auditoria historica do Desafio 1.
"""
import datetime
import json
from pathlib import Path


def excluir_documento(indice, nome, *, log_execucoes="resultados/logs/desafio2.jsonl",
                      revisoes="resultados/minutas/revisoes_desafio2.jsonl",
                      log_exclusoes="resultados/logs/exclusoes_desafio2.jsonl"):
    if not isinstance(nome, str) or not nome or Path(nome).name != nome:
        raise ValueError("Nome de documento invalido")
    itens = [x for x in indice.dados["itens"].values() if x["documento"] == nome]
    if not itens:
        raise ValueError("Documento nao encontrado no indice")
    ids_trechos = {x["id"] for x in itens}
    origem = Path(log_execucoes)
    registros = []
    if origem.exists():
        for linha in origem.read_text(encoding="utf-8").splitlines():
            if linha.strip():
                registros.append(json.loads(linha))
    afetados = {r["id"] for r in registros if ids_trechos.intersection(r.get("ids_recuperados", []))}
    destino_revisoes = Path(revisoes)
    linhas_revisoes = []
    if destino_revisoes.exists():
        linhas_revisoes = [json.loads(x) for x in destino_revisoes.read_text(encoding="utf-8").splitlines() if x.strip()]
    restantes = [r for r in registros if r.get("id") not in afetados]
    revisoes_restantes = [r for r in linhas_revisoes if r.get("id") not in afetados]
    # Preparar todos os dados antes de alterar o indice.
    indice.excluir(nome)
    def escrever_jsonl(caminho, dados):
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in dados), encoding="utf-8")
    if origem.exists():
        escrever_jsonl(origem, restantes)
    if destino_revisoes.exists():
        escrever_jsonl(destino_revisoes, revisoes_restantes)
    auditoria = Path(log_exclusoes)
    auditoria.parent.mkdir(parents=True, exist_ok=True)
    evento = {"documento": nome, "horario": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "trechos_removidos": len(itens), "execucoes_derivadas_removidas": len(afetados),
              "revisoes_derivadas_removidas": len(linhas_revisoes) - len(revisoes_restantes),
              "documento_original_preservado": True}
    with auditoria.open("a", encoding="utf-8") as f:
        f.write(json.dumps(evento, ensure_ascii=False) + "\n")
    return evento
