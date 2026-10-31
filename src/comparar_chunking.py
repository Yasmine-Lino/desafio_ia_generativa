"""Compara duas configurações de chunking com cinco perguntas respondíveis (RF18)."""
import json
from pathlib import Path
from .embeddings import Indice

CONFIGURACOES = ((300, 50), (600, 100))  # caracteres
TOP_K = 3

def executar(raiz=Path('.')):
    raiz = Path(raiz)
    perguntas = json.loads((raiz/'dados/gabaritos/desafio2_perguntas.json').read_text(encoding='utf-8'))
    respondiveis = [p for p in perguntas if p['tipo'] == 'respondível']
    if len(respondiveis) != 5:
        raise ValueError('O gabarito deve conter cinco perguntas respondíveis')
    arquivos = sorted((raiz/'dados/acervo').glob('*.txt')) + sorted((raiz/'dados/acervo').glob('*.pdf'))
    if not arquivos:
        raise ValueError('Acervo vazio')
    resultados = []
    for tamanho, sobreposicao in CONFIGURACOES:
        indice = Indice(raiz/f'indice/comparacao_{tamanho}_{sobreposicao}.json')
        indice.indexar(arquivos, tamanho=tamanho, sobreposicao=sobreposicao)
        itens = []
        for pergunta in respondiveis:
            achados = indice.buscar(pergunta['pergunta'], TOP_K)
            fontes = {x['documento'] for x in achados}
            acerto = bool(fontes.intersection(pergunta['fontes_referencia']))
            itens.append({'id': pergunta['id'], 'acerto': acerto, 'referencias': pergunta['fontes_referencia'],
                          'top_k': [{'id': x['id'], 'documento': x['documento'], 'similaridade': x['similaridade']} for x in achados]})
        n = sum(x['acerto'] for x in itens)
        resultados.append({'tamanho_caracteres': tamanho, 'sobreposicao_caracteres': sobreposicao,
                           'top_k': TOP_K, 'acertos': n, 'total': len(itens), 'taxa': n/len(itens), 'perguntas': itens})
    escolhido = max(resultados, key=lambda x: (x['taxa'], x['tamanho_caracteres']))
    saida = {'modelo': 'hashing-lexical-v1', 'resultados': resultados,
             'escolhida': {'tamanho_caracteres': escolhido['tamanho_caracteres'],
                           'sobreposicao_caracteres': escolhido['sobreposicao_caracteres']},
             'justificativa': 'Maior acerto top-3; em empate, chunks maiores preservam mais contexto.'}
    destino = raiz/'resultados/metricas/comparacao_chunking.json'
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(saida, ensure_ascii=False, indent=2), encoding='utf-8')
    return saida

if __name__ == '__main__':
    print(json.dumps(executar(), ensure_ascii=False, indent=2))
