"""Contrato Semântico (Pydantic) — ver ADR-0005.

Define o formato que a saída do Gemini deve obedecer ao extrair Indicadores
de uma Prévia Operacional. Campos ausentes na Prévia devem vir como None
(NULL), nunca inventados.
"""

from typing import Literal

from pydantic import BaseModel, Field

Indicador = Literal["lancamentos", "vendas"]


class IndicadorExtraido(BaseModel):
    """Um Indicador (Lançamentos ou Vendas) de uma empresa em um trimestre.

    `empresa = "TOTAL_SETOR"` é usado para os totais agregados do boletim.
    """

    empresa: str
    ano: int
    trimestre: int = Field(ge=1, le=4)
    indicador: Indicador
    valor_absoluto: float | None = None
    var_qoq: float | None = None
    var_yoy: float | None = None
    var_acumulado_aa: float | None = None


class ExtracaoResultado(BaseModel):
    """Lista de Indicadores extraídos de uma Prévia Operacional."""

    indicadores: list[IndicadorExtraido]
