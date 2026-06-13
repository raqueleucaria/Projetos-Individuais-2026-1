"""Orquestração do pipeline: hash/idempotência -> pré-filtro -> extração ->
persistência (Catálogo de Dados).

Ver ADR-0001 (pré-filtro), ADR-0002/0005 (extração via Gemini + contrato),
ADR-0003 (idempotência), ADR-0004 (modelo de dados).
"""

from pathlib import Path

from uda.db import (
    get_connection,
    init_db,
    registrar_indicadores,
    registrar_relatorio,
    relatorio_existe,
)
from uda.extraction import extrair_indicadores
from uda.hashing import hash_arquivo
from uda.prefilter import pre_filtrar


def processar_pdf(caminho_pdf: Path | str, url_origem: str = "") -> str:
    """Processa uma Prévia Operacional, respeitando a Idempotência.

    Retorna "ignorado" se o PDF já havia sido processado, ou "processado"
    caso tenha sido extraído e persistido agora.
    """
    init_db()
    conn = get_connection()
    try:
        hash_pdf = hash_arquivo(caminho_pdf)

        if relatorio_existe(conn, hash_pdf):
            return "ignorado"

        texto_paginas = pre_filtrar(caminho_pdf)
        resultado = extrair_indicadores(texto_paginas)

        registrar_relatorio(conn, hash_pdf, url_origem, str(caminho_pdf))
        registrar_indicadores(conn, hash_pdf, resultado.indicadores)

        return "processado"
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    from uda.config import DATA_DIR

    caminho = sys.argv[1] if len(sys.argv) > 1 else DATA_DIR / "exemplo_Boletim_Conjuntura_2025_3T.pdf"
    status = processar_pdf(
        caminho,
        url_origem="https://github.com/unb-Sistemas-de-Machine-learning/Projetos-Individuais-2026-1/blob/main/projeto-individual-4/exemplo_Boletim_Conjuntura_2025_3T.pdf",
    )
    print(f"{caminho}: {status}")
