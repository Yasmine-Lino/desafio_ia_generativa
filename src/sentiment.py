"""Triagem de sentimento por regras, com incerteza explícita (RF22)."""
import re
POSITIVOS={"ótimo","bom","excelente","rápido","satisfeito","agradeço","gentil","resolvido"}
NEGATIVOS={"ruim","péssimo","demora","atraso","insatisfeito","erro","horrível","não resolveu"}
def classificar(item):
    texto=item["texto"].casefold()
    palavras=set(re.findall(r"\w+",texto))
    p=bool(palavras&POSITIVOS);n=bool(palavras&NEGATIVOS) or "não resolveu" in texto
    ironia=any(x in texto for x in ("só que não","ironia","#sqn","parabéns pela demora"))
    rotulo="indeterminada" if (p and n) or ironia else "positiva" if p else "negativa" if n else "neutra" if len(palavras)>=4 else "indeterminada"
    return {"id":item["id"],"polaridade":rotulo,"justificativa":"Misto/irônico ou contexto insuficiente" if rotulo=="indeterminada" else "Indícios lexicais; estimativa não calibrada", "necessita_revisao":rotulo=="indeterminada"}
