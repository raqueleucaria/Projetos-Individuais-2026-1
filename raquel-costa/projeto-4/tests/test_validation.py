from uda.schemas import IndicadorExtraido
from uda.validation import validar_indicadores


def _ind(**kw):
    base = dict(empresa="MRV", ano=2025, trimestre=3, indicador="vendas")
    base.update(kw)
    return IndicadorExtraido(**base)


def test_indicador_valido_sem_avisos():
    avisos = validar_indicadores([_ind(var_qoq=-12.0, var_yoy=-10.0)])
    assert avisos == []


def test_linha_sem_nenhum_valor_gera_aviso():
    avisos = validar_indicadores([_ind()])  # todos os numéricos None
    assert any("possível linha vazia" in a for a in avisos)


def test_variacao_absurda_gera_aviso():
    avisos = validar_indicadores([_ind(var_yoy=5000.0)])
    assert any("fora da faixa plausível" in a for a in avisos)


def test_ano_fora_de_faixa_gera_aviso():
    avisos = validar_indicadores([_ind(ano=1800, var_qoq=1.0)])
    assert any("fora de" in a for a in avisos)


def test_empresa_vazia_gera_aviso():
    avisos = validar_indicadores([_ind(empresa="  ", var_qoq=1.0)])
    assert any("empresa vazia" in a for a in avisos)
