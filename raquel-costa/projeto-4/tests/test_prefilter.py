from uda.config import DATA_DIR
from uda.prefilter import extrair_texto_por_pagina, pagina_relevante, pre_filtrar

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
