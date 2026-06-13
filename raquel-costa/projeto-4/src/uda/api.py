"""Camada de Serviço (API REST) — GET /api/conjuntura.

Consulta os Indicadores persistidos no Catálogo de Dados, com filtros
opcionais por empresa/ano/trimestre e a Linhagem (url_origem) de cada item.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from uda.db import consultar_indicadores, get_connection, init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Conjuntura do Setor Habitacional", lifespan=lifespan)


@app.get("/api/conjuntura")
def conjuntura(
    empresa: str | None = None,
    ano: int | None = None,
    trimestre: int | None = None,
    variante: str | None = None,
    unidade: str | None = None,
) -> list[dict]:
    conn = get_connection()
    try:
        rows = consultar_indicadores(
            conn,
            empresa=empresa,
            ano=ano,
            trimestre=trimestre,
            variante=variante,
            unidade=unidade,
        )
        return [dict(row) for row in rows]
    finally:
        conn.close()
