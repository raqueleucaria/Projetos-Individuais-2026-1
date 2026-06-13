"""Pré-filtro de Páginas — ver ADR-0001.

Extrai o texto de cada página do PDF via PyMuPDF e seleciona apenas as
páginas cujo texto contém alguma das `PAGE_FILTER_KEYWORDS`. Apenas o texto
das páginas selecionadas é enviado à LLM, não o PDF como arquivo.
"""

from pathlib import Path

import fitz

from uda.config import PAGE_FILTER_KEYWORDS


def extrair_texto_por_pagina(caminho_pdf: Path | str) -> list[str]:
    """Retorna o texto de cada página do PDF, em ordem."""
    doc = fitz.open(caminho_pdf)
    try:
        return [page.get_text() for page in doc]
    finally:
        doc.close()


def pagina_relevante(texto: str, palavras_chave: list[str] = PAGE_FILTER_KEYWORDS) -> bool:
    """True se o texto da página contém alguma palavra-chave (case-insensitive)."""
    texto_lower = texto.lower()
    return any(palavra in texto_lower for palavra in palavras_chave)


def pre_filtrar(caminho_pdf: Path | str) -> str:
    """Extrai o texto das páginas relevantes e as concatena.

    Retorna uma string única com o texto de todas as páginas que passaram
    pelo Pré-filtro, pronta para compor o prompt enviado ao Gemini.
    """
    paginas = extrair_texto_por_pagina(caminho_pdf)
    relevantes = [texto for texto in paginas if pagina_relevante(texto)]
    return "\n\n".join(relevantes)
