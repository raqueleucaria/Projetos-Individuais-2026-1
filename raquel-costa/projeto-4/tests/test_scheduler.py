"""Testes do agendador de ingestão (sem rede nem LLM)."""

import uda.scheduler as scheduler


def test_carregar_fontes_le_urls_diretas(tmp_path):
    p = tmp_path / "sources.yaml"
    p.write_text("fontes:\n  - https://x/a.pdf\n  - https://x/b.pdf\nindices: []\n")
    assert scheduler.carregar_fontes(p) == ["https://x/a.pdf", "https://x/b.pdf"]


def test_carregar_fontes_descobre_em_indices(tmp_path, monkeypatch):
    p = tmp_path / "sources.yaml"
    p.write_text("fontes: []\nindices:\n  - https://ri.exemplo.com/resultados\n")
    monkeypatch.setattr(scheduler, "descobrir_pdfs", lambda url: ["https://ri.exemplo.com/x.pdf"])
    assert scheduler.carregar_fontes(p) == ["https://ri.exemplo.com/x.pdf"]


def test_rodar_executa_n_ciclos_e_dorme_entre_eles(monkeypatch):
    contagem = {"ciclos": 0, "sleeps": 0}
    monkeypatch.setattr(scheduler, "carregar_fontes", lambda: ["https://x/a.pdf"])
    monkeypatch.setattr(
        scheduler, "coletar",
        lambda fontes: contagem.__setitem__("ciclos", contagem["ciclos"] + 1) or {},
    )

    n = scheduler.rodar(
        0.0, max_ciclos=3,
        sleep=lambda s: contagem.__setitem__("sleeps", contagem["sleeps"] + 1),
    )

    assert n == 3
    assert contagem["ciclos"] == 3
    assert contagem["sleeps"] == 2  # dorme entre ciclos, não após o último


def test_sources_yaml_do_projeto_e_valido():
    fontes = scheduler.carregar_fontes()  # usa config/sources.yaml versionado
    assert isinstance(fontes, list)
    assert all(isinstance(f, str) for f in fontes)
