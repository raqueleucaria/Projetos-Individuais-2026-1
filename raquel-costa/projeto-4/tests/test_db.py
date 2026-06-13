from uda.db import get_connection, init_db, registrar_relatorio, relatorio_existe


def test_init_db_cria_tabelas(tmp_path):
    db_path = tmp_path / "catalogo.db"
    init_db(db_path)

    conn = get_connection(db_path)
    tabelas = {
        row["name"]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    }
    conn.close()

    assert "relatorios" in tabelas
    assert "indicadores" in tabelas


def test_idempotencia_relatorio_existe(tmp_path):
    db_path = tmp_path / "catalogo.db"
    init_db(db_path)
    conn = get_connection(db_path)

    hash_pdf = "a" * 64
    assert relatorio_existe(conn, hash_pdf) is False

    registrar_relatorio(conn, hash_pdf, "https://exemplo.com/previa.pdf", "data/previa.pdf")

    assert relatorio_existe(conn, hash_pdf) is True
    conn.close()


def test_indicadores_referenciam_relatorio(tmp_path):
    db_path = tmp_path / "catalogo.db"
    init_db(db_path)
    conn = get_connection(db_path)

    hash_pdf = "b" * 64
    registrar_relatorio(conn, hash_pdf, "https://exemplo.com/previa.pdf", "data/previa.pdf")

    conn.execute(
        """
        INSERT INTO indicadores
            (relatorio_hash, empresa, ano, trimestre, indicador, valor_absoluto, var_qoq, var_yoy, var_acumulado_aa)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (hash_pdf, "MRV", 2025, 3, "lancamentos", None, -32.0, -19.0, 20.0),
    )
    conn.commit()

    row = conn.execute(
        "SELECT * FROM indicadores WHERE relatorio_hash = ?", (hash_pdf,)
    ).fetchone()
    conn.close()

    assert row["empresa"] == "MRV"
    assert row["valor_absoluto"] is None
    assert row["var_qoq"] == -32.0
