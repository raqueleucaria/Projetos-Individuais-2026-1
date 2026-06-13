"""Extração via Gemini com Contrato Semântico — ver ADR-0002, ADR-0005, ADR-0006.

O conteúdo pré-filtrado (Markdown de tabelas + texto, não o PDF) é enviado ao
Gemini com `response_schema` derivado de `ExtracaoResultado`, forçando a saída
a obedecer ao Contrato Semântico (campos ausentes -> None/NULL).

Geração determinística: `temperature=0.0` e `thinking_budget=0`, para
reprodutibilidade e menor custo/latência numa tarefa estruturada.

Quando o PDF não tem camada de texto (escaneado), `extrair_indicadores_vision`
renderiza as páginas como imagens e usa o Gemini Vision com o mesmo schema
(ADR-0006).
"""

from pathlib import Path

import fitz
from google import genai
from google.genai import types

from uda.config import GEMINI_API_KEY, GEMINI_MODEL
from uda.schemas import ExtracaoResultado

PROMPT_SISTEMA = """\
Você é um extrator de dados para um pipeline de Engenharia de Dados Não \
Estruturados (UDA).

Receberá o conteúdo de páginas de uma Prévia Operacional de uma ou mais \
construtoras, contendo tabelas de Lançamentos e Vendas por empresa. As tabelas \
podem vir formatadas em Markdown — use o alinhamento de colunas para associar \
cada valor à empresa e ao indicador corretos.

Extraia UM item por (empresa, indicador, variante) usando exatamente o \
Contrato Semântico fornecido:
- "empresa": nome da empresa que **emite** o documento, exatamente como \
aparece no cabeçalho/título. Use "TOTAL_SETOR" **apenas** para linhas que \
sejam totais explicitamente agregados de **várias** empresas (ex: um boletim \
setorial com "Total lançamentos" somando empresas distintas). Se o documento é \
de uma **única** empresa, use o nome dela em TODAS as linhas — nunca \
"TOTAL_SETOR".
- "ano" e "trimestre": deduza do cabeçalho do documento (ex: "3º TRIMESTRE \
DE 2025" -> ano=2025, trimestre=3). Aplique o mesmo ano/trimestre a todos \
os itens, salvo indicação explícita em contrário.
- "indicador": "lancamentos" ou "vendas".
- "variante": quando o MESMO indicador aparece em recortes diferentes, \
distinga-os: "com_permuta", "ex_permuta" (ou "%CBR ex-permuta"), "permutas". \
Se não houver recorte explícito, deixe NULL.
- "unidade": unidade de "valor_absoluto" — "R$_milhoes" (valores em R$ \
milhões), "unidades" (nº de unidades), "empreendimentos" (nº de \
empreendimentos) ou "m2" (área). NULL quando "valor_absoluto" for NULL.
- "valor_absoluto": valor absoluto do indicador, se presente no texto, na \
unidade indicada em "unidade". Se o texto só traz percentuais de variação, \
deixe NULL. NÃO calcule nem estime valores absolutos a partir de percentuais.
- "var_qoq": variação percentual em relação ao trimestre anterior (ex: \
"X 2T25" quando o documento é do 3T). NULL se ausente.
- "var_yoy": variação percentual em relação ao mesmo trimestre do ano \
anterior (ex: "X 3T24"). NULL se ausente.
- "var_acumulado_aa": variação percentual acumulada (ex: "9m 25/24"). NULL \
se ausente.

Regras gerais:
- NUNCA invente valores. Campos sem informação no texto devem ser NULL.
- Ignore texto de marketing/comentários qualitativos; extraia apenas dados \
tabulares.
"""

# Páginas renderizadas para o fallback de Vision (limita custo/tokens).
MAX_PAGINAS_VISION = 5

_CONFIG = types.GenerateContentConfig(
    system_instruction=PROMPT_SISTEMA,
    response_mime_type="application/json",
    response_schema=ExtracaoResultado,
    temperature=0.0,
    thinking_config=types.ThinkingConfig(thinking_budget=0),
)


def _client() -> genai.Client:
    return genai.Client(api_key=GEMINI_API_KEY)


def extrair_indicadores(texto_paginas: str) -> ExtracaoResultado:
    """Chama o Gemini para extrair Indicadores do conteúdo pré-filtrado (texto)."""
    # Mantém referência forte ao Client durante a chamada: a requisição roda em
    # outra thread (retry interno do SDK) e um Client temporário seria coletado
    # pelo GC, fechando o httpx ("client has been closed").
    client = _client()
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"Conteúdo das páginas:\n\n{texto_paginas}",
        config=_CONFIG,
    )
    return ExtracaoResultado.model_validate_json(response.text)


def _renderizar_paginas(caminho_pdf: Path | str, dpi: int = 200) -> list[bytes]:
    """Renderiza as primeiras páginas do PDF como PNG (bytes)."""
    doc = fitz.open(caminho_pdf)
    try:
        matriz = fitz.Matrix(dpi / 72, dpi / 72)
        imagens = []
        for page in list(doc)[:MAX_PAGINAS_VISION]:
            pix = page.get_pixmap(matrix=matriz, alpha=False)
            imagens.append(pix.tobytes("png"))
        return imagens
    finally:
        doc.close()


def extrair_indicadores_vision(caminho_pdf: Path | str) -> ExtracaoResultado:
    """Fallback para PDFs escaneados: envia as imagens das páginas ao Gemini Vision."""
    partes: list = [
        types.Part.from_bytes(data=img, mime_type="image/png")
        for img in _renderizar_paginas(caminho_pdf)
    ]
    partes.append("Extraia os indicadores das tabelas nestas páginas.")

    client = _client()  # ver nota sobre referência forte em extrair_indicadores
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=partes,
        config=_CONFIG,
    )
    return ExtracaoResultado.model_validate_json(response.text)
