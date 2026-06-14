"""Testes do coletor de ingestão (sem rede nem LLM)."""

import uda.coletor as coletor

HTML_RI = """
<html><body>
  <h1>Central de Resultados 2025</h1>
  <ul>
    <li><a href="/docs/previa-operacional-3T25.pdf">Prévia Operacional 3T25</a></li>
    <li><a href="https://ri.exemplo.com/files/release-3T25.pdf?v=2">Release 3T25</a></li>
    <li><a href="/docs/previa-operacional-3T25.pdf">duplicado</a></li>
    <li><a href="/apresentacao.pptx">Apresentação</a></li>
  </ul>
</body></html>
"""


def test_extrair_links_pdf_resolve_e_deduplica():
    links = coletor.extrair_links_pdf(HTML_RI, base_url="https://ri.exemplo.com/resultados")
    assert links == [
        "https://ri.exemplo.com/docs/previa-operacional-3T25.pdf",
        "https://ri.exemplo.com/files/release-3T25.pdf?v=2",
    ]


def test_coletar_repassa_status_do_pipeline(tmp_path, monkeypatch):
    # baixar_pdf não toca a rede; processar_pdf não toca o LLM.
    monkeypatch.setattr(coletor, "baixar_pdf", lambda url, destino=None: tmp_path / "x.pdf")

    chamadas = {"n": 0}

    def fake_processar(pdf, url_origem=""):
        chamadas["n"] += 1
        return "processado" if chamadas["n"] == 1 else "ignorado"

    monkeypatch.setattr(coletor, "processar_pdf", fake_processar)

    url = "https://ri.exemplo.com/previa.pdf"
    resumo = coletor.coletar([url, url])  # mesma fonte 2x
    assert resumo[url] == "ignorado"  # 2ª passada (idempotência do pipeline)
    assert chamadas["n"] == 2


def test_coletar_marca_falha_download(monkeypatch):
    monkeypatch.setattr(coletor, "baixar_pdf", lambda url, destino=None: None)
    resumo = coletor.coletar(["https://ri.exemplo.com/nao-e-pdf"])
    assert resumo["https://ri.exemplo.com/nao-e-pdf"] == "falha_download"


def test_coletar_trata_excecao_de_rede(monkeypatch):
    def explode(url, destino=None):
        raise OSError("conexão recusada")

    monkeypatch.setattr(coletor, "baixar_pdf", explode)
    resumo = coletor.coletar(["https://ri.exemplo.com/timeout.pdf"])
    assert resumo["https://ri.exemplo.com/timeout.pdf"] == "falha_download"
