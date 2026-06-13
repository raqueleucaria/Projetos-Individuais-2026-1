# Idempotência via SHA-256 do PDF, catálogo em SQLite

Para evitar chamadas desnecessárias à LLM em Prévias Operacionais já processadas,
o pipeline calcula o SHA-256 do conteúdo do PDF antes de qualquer chamada ao
Gemini e consulta o Catálogo de Dados (SQLite) por esse hash. Se o hash já existe,
o arquivo é ignorado; se é novo, o fluxo de extração segue e o hash é registrado
junto com a URL de origem (Linhagem) e os Indicadores extraídos.

SQLite foi escolhido em vez de um banco gerenciado (Postgres/etc.) pela
simplicidade de setup dado o prazo de 1 dia — é suficiente para o volume de
Prévias do MVP e para servir a API de consulta via FastAPI.

## Status

accepted
