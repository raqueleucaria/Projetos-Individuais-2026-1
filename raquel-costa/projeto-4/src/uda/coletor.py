"""Coletor de ingestão — dispara o pipeline a partir de fontes de RI.

Implementa o gatilho de ingestão orientado a eventos (enunciado, seção A), em
dois níveis:

- **Nível 1 — coleta a partir de fontes (`coletar`)**: dada uma lista de URLs de
  PDFs de Prévias Operacionais, baixa cada um e chama `processar_pdf`, que
  garante a **idempotência** (hash SHA-256 — ADR-0003): um PDF já processado é
  ignorado sem custo de LLM. É o caminho automatizável (polling/cron) sobre uma
  lista de fontes conhecidas.

- **Descoberta (nível 2) — `extrair_links_pdf`**: dada a página de uma Central
  de Resultados servida como HTML estático, encontra os links de PDF. Portais
  de RI que carregam a lista via JavaScript ou usam links sem extensão `.pdf`
  (ex: filemanager) exigem um adaptador por portal — ver `ingestao-polling.md`.

Ver [`docs/planning/ingestao-polling.md`](../../docs/planning/ingestao-polling.md).
"""

from __future__ import annotations

import logging
import re
import tempfile
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

from uda.pipeline import processar_pdf

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/pdf,text/html,*/*",
    "Referer": "https://www.google.com/",
}


def baixar_pdf(url: str, destino: Path | None = None) -> Path | None:
    """Baixa o PDF da URL. Retorna o Path local, ou None se não for um PDF."""
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req) as resp:  # noqa: S310
        dados = resp.read()
    if not dados.startswith(b"%PDF"):
        logger.warning("Conteúdo de %s não é um PDF — ignorando", url)
        return None
    destino = destino or (Path(tempfile.gettempdir()) / f"coletor_{abs(hash(url))}.pdf")
    destino.write_bytes(dados)
    return destino


def baixar_html(url: str) -> str:
    """Baixa o HTML de uma página (ex: Central de Resultados)."""
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req) as resp:  # noqa: S310
        return resp.read().decode("utf-8", errors="replace")


def extrair_links_pdf(html: str, base_url: str = "") -> list[str]:
    """Descoberta: extrai links de PDF de um HTML, resolvendo URLs relativas.

    Pega `href`/`src` terminados em `.pdf` (com query opcional). Mantém a ordem
    e remove duplicatas.
    """
    achados = re.findall(r'(?:href|src)=["\']([^"\']+\.pdf(?:\?[^"\']*)?)["\']', html, flags=re.I)
    return [urljoin(base_url, link) for link in dict.fromkeys(achados)]


def descobrir_pdfs(url_indice: str) -> list[str]:
    """Baixa a página de índice (RI) e descobre os links de PDF nela."""
    return extrair_links_pdf(baixar_html(url_indice), base_url=url_indice)


def coletar(fontes: list[str]) -> dict[str, str]:
    """Baixa e processa cada fonte (URL de PDF), de forma idempotente.

    Retorna um resumo {url: status}, onde status ∈ {"processado", "ignorado",
    "falha_download"}.
    """
    resumo: dict[str, str] = {}
    for url in fontes:
        try:
            pdf = baixar_pdf(url)
        except Exception as e:  # rede instável, 4xx/5xx, etc.
            logger.error("Falha ao baixar %s: %s", url, e)
            resumo[url] = "falha_download"
            continue
        if pdf is None:
            resumo[url] = "falha_download"
            continue
        resumo[url] = processar_pdf(pdf, url_origem=url)
        logger.info("%s -> %s", url, resumo[url])
    return resumo


if __name__ == "__main__":
    import sys

    logging.basicConfig(level=logging.INFO)
    fontes = sys.argv[1:]
    if not fontes:
        print("uso: python -m uda.coletor <url_pdf> [<url_pdf> ...]")
        raise SystemExit(2)
    for url, status in coletar(fontes).items():
        print(f"{status}\t{url}")
