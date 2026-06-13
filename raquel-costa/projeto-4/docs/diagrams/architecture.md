# Arquitetura — Pipeline de Conjuntura do Setor Habitacional

```mermaid
flowchart LR
    A["Prévia Operacional (PDF)"] --> B["Hash SHA-256"]
    B --> C{"Hash existe em 'relatorios'?"}
    C -- sim --> Z["Ignorar (idempotência)"]
    C -- não --> T{"PDF tem camada de texto?"}
    T -- sim --> D["Pré-filtro de Páginas + tabelas em Markdown (palavras-chave)"]
    T -- não --> V["Renderizar páginas como imagem (Gemini Vision)"]
    D --> E["Gemini 2.5 Flash + Contrato Semântico (Pydantic / response_schema)"]
    V --> E
    E --> VAL["Validação semântica pós-LLM (warnings)"]
    VAL --> F[("Catálogo de Dados SQLite")]
    F --> F1["tabela relatorios: hash, url_origem, arquivo_local"]
    F --> F2["tabela indicadores: empresa, ano, trimestre, indicador, valor_absoluto, var_qoq, var_yoy, var_acumulado_aa"]
    F2 --> G["API FastAPI: GET /api/conjuntura?empresa=&ano=&trimestre="]
```

## Notas

- O **Pré-filtro de Páginas** (ADR-0001) reduz o texto enviado ao Gemini,
  selecionando páginas candidatas por palavras-chave (`lançamentos`, `vendas`,
  `VGV`, `unidades`) e enviando as tabelas dessas páginas como **Markdown**
  (via `find_tables()`), preservando o alinhamento empresa↔valor.
- Para PDFs **escaneados** (sem camada de texto), o pipeline recorre ao
  **Gemini Vision** com o mesmo Contrato Semântico (ADR-0006).
- O **Contrato Semântico** (ADR-0002, ADR-0005) força o Gemini a retornar dados
  no formato Pydantic, com `None`/NULL para campos ausentes; a geração usa
  `temperature=0.0` + `thinking_budget=0` (determinística).
- A **Validação semântica pós-LLM** (`src/uda/validation.py`) sinaliza linhas
  suspeitas (sem valores, variação implausível, empresa vazia) antes de persistir.
- A **Linhagem** é preservada via `relatorio_hash` na tabela `indicadores`,
  apontando para `url_origem` em `relatorios` (ADR-0003, ADR-0004).
- O **Gatilho de Ingestão** (polling/cron sobre as Centrais de Resultados) não
  está representado neste diagrama — é um próximo passo documentado em
  `docs/planning/00-overview.md`, fora do MVP.
