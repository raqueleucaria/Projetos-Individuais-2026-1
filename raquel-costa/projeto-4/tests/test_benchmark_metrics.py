"""Testes determinísticos das métricas de benchmark (sem LLM).

Garantem que o *medidor* de qualidade está correto, usando dados sintéticos —
não chamam a API. O gate e2e real (que chama o Gemini) é opt-in e fica fora do
pytest padrão.
"""

from uda.benchmark import avaliar, carregar_golden

ESPERADO = [
    {"empresa": "MRV", "ano": 2025, "trimestre": 3, "indicador": "lancamentos",
     "variante": None, "valor_absoluto": None, "var_qoq": -32, "var_yoy": -19, "var_acumulado_aa": 20},
    {"empresa": "Cury", "ano": 2025, "trimestre": 3, "indicador": "vendas",
     "variante": None, "valor_absoluto": None, "var_qoq": -15, "var_yoy": 32, "var_acumulado_aa": 27},
]


def _clone(rows):
    return [dict(r) for r in rows]


def test_extracao_perfeita_pontua_tudo():
    m = avaliar(ESPERADO, _clone(ESPERADO))
    assert m.cobertura == 1.0
    assert m.precisao == 1.0
    assert m.acuracia_numerica == 1.0
    assert m.disciplina_null == 1.0
    assert m.consistencia_temporal == 1.0
    assert m.faltantes == [] and m.extras == []


def test_tolerancia_numerica_em_pp():
    extr = _clone(ESPERADO)
    extr[0]["var_qoq"] = -32.4  # dentro de TOL_PP (0.5)
    assert avaliar(ESPERADO, extr).acuracia_numerica == 1.0
    extr[0]["var_qoq"] = -30.0  # fora da tolerância
    assert avaliar(ESPERADO, extr).acuracia_numerica < 1.0


def test_linha_faltante_reduz_cobertura():
    m = avaliar(ESPERADO, _clone(ESPERADO)[:1])
    assert m.cobertura == 0.5
    assert len(m.faltantes) == 1


def test_linha_extra_reduz_precisao():
    extr = _clone(ESPERADO) + [
        {"empresa": "Fantasma", "ano": 2025, "trimestre": 3, "indicador": "vendas",
         "variante": None, "valor_absoluto": None, "var_qoq": 1}
    ]
    m = avaliar(ESPERADO, extr)
    assert m.precisao < 1.0
    assert len(m.extras) == 1


def test_valor_inventado_quebra_disciplina_null():
    extr = _clone(ESPERADO)
    extr[0]["valor_absoluto"] = 999.0  # esperado era None -> alucinação
    m = avaliar(ESPERADO, extr)
    assert m.disciplina_null < 1.0


def test_trimestre_errado_quebra_consistencia_temporal():
    extr = _clone(ESPERADO)
    extr[0]["trimestre"] = 2
    # chave usa indicador/empresa/variante, não trimestre -> linha ainda casa
    m = avaliar(ESPERADO, extr)
    assert m.consistencia_temporal < 1.0


def test_golden_boletim_e_valido():
    golden = carregar_golden("boletim_3T25")
    assert len(golden["esperado"]) == 14
    assert all(item["valor_absoluto"] is None for item in golden["esperado"])
