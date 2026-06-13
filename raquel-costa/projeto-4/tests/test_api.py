import pytest
from fastapi.testclient import TestClient

from uda import config
from uda.db import get_connection, init_db, registrar_indicadores, registrar_relatorio
from uda.schemas import IndicadorExtraido


@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path = tmp_path / "catalogo.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)

    # uda.db importa DB_PATH no nível de módulo; também precisa ser ajustado.
    from uda import db as db_module

    monkeypatch.setattr(db_module, "DB_PATH", db_path)

    init_db(db_path)
    conn = get_connection(db_path)
    registrar_relatorio(conn, "h" * 64, "https://exemplo.com/previa.pdf", "data/previa.pdf")
    registrar_indicadores(
        conn,
        "h" * 64,
        [
            IndicadorExtraido(empresa="MRV", ano=2025, trimestre=3, indicador="lancamentos", var_qoq=-32.0),
            IndicadorExtraido(empresa="Cury", ano=2025, trimestre=3, indicador="vendas", var_qoq=-15.0),
        ],
    )
    conn.close()

    from uda.api import app

    return TestClient(app)


def test_conjuntura_sem_filtros(client):
    resp = client.get("/api/conjuntura")
    assert resp.status_code == 200
    assert len(resp.json()) == 2


def test_conjuntura_filtra_por_empresa_ano_trimestre(client):
    resp = client.get("/api/conjuntura", params={"empresa": "MRV", "ano": 2025, "trimestre": 3})
    assert resp.status_code == 200
    dados = resp.json()
    assert len(dados) == 1
    assert dados[0]["empresa"] == "MRV"
    assert dados[0]["url_origem"] == "https://exemplo.com/previa.pdf"


def test_conjuntura_sem_resultados(client):
    resp = client.get("/api/conjuntura", params={"empresa": "Inexistente"})
    assert resp.status_code == 200
    assert resp.json() == []
