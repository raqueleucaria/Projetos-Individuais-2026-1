"""Catálogo de Dados (SQLite) — schema e helpers de conexão.

Ver ADR-0003 (idempotência via SHA-256) e ADR-0004 (modelo de dados:
uma linha por (empresa, ano, trimestre, indicador)).
"""

import sqlite3
from pathlib import Path

from uda.config import DB_PATH
from uda.schemas import IndicadorExtraido

SCHEMA = """
CREATE TABLE IF NOT EXISTS relatorios (
    hash TEXT PRIMARY KEY,
    url_origem TEXT,
    arquivo_local TEXT,
    data_processamento TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS indicadores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    relatorio_hash TEXT NOT NULL REFERENCES relatorios(hash),
    empresa TEXT NOT NULL,
    ano INTEGER NOT NULL,
    trimestre INTEGER NOT NULL,
    indicador TEXT NOT NULL,
    valor_absoluto REAL,
    var_qoq REAL,
    var_yoy REAL,
    var_acumulado_aa REAL
);
"""


def get_connection(db_path: Path | str | None = None) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path if db_path is not None else DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str | None = None) -> None:
    conn = get_connection(db_path)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()


def relatorio_existe(conn: sqlite3.Connection, hash_pdf: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM relatorios WHERE hash = ?", (hash_pdf,)
    ).fetchone()
    return row is not None


def registrar_relatorio(
    conn: sqlite3.Connection, hash_pdf: str, url_origem: str, arquivo_local: str
) -> None:
    conn.execute(
        "INSERT INTO relatorios (hash, url_origem, arquivo_local) VALUES (?, ?, ?)",
        (hash_pdf, url_origem, arquivo_local),
    )
    conn.commit()


def registrar_indicadores(
    conn: sqlite3.Connection, hash_pdf: str, indicadores: list[IndicadorExtraido]
) -> None:
    conn.executemany(
        """
        INSERT INTO indicadores
            (relatorio_hash, empresa, ano, trimestre, indicador, valor_absoluto, var_qoq, var_yoy, var_acumulado_aa)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                hash_pdf,
                item.empresa,
                item.ano,
                item.trimestre,
                item.indicador,
                item.valor_absoluto,
                item.var_qoq,
                item.var_yoy,
                item.var_acumulado_aa,
            )
            for item in indicadores
        ],
    )
    conn.commit()


def consultar_indicadores(
    conn: sqlite3.Connection,
    empresa: str | None = None,
    ano: int | None = None,
    trimestre: int | None = None,
) -> list[sqlite3.Row]:
    query = """
        SELECT i.*, r.url_origem
        FROM indicadores i
        JOIN relatorios r ON r.hash = i.relatorio_hash
        WHERE 1=1
    """
    params: list = []
    if empresa is not None:
        query += " AND i.empresa = ?"
        params.append(empresa)
    if ano is not None:
        query += " AND i.ano = ?"
        params.append(ano)
    if trimestre is not None:
        query += " AND i.trimestre = ?"
        params.append(trimestre)

    return conn.execute(query, params).fetchall()


if __name__ == "__main__":
    init_db()
    print(f"Catálogo de Dados inicializado em {DB_PATH}")
