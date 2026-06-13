from uda.config import DATA_DIR
from uda.prefilter import (
    _grid_para_markdown,
    extrair_texto_por_pagina,
    pagina_relevante,
    pre_filtrar,
    tem_camada_de_texto,
)

EXEMPLO_PDF = DATA_DIR / "exemplo_Boletim_Conjuntura_2025_3T.pdf"


def test_pagina_relevante_com_palavra_chave():
    assert pagina_relevante("Total de LANÇAMENTOS no trimestre") is True
    assert pagina_relevante("Relatório de sustentabilidade ESG") is False


def test_extrair_texto_por_pagina_pdf_exemplo():
    paginas = extrair_texto_por_pagina(EXEMPLO_PDF)
    assert len(paginas) >= 1
    assert "lançamentos" in paginas[0].lower()


def test_pre_filtrar_mantem_paginas_relevantes():
    texto = pre_filtrar(EXEMPLO_PDF)
    assert "MRV" in texto
    assert "Vendas".lower() in texto.lower() or "vendas" in texto.lower()


def test_grid_para_markdown_formata_tabela():
    md = _grid_para_markdown([["Empresa", "Vendas"], ["MRV", "-12%"]])
    linhas = md.splitlines()
    assert linhas[0] == "| Empresa | Vendas |"
    assert linhas[1] == "| --- | --- |"
    assert linhas[2] == "| MRV | -12% |"


def test_grid_para_markdown_normaliza_celulas_none_e_colunas_faltando():
    md = _grid_para_markdown([["A", "B"], [None]])
    assert md.splitlines()[2] == "|  |  |"


def test_pre_filtrar_gera_markdown_com_tabela():
    texto = pre_filtrar(EXEMPLO_PDF)
    assert "| --- |" in texto  # ao menos uma tabela Markdown


def test_tem_camada_de_texto_pdf_exemplo():
    assert tem_camada_de_texto(EXEMPLO_PDF) is True
