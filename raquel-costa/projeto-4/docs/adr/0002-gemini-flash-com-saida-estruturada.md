# Gemini 2.5 Flash com saída estruturada (response_schema)

A camada de extração precisa de um LLM que aceite texto livre (saída do
Pré-filtro de Páginas) e retorne dados aderentes ao Contrato Semântico. Optamos
pelo Gemini Flash (free tier do Google AI Studio), usando o parâmetro nativo
`response_schema` para forçar a saída no formato do Pydantic, em vez de GPT-4/
Claude (sem free tier viável para o prazo) ou de parsing manual de JSON livre
(mais frágil contra alucinações de formato).

A chave de API foi gerada e testada em 2026-06-13 (`google-genai`, lib
`google.genai.Client`). O modelo originalmente planejado, `gemini-2.0-flash`,
retornou `429 RESOURCE_EXHAUSTED` com `limit: 0` no free tier para esta chave
(modelo sem cota free tier para projetos novos). Testes confirmaram que
`gemini-2.5-flash` e `gemini-flash-latest` respondem normalmente no free tier.
Decisão: usar **`gemini-2.5-flash`** como modelo da camada de extração.
`gemini-1.5-flash` está descontinuado (404 para `generateContent`).

## Status

accepted
