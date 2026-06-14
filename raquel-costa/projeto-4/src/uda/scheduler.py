"""Agendador de ingestão — observação contínua das fontes (enunciado, seção A).

Roda o coletor (`coletar`) sobre as fontes configuradas em
`config/sources.yaml` a cada `intervalo` segundos (ex: 1×/dia). A idempotência
(hash SHA-256) garante que documentos já processados sejam ignorados, então
ciclos repetidos não reprocessam nem geram custo de LLM.

Fontes:
- `fontes`: lista de URLs de PDFs de Prévias Operacionais (caminho direto).
- `indices`: páginas de Central de Resultados (HTML estático) das quais os
  links de PDF são descobertos (`descobrir_pdfs`).
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

import yaml

from uda.coletor import coletar, descobrir_pdfs
from uda.config import BASE_DIR

SOURCES_PATH = BASE_DIR / "config" / "sources.yaml"
logger = logging.getLogger(__name__)


def carregar_fontes(path: Path | str = SOURCES_PATH) -> list[str]:
    """Lê as fontes do `sources.yaml` (URLs diretas + descoberta em índices)."""
    cfg = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    fontes: list[str] = list(cfg.get("fontes") or [])
    for indice in cfg.get("indices") or []:
        try:
            fontes.extend(descobrir_pdfs(indice))
        except Exception as e:
            logger.warning("Falha ao descobrir PDFs em %s: %s", indice, e)
    return fontes


def ciclo() -> dict[str, str]:
    """Um ciclo de ingestão: carrega as fontes e dispara o coletor."""
    fontes = carregar_fontes()
    logger.info("Ciclo de ingestão: %d fonte(s)", len(fontes))
    return coletar(fontes)


def rodar(intervalo_seg: float, max_ciclos: int | None = None, sleep=time.sleep) -> int:
    """Executa ciclos de ingestão em intervalo.

    `max_ciclos=None` roda indefinidamente (uso em produção). Retorna o número
    de ciclos executados.
    """
    n = 0
    while max_ciclos is None or n < max_ciclos:
        ciclo()
        n += 1
        if max_ciclos is None or n < max_ciclos:
            sleep(intervalo_seg)
    return n


if __name__ == "__main__":
    import os

    logging.basicConfig(level=logging.INFO)
    intervalo = float(os.environ.get("SCHEDULER_INTERVALO_SEG", "86400"))  # 1x/dia
    logger.info("Scheduler iniciado (intervalo=%ss). Ctrl+C para parar.", intervalo)
    rodar(intervalo)
