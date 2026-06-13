"""Extração via Gemini com Contrato Semântico — ver ADR-0002, ADR-0005.

O texto pré-filtrado (não o PDF) é enviado ao Gemini com `response_schema`
derivado de `ExtracaoResultado`, forçando a saída a obedecer ao Contrato
Semântico (campos ausentes -> None/NULL).
"""

from google import genai

from uda.config import GEMINI_API_KEY, GEMINI_MODEL
from uda.schemas import ExtracaoResultado

PROMPT_SISTEMA = """\
Você é um extrator de dados para um pipeline de Engenharia de Dados Não \
Estruturados (UDA).

Receberá o texto extraído de páginas de uma Prévia Operacional de uma ou \
mais construtoras, contendo tabelas de Lançamentos e Vendas por empresa.

Extraia UM item por (empresa, indicador) usando exatamente o Contrato \
Semântico fornecido:
- "empresa": nome da construtora exatamente como aparece no texto. Use \
"TOTAL_SETOR" para os totais agregados do setor (ex: "Total lançamentos", \
"Total vendas").
- "ano" e "trimestre": deduza do cabeçalho do documento (ex: "3º TRIMESTRE \
DE 2025" -> ano=2025, trimestre=3). Aplique o mesmo ano/trimestre a todos \
os itens, salvo indicação explícita em contrário.
- "indicador": "lancamentos" ou "vendas".
- "valor_absoluto": valor absoluto (R$, unidades, m²) do indicador, se \
presente no texto. Se o texto só traz percentuais de variação, deixe NULL. \
NÃO calcule nem estime valores absolutos a partir de percentuais.
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


def extrair_indicadores(texto_paginas: str) -> ExtracaoResultado:
    """Chama o Gemini para extrair Indicadores do texto pré-filtrado."""
    client = genai.Client(api_key=GEMINI_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=f"{PROMPT_SISTEMA}\n\n---\n\nTexto das páginas:\n\n{texto_paginas}",
        config={
            "response_mime_type": "application/json",
            "response_schema": ExtracaoResultado,
        },
    )

    return ExtracaoResultado.model_validate_json(response.text)
