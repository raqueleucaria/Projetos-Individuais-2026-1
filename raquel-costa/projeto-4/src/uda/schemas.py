"""Contrato Semântico (Pydantic) — ver ADR-0005.

Define o formato que a saída do Gemini deve obedecer ao extrair Indicadores
de uma Prévia Operacional. Campos ausentes na Prévia devem vir como None
(NULL), nunca inventados.
"""

from typing import Literal

from pydantic import BaseModel, Field

Indicador = Literal["lancamentos", "vendas"]

# Unidade de `valor_absoluto`. Ver ADR-0007.
Unidade = Literal["R$_milhoes", "unidades", "empreendimentos", "m2"]


class IndicadorExtraido(BaseModel):
    """Um Indicador (Lançamentos ou Vendas) de uma empresa em um trimestre.

    `empresa = "TOTAL_SETOR"` é reservado para totais agregados de várias
    empresas (boletins setoriais). Em documentos de uma única empresa, usa-se o
    nome da própria empresa em todas as linhas.

    `variante` distingue recortes do mesmo indicador (ex: "com_permuta",
    "ex_permuta", "permutas") quando o documento os apresenta; `unidade`
    desambigua `valor_absoluto` (R$ milhões, unidades, empreendimentos, m²).
    Ver ADR-0007.
    """

    empresa: str
    ano: int
    trimestre: int = Field(ge=1, le=4)
    indicador: Indicador
    variante: str | None = None
    unidade: Unidade | None = None
    valor_absoluto: float | None = None
    var_qoq: float | None = None
    var_yoy: float | None = None
    var_acumulado_aa: float | None = None


class ExtracaoResultado(BaseModel):
    """Lista de Indicadores extraídos de uma Prévia Operacional."""

    indicadores: list[IndicadorExtraido]
