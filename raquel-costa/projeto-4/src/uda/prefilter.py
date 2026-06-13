"""Pré-filtro de Páginas + extração table-aware — ver ADR-0001.

Seleciona as páginas relevantes por palavras-chave (ADR-0001) e, para cada
página selecionada, extrai as tabelas como **Markdown** (via PyMuPDF
`find_tables()`) além do texto fora das tabelas. Só esse Markdown (não o PDF
como arquivo) é enviado à LLM.

A saída em tabelas Markdown preserva o alinhamento linha/coluna dos
indicadores, reduzindo erros de associação (empresa↔valor) na extração.
"""

from pathlib import Path

import fitz

from uda.config import PAGE_FILTER_KEYWORDS

# Abaixo deste total de caracteres de texto extraível, o PDF é tratado como
# escaneado/sem camada de texto e o pipeline recorre ao Gemini Vision.
MIN_CHARS_CAMADA_TEXTO = 40


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


def tem_camada_de_texto(caminho_pdf: Path | str, min_chars: int = MIN_CHARS_CAMADA_TEXTO) -> bool:
    """True se o PDF tem texto extraível suficiente (PDF nativo digital).

    PDFs escaneados/imagens retornam pouco ou nenhum texto via `get_text()`;
    nesse caso o pipeline deve recorrer ao Gemini Vision.
    """
    total = sum(len(t.strip()) for t in extrair_texto_por_pagina(caminho_pdf))
    return total >= min_chars


def _grid_para_markdown(grid: list[list]) -> str:
    """Converte um grid de tabela (lista de linhas) em uma tabela Markdown."""
    if not grid:
        return ""
    header = [(c or "").strip() for c in grid[0]]
    n = len(header)
    linhas = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * n) + " |",
    ]
    for row in grid[1:]:
        cells = [(c or "").strip() for c in row]
        cells = cells + [""] * (n - len(cells)) if len(cells) < n else cells[:n]
        linhas.append("| " + " | ".join(cells) + " |")
    return "\n".join(linhas)


def pagina_para_markdown(page: "fitz.Page") -> str:
    """Texto + tabelas (Markdown) de uma página.

    As tabelas viram Markdown; o texto que cai dentro da área de uma tabela é
    omitido para não duplicar o conteúdo já estruturado.
    """
    partes: list[str] = []
    rects: list[fitz.Rect] = []

    try:
        for table in page.find_tables().tables:
            grid = table.extract()
            if not grid or not any(any(cell for cell in row) for row in grid):
                continue
            partes.append(_grid_para_markdown(grid))
            rects.append(fitz.Rect(table.bbox))
    except Exception:
        # find_tables pode falhar em layouts atípicos; segue só com o texto.
        pass

    text_dict = page.get_text("dict")
    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:  # 0 = bloco de texto
            continue
        block_rect = fitz.Rect(block["bbox"])
        if any(r.intersects(block_rect) for r in rects):
            continue
        linhas_bloco = []
        for line in block.get("lines", []):
            t = " ".join(span["text"] for span in line.get("spans", [])).strip()
            if t:
                linhas_bloco.append(t)
        if linhas_bloco:
            partes.append("\n".join(linhas_bloco))

    return "\n\n".join(partes)


def pre_filtrar(caminho_pdf: Path | str) -> str:
    """Extrai o conteúdo (Markdown) das páginas relevantes e as concatena.

    Cada página cujo texto contém uma palavra-chave (ADR-0001) é convertida em
    Markdown (tabelas + texto). O resultado é a string enviada ao Gemini.
    """
    doc = fitz.open(caminho_pdf)
    try:
        partes = []
        for page in doc:
            if pagina_relevante(page.get_text()):
                md = pagina_para_markdown(page)
                if md.strip():
                    partes.append(md)
        return "\n\n---\n\n".join(partes)
    finally:
        doc.close()
