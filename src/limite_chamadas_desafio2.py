"""Controle persistente de chamadas externas do Desafio 2."""

import datetime
import json
import os
import time
import msvcrt
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_CONTROLE = RAIZ / "resultados" / "logs" / "limite_chamadas_desafio2.json"


def reservar_chamada(caminho=None):
    """Reserva uma chamada com bloqueio entre processos no Windows."""
    arquivo = Path(caminho) if caminho is not None else ARQUIVO_CONTROLE
    arquivo.parent.mkdir(parents=True, exist_ok=True)

    config_arquivo = RAIZ / "config_desafio2.json"
    with config_arquivo.open(encoding="utf-8") as f:
        config = json.load(f)

    limite = config["limite_chamadas_diarias"]

    if type(limite) is not int or limite < 1:
        raise ValueError("Limite diario invalido")

    bloqueio = arquivo.with_name(arquivo.name + ".lock")

    with bloqueio.open("a+b") as controle:
        controle.seek(0, os.SEEK_END)

        if controle.tell() == 0:
            controle.write(b"0")
            controle.flush()

        adquirido = False

        for tentativa in range(100):
            try:
                controle.seek(0)
                msvcrt.locking(controle.fileno(), msvcrt.LK_NBLCK, 1)
                adquirido = True
                break
            except OSError:
                time.sleep(0.05)

        if not adquirido:
            raise RuntimeError("Nao foi possivel obter o bloqueio do contador")

        try:
            hoje = datetime.datetime.now(
                datetime.timezone.utc
            ).date().isoformat()

            if arquivo.exists():
                try:
                    dados = json.loads(
                        arquivo.read_text(encoding="utf-8")
                    )
                except (ValueError, UnicodeError) as erro:
                    raise RuntimeError(
                        "Arquivo do contador invalido"
                    ) from erro

                if (
                    not isinstance(dados, dict)
                    or set(dados) != {"data", "quantidade"}
                    or not isinstance(dados["data"], str)
                    or type(dados["quantidade"]) is not int
                    or dados["quantidade"] < 0
                ):
                    raise RuntimeError(
                        "Dados do contador invalidos"
                    )

                try:
                    data_registro = datetime.date.fromisoformat(
                        dados["data"]
                    )
                except ValueError as erro:
                    raise RuntimeError(
                        "Data do contador invalida"
                    ) from erro

                if data_registro.isoformat() != dados["data"]:
                    raise RuntimeError(
                        "Formato da data do contador invalido"
                    )

                quantidade = (
                    dados["quantidade"]
                    if dados["data"] == hoje
                    else 0
                )
            else:
                quantidade = 0

            if quantidade >= limite:
                raise RuntimeError(
                    "Limite diario de chamadas atingido"
                )

            novo = {
                "data": hoje,
                "quantidade": quantidade + 1
            }

            temporario = arquivo.with_name(
                arquivo.name + ".tmp"
            )

            temporario.write_text(
                json.dumps(
                    novo,
                    ensure_ascii=False,
                    indent=2
                ) + "\n",
                encoding="utf-8"
            )

            os.replace(temporario, arquivo)

            return {
                "utilizadas": quantidade + 1,
                "limite": limite
            }

        finally:
            controle.seek(0)
            msvcrt.locking(
                controle.fileno(),
                msvcrt.LK_UNLCK,
                1
            )
