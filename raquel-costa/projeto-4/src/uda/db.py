"""Catálogo de Dados (SQLite) — schema e helpers de conexão.

Ver ADR-0003 (idempotência via SHA-256) e ADR-0004 (modelo de dados:
uma linha por (empresa, ano, trimestre, indicador)).
"""

import sqlite3
from pathlib import Path

from uda.config import DB_PATH

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


def get_connection(db_path: Path | str = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Path | str = DB_PATH) -> None:
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


if __name__ == "__main__":
    init_db()
    print(f"Catálogo de Dados inicializado em {DB_PATH}")
