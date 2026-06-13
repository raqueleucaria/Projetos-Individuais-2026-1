"""Orquestração do pipeline: hash/idempotência -> pré-filtro -> extração ->
validação -> persistência (Catálogo de Dados).

Ver ADR-0001 (pré-filtro), ADR-0002/0005 (extração via Gemini + contrato),
ADR-0003 (idempotência), ADR-0004 (modelo de dados), ADR-0006 (fallback Vision
para PDFs escaneados).
"""

import logging
from pathlib import Path

from uda.db import (
    get_connection,
    init_db,
    registrar_indicadores,
    registrar_relatorio,
    relatorio_existe,
)
from uda.extraction import extrair_indicadores, extrair_indicadores_vision
from uda.hashing import hash_arquivo
from uda.prefilter import pre_filtrar, tem_camada_de_texto
from uda.validation import validar_indicadores

logger = logging.getLogger(__name__)


def processar_pdf(caminho_pdf: Path | str, url_origem: str = "") -> str:
    """Processa uma Prévia Operacional, respeitando a Idempotência.

    Retorna "ignorado" se o PDF já havia sido processado, ou "processado"
    caso tenha sido extraído e persistido agora.

    Se o PDF não tem camada de texto (escaneado), recorre ao Gemini Vision
    (ADR-0006). Após a extração, roda a validação semântica e registra avisos.
    """
    init_db()
    conn = get_connection()
    try:
        hash_pdf = hash_arquivo(caminho_pdf)

        if relatorio_existe(conn, hash_pdf):
            return "ignorado"

        if tem_camada_de_texto(caminho_pdf):
            conteudo = pre_filtrar(caminho_pdf)
            resultado = extrair_indicadores(conteudo)
        else:
            logger.info("PDF sem camada de texto — usando Gemini Vision: %s", caminho_pdf)
            resultado = extrair_indicadores_vision(caminho_pdf)

        for aviso in validar_indicadores(resultado.indicadores):
            logger.warning("Validação: %s", aviso)

        registrar_relatorio(conn, hash_pdf, url_origem, str(caminho_pdf))
        registrar_indicadores(conn, hash_pdf, resultado.indicadores)

        return "processado"
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    from uda.config import DATA_DIR

    logging.basicConfig(level=logging.INFO)
    caminho = sys.argv[1] if len(sys.argv) > 1 else DATA_DIR / "exemplo_Boletim_Conjuntura_2025_3T.pdf"
    status = processar_pdf(
        caminho,
        url_origem="https://github.com/unb-Sistemas-de-Machine-learning/Projetos-Individuais-2026-1/blob/main/projeto-individual-4/exemplo_Boletim_Conjuntura_2025_3T.pdf",
    )
    print(f"{caminho}: {status}")
