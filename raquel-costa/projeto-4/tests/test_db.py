from uda.db import (
    consultar_indicadores,
    get_connection,
    init_db,
    registrar_indicadores,
    registrar_relatorio,
    relatorio_existe,
)
from uda.schemas import IndicadorExtraido


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


def test_registrar_e_consultar_indicadores(tmp_path):
    db_path = tmp_path / "catalogo.db"
    init_db(db_path)
    conn = get_connection(db_path)

    hash_pdf = "b" * 64
    registrar_relatorio(conn, hash_pdf, "https://exemplo.com/previa.pdf", "data/previa.pdf")

    registrar_indicadores(
        conn,
        hash_pdf,
        [
            IndicadorExtraido(
                empresa="MRV",
                ano=2025,
                trimestre=3,
                indicador="lancamentos",
                var_qoq=-32.0,
                var_yoy=-19.0,
                var_acumulado_aa=20.0,
            ),
            IndicadorExtraido(
                empresa="Cury",
                ano=2025,
                trimestre=3,
                indicador="vendas",
                var_qoq=-15.0,
            ),
        ],
    )

    todos = consultar_indicadores(conn)
    assert len(todos) == 2

    so_mrv = consultar_indicadores(conn, empresa="MRV")
    assert len(so_mrv) == 1
    assert so_mrv[0]["empresa"] == "MRV"
    assert so_mrv[0]["valor_absoluto"] is None
    assert so_mrv[0]["url_origem"] == "https://exemplo.com/previa.pdf"

    nenhum = consultar_indicadores(conn, empresa="Tenda")
    assert nenhum == []

    conn.close()


def test_registrar_e_consultar_variante_unidade(tmp_path):
    db_path = tmp_path / "catalogo.db"
    init_db(db_path)
    conn = get_connection(db_path)

    hash_pdf = "c" * 64
    registrar_relatorio(conn, hash_pdf, "https://exemplo.com/cyrela.pdf", "data/cyrela.pdf")
    registrar_indicadores(
        conn,
        hash_pdf,
        [
            IndicadorExtraido(
                empresa="Cyrela", ano=2025, trimestre=3, indicador="lancamentos",
                variante="com_permuta", unidade="R$_milhoes", valor_absoluto=5050.0,
            ),
            IndicadorExtraido(
                empresa="Cyrela", ano=2025, trimestre=3, indicador="lancamentos",
                variante="ex_permuta", unidade="R$_milhoes", valor_absoluto=3411.0,
            ),
        ],
    )

    ex = consultar_indicadores(conn, empresa="Cyrela", variante="ex_permuta")
    assert len(ex) == 1
    assert ex[0]["valor_absoluto"] == 3411.0
    assert ex[0]["unidade"] == "R$_milhoes"

    em_rs = consultar_indicadores(conn, unidade="R$_milhoes")
    assert len(em_rs) == 2

    conn.close()
