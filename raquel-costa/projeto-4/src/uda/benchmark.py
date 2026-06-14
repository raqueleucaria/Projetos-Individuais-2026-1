"""Benchmark de qualidade da extração — golden dataset + métricas.

Mede a qualidade da leitura do pipeline comparando a extração contra uma
verdade-base (golden), com métricas mapeadas aos critérios de avaliação:

- `disciplina_null`  -> "tratar valores ausentes como NULL" (não alucinar).
- `cobertura`        -> recall: achou as linhas esperadas.
- `precisao`         -> não inventou linhas a mais.
- `acuracia_numerica`-> variações/absolutos corretos (com tolerância).
- `consistencia_temporal` -> ano/trimestre corretos.

As funções de métrica são puras e determinísticas (testáveis sem LLM). O
`__main__` roda o pipeline real sobre os PDFs disponíveis e imprime o relatório.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from uda.config import BASE_DIR

GOLDEN_DIR = BASE_DIR / "benchmark" / "golden"
SNAPSHOT_DIR = BASE_DIR / "benchmark" / "snapshots"
CAMPOS_PERCENTUAIS = ("var_qoq", "var_yoy", "var_acumulado_aa")
TOL_PP = 0.5      # tolerância em pontos percentuais para variações
TOL_REL = 0.01    # tolerância relativa (1%) para valor_absoluto


# ─────────────────────────────────────────────────────────────────────────
# Normalização e casamento de linhas
# ─────────────────────────────────────────────────────────────────────────

def _to_dict(ind) -> dict:
    return ind.model_dump() if hasattr(ind, "model_dump") else dict(ind)


def _norm_empresa(s: str | None) -> str:
    return (s or "").strip().lower()


def chave(ind: dict) -> tuple:
    """Chave lógica de uma linha: (empresa, indicador, variante)."""
    return (_norm_empresa(ind.get("empresa")), ind.get("indicador"), ind.get("variante") or None)


def _num_ok(esperado, extraido, tol_abs: float | None = None, tol_rel: float | None = None) -> bool:
    if esperado is None:
        return extraido is None
    if extraido is None:
        return False
    if tol_rel is not None:
        return abs(extraido - esperado) <= max(abs(esperado) * tol_rel, 1e-9)
    return abs(extraido - esperado) <= (tol_abs if tol_abs is not None else 0)


# ─────────────────────────────────────────────────────────────────────────
# Métricas
# ─────────────────────────────────────────────────────────────────────────

@dataclass
class Metricas:
    n_esperado: int
    n_extraido: int
    cobertura: float            # recall = casadas / esperadas
    precisao: float             # casadas / extraídas
    acuracia_numerica: float    # campos numéricos corretos / comparados
    disciplina_null: float      # campos NULL esperados que vieram NULL / total
    consistencia_temporal: float  # linhas casadas com ano/trimestre corretos
    faltantes: list             # chaves esperadas não extraídas
    extras: list                # chaves extraídas não esperadas


def avaliar(esperado: list[dict], extraido: list) -> Metricas:
    """Compara a extração contra a verdade-base e devolve as métricas."""
    extraido = [_to_dict(i) for i in extraido]
    by_exp = {chave(e): e for e in esperado}
    by_ext = {chave(x): x for x in extraido}

    casadas = [k for k in by_exp if k in by_ext]
    faltantes = [k for k in by_exp if k not in by_ext]
    extras = [k for k in by_ext if k not in by_exp]

    num_ok = num_tot = 0
    null_ok = null_tot = 0
    temp_ok = 0

    for k in casadas:
        e, x = by_exp[k], by_ext[k]

        for campo in CAMPOS_PERCENTUAIS:
            num_tot += 1
            if _num_ok(e.get(campo), x.get(campo), tol_abs=TOL_PP):
                num_ok += 1
        # valor_absoluto: tolerância relativa quando esperado != None
        num_tot += 1
        if _num_ok(e.get("valor_absoluto"), x.get("valor_absoluto"), tol_rel=TOL_REL):
            num_ok += 1

        # disciplina de NULL: campos esperados como None devem vir None
        for campo in ("valor_absoluto", *CAMPOS_PERCENTUAIS):
            if e.get(campo) is None:
                null_tot += 1
                if x.get(campo) is None:
                    null_ok += 1

        if x.get("ano") == e.get("ano") and x.get("trimestre") == e.get("trimestre"):
            temp_ok += 1

    n_exp, n_ext, n_cas = len(esperado), len(extraido), len(casadas)
    return Metricas(
        n_esperado=n_exp,
        n_extraido=n_ext,
        cobertura=n_cas / n_exp if n_exp else 0.0,
        precisao=n_cas / n_ext if n_ext else 0.0,
        acuracia_numerica=num_ok / num_tot if num_tot else 1.0,
        disciplina_null=null_ok / null_tot if null_tot else 1.0,
        consistencia_temporal=temp_ok / n_cas if n_cas else 1.0,
        faltantes=faltantes,
        extras=extras,
    )


# ─────────────────────────────────────────────────────────────────────────
# Golden dataset
# ─────────────────────────────────────────────────────────────────────────

def carregar_golden(nome: str) -> dict:
    return json.loads((GOLDEN_DIR / f"{nome}.json").read_text(encoding="utf-8"))


def carregar_snapshot(nome: str) -> list[dict]:
    """Carrega um snapshot gravado de extração real (para asserts offline)."""
    return json.loads((SNAPSHOT_DIR / f"{nome}.json").read_text(encoding="utf-8"))


def listar_golden() -> list[str]:
    return sorted(p.stem for p in GOLDEN_DIR.glob("*.json"))


def resolver_pdf(golden: dict, baixar: bool = True) -> Path | None:
    """Resolve o PDF de uma entrada golden: caminho versionado ou download.

    Retorna o Path do PDF, ou None se indisponível (ex: sem o arquivo local e
    sem rede para baixar) — nesse caso a entrada deve ser pulada.
    """
    if golden.get("pdf_path"):
        p = (BASE_DIR / golden["pdf_path"]).resolve()
        if p.exists():
            return p
    url = golden.get("pdf_url")
    if url and baixar:
        import tempfile
        import urllib.request

        destino = Path(tempfile.gettempdir()) / f"golden_{golden['nome']}.pdf"
        if not destino.exists():
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Accept": "application/pdf,*/*",
                    "Referer": "https://api.mziq.com/",
                },
            )
            with urllib.request.urlopen(req) as r:  # noqa: S310
                dados = r.read()
            if not dados.startswith(b"%PDF"):
                return None
            destino.write_bytes(dados)
        return destino
    return None


# ─────────────────────────────────────────────────────────────────────────
# Relatório
# ─────────────────────────────────────────────────────────────────────────

def _pct(x: float) -> str:
    return f"{x * 100:.0f}%"


def relatorio_markdown(resultados: dict[str, Metricas]) -> str:
    linhas = [
        "| PDF | esperadas | extraídas | cobertura | precisão | acur. num. | disc. NULL | temporal |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for nome, m in resultados.items():
        linhas.append(
            f"| {nome} | {m.n_esperado} | {m.n_extraido} | {_pct(m.cobertura)} | "
            f"{_pct(m.precisao)} | {_pct(m.acuracia_numerica)} | {_pct(m.disciplina_null)} | "
            f"{_pct(m.consistencia_temporal)} |"
        )
    return "\n".join(linhas)


def extrair_de_pdf(caminho_pdf) -> list:
    """Roda a extração do pipeline sobre um PDF (texto ou Vision), sem persistir."""
    from uda.extraction import extrair_indicadores, extrair_indicadores_vision
    from uda.prefilter import pre_filtrar, tem_camada_de_texto

    if tem_camada_de_texto(caminho_pdf):
        return extrair_indicadores(pre_filtrar(caminho_pdf)).indicadores
    return extrair_indicadores_vision(caminho_pdf).indicadores


def rodar_benchmark(nomes: list[str] | None = None) -> dict[str, Metricas]:
    resultados: dict[str, Metricas] = {}
    for nome in nomes or listar_golden():
        golden = carregar_golden(nome)
        pdf = resolver_pdf(golden)
        if pdf is None:
            print(f"[skip] {nome}: PDF indisponível (sem arquivo local nem download)")
            continue
        extraido = extrair_de_pdf(pdf)
        resultados[nome] = avaliar(golden["esperado"], extraido)
    return resultados


if __name__ == "__main__":
    res = rodar_benchmark()
    if res:
        print(relatorio_markdown(res))
        for nome, m in res.items():
            if m.faltantes or m.extras:
                print(f"\n{nome}: faltantes={m.faltantes} extras={m.extras}")
