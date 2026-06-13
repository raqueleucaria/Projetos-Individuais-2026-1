import pytest
from pydantic import ValidationError

from uda.schemas import ExtracaoResultado, IndicadorExtraido


def test_indicador_aceita_campos_ausentes_como_none():
    item = IndicadorExtraido(
        empresa="MRV",
        ano=2025,
        trimestre=3,
        indicador="lancamentos",
    )
    assert item.valor_absoluto is None
    assert item.var_qoq is None
    assert item.var_yoy is None
    assert item.var_acumulado_aa is None
    assert item.variante is None
    assert item.unidade is None


def test_indicador_com_variante_e_unidade():
    item = IndicadorExtraido(
        empresa="Cyrela Brazil Realty",
        ano=2025,
        trimestre=3,
        indicador="lancamentos",
        variante="ex_permuta",
        unidade="R$_milhoes",
        valor_absoluto=3411.0,
    )
    assert item.variante == "ex_permuta"
    assert item.unidade == "R$_milhoes"
    assert item.valor_absoluto == 3411.0


def test_unidade_invalida_rejeitada():
    with pytest.raises(ValidationError):
        IndicadorExtraido(
            empresa="Cyrela",
            ano=2025,
            trimestre=3,
            indicador="lancamentos",
            unidade="reais",  # fora do Literal de Unidade
        )


def test_indicador_total_setor_com_variacoes():
    item = IndicadorExtraido(
        empresa="TOTAL_SETOR",
        ano=2025,
        trimestre=3,
        indicador="lancamentos",
        var_qoq=14.0,
        var_yoy=9.0,
    )
    assert item.empresa == "TOTAL_SETOR"
    assert item.var_qoq == 14.0


@pytest.mark.parametrize("trimestre", [0, 5, -1])
def test_trimestre_fora_do_range_rejeitado(trimestre):
    with pytest.raises(ValidationError):
        IndicadorExtraido(
            empresa="MRV",
            ano=2025,
            trimestre=trimestre,
            indicador="vendas",
        )


def test_indicador_invalido_rejeitado():
    with pytest.raises(ValidationError):
        IndicadorExtraido(
            empresa="MRV",
            ano=2025,
            trimestre=3,
            indicador="vgv",  # não está no Literal["lancamentos", "vendas"]
        )


def test_extracao_resultado_lista_de_indicadores():
    resultado = ExtracaoResultado(
        indicadores=[
            IndicadorExtraido(
                empresa="MRV", ano=2025, trimestre=3, indicador="lancamentos"
            ),
            IndicadorExtraido(
                empresa="Cury", ano=2025, trimestre=3, indicador="vendas"
            ),
        ]
    )
    assert len(resultado.indicadores) == 2
