"""Asserts de qualidade da leitura, SEPARADOS POR PDF (offline).

Cada PDF tem seu próprio bloco de asserts, comparando a verdade-base (golden)
com um snapshot gravado de extração real (`benchmark/snapshots/`). Assim:

- **boletim_3T25** (`fonte: data`): PDF versionado em `data/` — também roda no
  benchmark ao vivo; aqui o snapshot garante o assert offline no CI.
- **cyrela_3T25** (`fonte: externo`): PDF de terceiros que **não está em
  `data/`** — o snapshot torna a qualidade testável no CI sem precisar do PDF.

Os asserts não chamam a API: usam o snapshot. A deriva do LLM ao vivo é
verificada à parte rodando `python -m uda.benchmark`.
"""

from uda.benchmark import avaliar, carregar_golden, carregar_snapshot


def _avaliar(nome):
    golden = carregar_golden(nome)
    return golden, avaliar(golden["esperado"], carregar_snapshot(nome))


# ── PDF 1: boletim (fonte: data, versionado) ────────────────────────────────

def test_boletim_data_qualidade_total():
    golden, m = _avaliar("boletim_3T25")
    assert golden["fonte"] == "data"
    assert m.cobertura == 1.0          # achou as 14 linhas
    assert m.precisao == 1.0           # sem linhas a mais
    assert m.acuracia_numerica == 1.0  # percentuais corretos
    assert m.disciplina_null == 1.0    # não inventou absolutos (todos NULL)
    assert m.consistencia_temporal == 1.0


# ── PDF 2: cyrela (fonte: externo, NÃO está em data/) ───────────────────────

def test_cyrela_externo_extrai_absolutos():
    golden, m = _avaliar("cyrela_3T25")
    assert golden["fonte"] == "externo"
    assert m.cobertura == 1.0          # achou os 3 âncoras de valor absoluto
    assert m.acuracia_numerica == 1.0  # absolutos/variações dentro da tolerância
    assert m.disciplina_null == 1.0
    # critério "extração de valores absolutos": todo esperado tem absoluto > 0
    snap = {(r["empresa"], r["indicador"], r.get("variante")): r
            for r in carregar_snapshot("cyrela_3T25")}
    for esp in golden["esperado"]:
        achado = snap[(esp["empresa"], esp["indicador"], esp.get("variante"))]
        assert achado["valor_absoluto"] and achado["valor_absoluto"] > 0
        assert achado["unidade"] == "R$_milhoes"
