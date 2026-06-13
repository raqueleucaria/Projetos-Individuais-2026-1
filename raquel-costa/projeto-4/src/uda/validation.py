"""Validação semântica pós-LLM dos Indicadores extraídos.

O Contrato Semântico (Pydantic) já garante tipos e ranges estruturais
(ex: `trimestre` 1-4). Esta camada acrescenta checagens de plausibilidade que
o schema não cobre, no princípio de não confiar 100% na saída da LLM: sinaliza
linhas provavelmente vazias/alucinadas ou com valores fora do esperado.

Retorna *warnings* (não bloqueia a persistência) para registro/inspeção.
"""

from datetime import date

from uda.schemas import IndicadorExtraido

# Faixa plausível para variações percentuais; acima disso é suspeito.
LIMIAR_VARIACAO_ABS = 1000.0
ANO_MIN = 2000


def validar_indicadores(indicadores: list[IndicadorExtraido]) -> list[str]:
    """Retorna uma lista de avisos sobre Indicadores suspeitos."""
    avisos: list[str] = []
    ano_max = date.today().year + 1

    for i, ind in enumerate(indicadores):
        rotulo = f"[{i}] {ind.empresa or '?'} / {ind.indicador}"

        if not (ind.empresa or "").strip():
            avisos.append(f"{rotulo}: empresa vazia.")

        variacoes = [ind.var_qoq, ind.var_yoy, ind.var_acumulado_aa]
        if ind.valor_absoluto is None and all(v is None for v in variacoes):
            avisos.append(
                f"{rotulo}: nenhum valor (absoluto/variações) — possível linha vazia."
            )

        for nome, v in (
            ("var_qoq", ind.var_qoq),
            ("var_yoy", ind.var_yoy),
            ("var_acumulado_aa", ind.var_acumulado_aa),
        ):
            if v is not None and abs(v) > LIMIAR_VARIACAO_ABS:
                avisos.append(f"{rotulo}: {nome}={v} fora da faixa plausível.")

        if not (ANO_MIN <= ind.ano <= ano_max):
            avisos.append(f"{rotulo}: ano={ind.ano} fora de [{ANO_MIN}, {ano_max}].")

    return avisos
