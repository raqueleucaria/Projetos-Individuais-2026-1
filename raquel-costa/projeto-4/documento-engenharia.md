# Documento de Engenharia — Pipeline de Conjuntura do Setor Habitacional

> Esqueleto preenchido ao longo das fases de implementação. Ver
> [`docs/planning/PRD.md`](docs/planning/PRD.md) e
> [`docs/planning/backlog.md`](docs/planning/backlog.md) para o detalhamento
> atual do escopo.

## 1. Visão geral

(Resumo do problema e da solução — ver PRD.)

## 2. Arquitetura

(Diagrama em [`docs/diagrams/architecture.md`](docs/diagrams/architecture.md);
descrição textual a ser preenchida durante a implementação.)

## 3. Camada A — Extração e Idempotência

`src/uda/hashing.py` calcula o SHA-256 do PDF (`hash_arquivo`). `src/uda/pipeline.py`
(`processar_pdf`) orquestra o fluxo: calcula o hash, consulta
`relatorio_existe` (ver [ADR-0003](docs/adr/0003-idempotencia-via-sha256-em-sqlite.md));
se o hash já existir em `relatorios`, retorna `"ignorado"` sem chamar o
Gemini. Caso contrário, segue para o Pré-filtro (Camada B), grava o relatório
e os indicadores extraídos, e retorna `"processado"`. Testado com o PDF de
exemplo: a 1ª execução processa e persiste 14 indicadores; a 2ª execução do
mesmo arquivo é ignorada.

## 4. Camada B — Contrato Semântico e Chunking

`src/uda/prefilter.py` usa PyMuPDF (`fitz`) para selecionar as páginas
relevantes por palavras-chave (`pagina_relevante`, `PAGE_FILTER_KEYWORDS` em
`src/uda/config.py`) e, para cada página selecionada, gera **Markdown** das
tabelas (`find_tables()` → `pagina_para_markdown`) mais o texto fora delas,
conforme [ADR-0001](docs/adr/0001-pre-filtro-de-paginas-antes-da-llm.md). Só
esse Markdown (não o PDF como arquivo) é enviado ao Gemini; as tabelas em
Markdown preservam o alinhamento empresa↔valor, reduzindo erros de associação.

`src/uda/extraction.py` define `extrair_indicadores`, que envia esse conteúdo ao
modelo `gemini-2.5-flash` via `client.models.generate_content` com
`response_schema=ExtracaoResultado`, `temperature=0.0` e `thinking_budget=0`
(geração determinística — ver [ADR-0002](docs/adr/0002-gemini-flash-com-saida-estruturada.md)).
O Contrato Semântico (`src/uda/schemas.py`) define `IndicadorExtraido`
(`empresa`, `ano`, `trimestre` 1-4, `indicador` ∈ {`lancamentos`, `vendas`},
`variante`, `unidade`, `valor_absoluto`, `var_qoq`, `var_yoy`,
`var_acumulado_aa`, todos opcionais e `None` quando ausentes no PDF — ver
[ADR-0005](docs/adr/0005-contrato-cobre-absolutos-e-percentuais-com-null.md) e
[ADR-0007](docs/adr/0007-variante-e-unidade-no-contrato.md)). `variante`
distingue recortes do mesmo indicador (com/ex-permuta) e `unidade` desambigua
`valor_absoluto` (R$ milhões, unidades, empreendimentos, m²).
Testado com o PDF de exemplo real: 14 `IndicadorExtraido` retornados (7
empresas/total × 2 indicadores), todos com `valor_absoluto=None` e percentuais
conferindo com a tabela do PDF.

Para PDFs **escaneados** (sem camada de texto), `processar_pdf` detecta a
ausência de texto (`tem_camada_de_texto`) e recorre ao Gemini Vision
(`extrair_indicadores_vision`), renderizando as páginas como imagem e usando o
mesmo `response_schema` (ver [ADR-0006](docs/adr/0006-fallback-gemini-vision-para-pdfs-sem-texto.md)).

Após a extração, `src/uda/validation.py` (`validar_indicadores`) faz a validação
semântica pós-LLM: além dos tipos/ranges do Pydantic, registra avisos para
linhas sem nenhum valor (provável alucinação), variações fora de faixa
plausível, empresa vazia ou ano improvável — no princípio de não confiar 100%
na saída da LLM.

## 5. Camada C — API REST

`src/uda/api.py` expõe `GET /api/conjuntura` (FastAPI), com filtros opcionais
`empresa`, `ano` e `trimestre`. A consulta usa `consultar_indicadores`
(`src/uda/db.py`), que faz `JOIN` entre `indicadores` e `relatorios` para
incluir `url_origem` (Linhagem) em cada item da resposta. A inicialização do
banco (`init_db`) ocorre via `lifespan` da aplicação FastAPI. Verificado com
uvicorn + curl: sem filtros retorna os 14 indicadores do PDF de exemplo; com
`empresa=MRV&ano=2025&trimestre=3` retorna 2 itens (lançamentos e vendas), cada
um com `url_origem` apontando para o PDF de origem.

## 6. Modelo de dados e linhagem

`src/uda/db.py` define o schema SQLite com duas tabelas (ver
[ADR-0004](docs/adr/0004-modelo-de-dados-uma-linha-por-indicador.md)):
`relatorios` (`hash` PK, `url_origem`, `arquivo_local`,
`data_processamento`) e `indicadores` (uma linha por `empresa`/`ano`/
`trimestre`/`indicador`/`variante`, com colunas `variante`, `unidade`,
`valor_absoluto` e variações, e `relatorio_hash` referenciando
`relatorios.hash` — ver [ADR-0007](docs/adr/0007-variante-e-unidade-no-contrato.md)).
Essa referência é a Linhagem: toda consulta à API carrega `url_origem` junto
com cada indicador, permitindo rastrear de qual Prévia Operacional o dado veio.

## 7. Gatilho de ingestão

`src/uda/coletor.py` implementa o gatilho em dois níveis. **Nível 1**
(`coletar`): dada uma lista de fontes (URLs de PDFs), baixa cada um e chama
`processar_pdf`, reaproveitando a Idempotência (hash) — um PDF já processado é
ignorado sem custo de LLM; é o caminho automatizável por polling/cron.
**Descoberta (nível 2)** (`extrair_links_pdf`): encontra links de PDF numa
página de Central de Resultados servida como HTML estático. Portais com lista
via JavaScript ou links sem extensão `.pdf` (ex: filemanager) exigem um
adaptador por portal — a estratégia completa está em
[`docs/planning/ingestao-polling.md`](docs/planning/ingestao-polling.md).
Validado ao vivo: o coletor baixou uma Prévia real da internet e a processou; em
nova passada do mesmo documento, retornou `ignorado` (idempotência).

## 8. Limitações conhecidas e próximos passos

- Resiliência validada com um 2º layout real (Prévia 3T25 da Cyrela, empresa
  única com valores absolutos): pipeline processou ponta-a-ponta e populou
  `valor_absoluto`. Diferenças e melhorias recomendadas (rótulo de empresa em
  docs de emissor único, variantes com/ex-permuta, campo de unidade) em
  [`docs/planning/validacao-2-layout.md`](docs/planning/validacao-2-layout.md).
- PDFs escaneados são cobertos pelo fallback Gemini Vision
  ([ADR-0006](docs/adr/0006-fallback-gemini-vision-para-pdfs-sem-texto.md)).
- Gatilho de ingestão (polling) documentado, mas ainda não implementado
  ([`docs/planning/ingestao-polling.md`](docs/planning/ingestao-polling.md)).

## 9. Benchmark de qualidade da leitura

A qualidade da extração é medida contra uma verdade-base (golden) em
`benchmark/golden/`, com métricas mapeadas aos critérios de avaliação
(cobertura, precisão, acurácia numérica, disciplina de NULL, consistência
temporal). No boletim de exemplo o pipeline atinge 100% em todas as métricas
(inclusive `disciplina_null`, confirmando que não inventa absolutos); na Cyrela,
os valores absolutos são extraídos corretamente. Medidor testado de forma
determinística em `tests/test_benchmark_metrics.py`. Detalhes e resultados em
[`docs/planning/benchmark-qualidade.md`](docs/planning/benchmark-qualidade.md).
