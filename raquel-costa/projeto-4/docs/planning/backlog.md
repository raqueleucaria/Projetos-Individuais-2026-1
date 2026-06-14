# Backlog — Pipeline de Conjuntura do Setor Habitacional

Itens em fatias verticais (tracer bullets), priorizados para o prazo de
13/06/2026 23:59. Labels seguem o vocabulário em
[`../agents/triage-labels.md`](../agents/triage-labels.md).

---

### [fase::0] [type::chore] [priority::p0] [status::done] Setup do projeto

Estrutura `src/`/`tests/`, `requirements.txt`, `.env.example`, configuração de
acesso ao SQLite.

**Critérios de aceite:**
- `pip install -r requirements.txt` instala todas as deps (pymupdf, pydantic, ✅
  fastapi, uvicorn, google-genai, pytest, httpx).
- `.env.example` documenta `GEMINI_API_KEY`. ✅
- Banco SQLite criado com as tabelas `relatorios` e `indicadores` ✅
  (ADR-0004) via `src/uda/db.py` (`init_db`).

**Resultado (2026-06-13)**: criados `src/uda/{config,db,schemas,hashing}.py` +
testes (`tests/test_db.py`, `test_schemas.py`, `test_hashing.py`), 12 testes
passando (`pytest`).

**Blocked by**: None - pode começar imediatamente.

---

### [fase::0] [type::spike] [priority::p0] [status::done] Gerar chave do Gemini

Criar conta/chave no Google AI Studio para Gemini Flash (free tier).

**Critérios de aceite:**
- `GEMINI_API_KEY` válida disponível em `.env` local (não commitado). ✅
- Teste manual: chamada simples ao Gemini retorna resposta. ✅

**Resultado (2026-06-13)**: chave gerada e testada com `google-genai`.
`gemini-2.0-flash` retornou `429 RESOURCE_EXHAUSTED` (`limit: 0` no free tier);
`gemini-1.5-flash` retornou 404 (descontinuado). `gemini-2.5-flash` respondeu
normalmente — modelo escolhido (ver ADR-0002 atualizado).

**Fallback**: mantido como referência — caso a chave expire/seja revogada, a
Camada de extração (fase::2) deve suportar um "modo mock" que retorna uma
resposta fixa/fixture em vez de chamar a API real, para não bloquear o restante
do pipeline.

**Blocked by**: None - pode começar imediatamente, em paralelo com fase::0 setup.

---

### [fase::1] [type::feature] [priority::p0] [status::done] Hash/idempotência + catálogo SQLite

Função que calcula SHA-256 do PDF, consulta a tabela `relatorios` e decide se o
arquivo deve ser processado ou ignorado.

**Critérios de aceite:**
- Dado um PDF novo, hash não existe em `relatorios` → segue para extração.
- Dado um PDF já processado, hash existe → pipeline encerra sem chamar a LLM.
- Após processar um PDF novo, uma linha é inserida em `relatorios` com hash,
  `url_origem` e `arquivo_local`.
- Teste de integração: processar o mesmo PDF duas vezes não duplica chamadas à
  LLM (mockada) nem linhas em `indicadores`.

**Resultado (2026-06-13)**: `src/uda/pipeline.py` (`processar_pdf`) implementa a
orquestração hash → checagem em `relatorios` → pré-filtro → extração →
persistência. Testado contra o PDF de exemplo com a API real do Gemini:
1ª chamada retorna `"processado"` (registra relatório + 14 indicadores), 2ª
chamada com o mesmo PDF retorna `"ignorado"` sem nova chamada à LLM.

**Blocked by**: fase::0 setup do projeto.

---

### [fase::2] [type::feature] [priority::p0] [status::done] Pré-filtro de páginas + extração via Gemini com Contrato Semântico

Extrai texto por página (PyMuPDF), seleciona páginas por palavras-chave
(ADR-0001), monta prompt e chama Gemini 2.5 Flash com `response_schema` derivado
do Contrato Semântico (ADR-0002, ADR-0005).

**Critérios de aceite:**
- Dado o PDF de exemplo, o Pré-filtro seleciona as páginas com as tabelas de
  Lançamentos/Vendas.
- A chamada ao Gemini retorna uma lista de objetos validados pelo Pydantic
  (`empresa`, `ano`, `trimestre`, `indicador`, `valor_absoluto`, `var_qoq`,
  `var_yoy`, `var_acumulado_aa`).
- Campos ausentes no PDF (ex: `valor_absoluto`) chegam como `None`/NULL, não
  como valor inventado.
- Modo mock disponível para rodar sem `GEMINI_API_KEY` (ver item de geração de
  chave).
- Teste unitário do Contrato Semântico: fixture de resposta da LLM →
  validação Pydantic passa e tipos/ranges (`trimestre` 1-4) são respeitados.

**Resultado (2026-06-13)**: `src/uda/prefilter.py` (PyMuPDF) extrai texto por
página e seleciona páginas pelas palavras-chave de `PAGE_FILTER_KEYWORDS`;
`src/uda/extraction.py` envia apenas esse texto ao `gemini-2.5-flash` com
`response_schema=ExtracaoResultado`. Testado com o PDF de exemplo real: retorna
14 `IndicadorExtraido` (7 empresas/total × 2 indicadores), todos com
`valor_absoluto=None` (o PDF só traz percentuais) e variações conferindo com a
tabela do PDF. Testes em `tests/test_prefilter.py`.

**Blocked by**: fase::0 setup do projeto, fase::0 geração da chave (ou modo
mock).

---

### [fase::3] [type::feature] [priority::p0] [status::done] Persistência das métricas extraídas (linhagem)

Grava os Indicadores extraídos na tabela `indicadores`, vinculados ao
`relatorio_hash` (Linhagem).

**Critérios de aceite:**
- Cada Indicador extraído gera uma linha em `indicadores` com
  `relatorio_hash` apontando para a linha correspondente em `relatorios`.
- Dado o PDF de exemplo, as linhas de `TOTAL_SETOR` e das 6 empresas
  (MRV, Cury, Tenda, Plano & Plano, Direcional, Pacaembu) para Lançamentos e
  Vendas são persistidas.

**Resultado (2026-06-13)**: `registrar_indicadores` (em `src/uda/db.py`),
chamada por `processar_pdf`, grava cada `IndicadorExtraido` em `indicadores`
com `relatorio_hash` apontando para a linha de `relatorios`. Confirmado com o
PDF de exemplo: 14 linhas persistidas, todas com `relatorio_hash` válido.
Testes em `tests/test_db.py`.

**Blocked by**: fase::1 hash/catálogo, fase::2 extração via Gemini.

---

### [fase::4] [type::feature] [priority::p0] [status::done] API REST `/api/conjuntura`

Endpoint FastAPI que consulta `indicadores` (com join em `relatorios` para
`url_origem`/Linhagem) filtrando por `empresa`, `ano`, `trimestre` (todos
opcionais).

**Critérios de aceite:**
- `GET /api/conjuntura` sem filtros retorna todos os Indicadores.
- `GET /api/conjuntura?empresa=MRV&ano=2025&trimestre=3` retorna só os
  Indicadores de MRV no 3T25.
- Cada item da resposta inclui `url_origem` (Linhagem).
- Teste de integração com fixture do Catálogo de Dados populado.

**Resultado (2026-06-13)**: `src/uda/api.py` expõe `GET /api/conjuntura` com
filtros opcionais `empresa`/`ano`/`trimestre`, usando `lifespan` para
`init_db()`. Verificado com uvicorn + curl contra o catálogo populado pelo PDF
de exemplo: sem filtros retorna 14 itens; com
`empresa=MRV&ano=2025&trimestre=3` retorna 2 itens (lançamentos e vendas), cada
um com `url_origem`. Testes em `tests/test_api.py`.

**Blocked by**: fase::3 persistência das métricas.

---

### [fase::5] [type::feature] [priority::p1] [status::done] Coletor de ingestão (implementação)

Implementação do gatilho de ingestão (`src/uda/coletor.py`).

**Critérios de aceite:**
- `coletar(fontes)` baixa cada PDF e chama `processar_pdf` (idempotente). ✅
- Descoberta `extrair_links_pdf(html)` acha links de PDF em HTML estático. ✅
- Testes sem rede/LLM (`tests/test_coletor.py`) + demo e2e ao vivo. ✅

**Resultado (2026-06-13)**: nível 1 (lista de fontes → download → pipeline
idempotente) + descoberta nível 2 para HTML estático. Validado ao vivo: baixou
uma Prévia real da internet e processou; 2ª passada do mesmo doc → `ignorado`.
Scraping de portais JS reais fica documentado como adaptador por portal
(`ingestao-polling.md`). 4 testes (mock de rede/LLM).

---

### [fase::5] [type::feature] [priority::p1] [status::done] Documentar gatilho de ingestão (polling) como próximo passo

Seção em `docs/planning/00-overview.md` (ou novo doc) descrevendo a estratégia
de polling/cron para detectar novas Prévias Operacionais nas Centrais de
Resultados, sem implementação no MVP.

**Critérios de aceite:**
- Documento descreve frequência sugerida, fontes (URLs de RI) e como o ✅
  resultado se encaixa na Idempotência (fase::1) já implementada.

**Resultado (2026-06-13)**: criado
[`docs/planning/ingestao-polling.md`](./ingestao-polling.md) com a frequência
sugerida (polling diário, janelas trimestrais), os portais de RI das seis
empresas-alvo e o fluxo do coletor delegando dedup ao `processar_pdf` (hash →
`relatorios`), mantendo o coletor _stateless_. Overview atualizado para apontar
para o doc.

**Blocked by**: None - pode ser feito em paralelo, mas faz mais sentido após o
PRD estar fechado.

---

### [fase::6] [type::spike] [priority::p2] [status::done] Validação com 2º layout de Prévia Operacional (pós-MVP)

Buscar uma Prévia Operacional real em outro layout (ex: MRV RI, apresentação em
slides), rodar o pipeline e documentar ajustes necessários para resiliência.

**Critérios de aceite:**
- PDF de outro layout processado com sucesso (mesmo que com campos NULL para o ✅
  que não existir nesse layout).
- Diferenças de comportamento (Pré-filtro, schema) documentadas. ✅

**Resultado (2026-06-13)**: validado com a **Prévia Operacional 3T25 da Cyrela**
(CYRE3) — comunicado de empresa única, em prosa + tabelas, com valores absolutos
em R$ milhões (layout bem diferente do boletim agregado de exemplo). Pipeline
rodou ponta-a-ponta (`processado`); desta vez `valor_absoluto` veio populado
(R$ 5.050M / R$ 3.411M lançamentos, R$ 2.459M vendas), conferindo com o texto.
Diferenças e recomendações (rótulo `TOTAL_SETOR` em doc de empresa única;
variantes com/ex-permuta; falta de campo de unidade) documentadas em
[`validacao-2-layout.md`](./validacao-2-layout.md).

**Blocked by**: fase::2, fase::3, fase::4 (pipeline ponta-a-ponta funcionando
com o PDF de exemplo).

---

### [fase::6] [type::feature] [priority::p1] [status::done] Estratégias de robustez da extração

Quatro estratégias para elevar qualidade/resiliência sobre o MVP validado.

**Critérios de aceite:**
- Extração table-aware: tabelas viram Markdown antes da LLM (ADR-0001). ✅
- Geração determinística: `temperature=0.0` + `thinking_budget=0`. ✅
- Validação semântica pós-LLM com warnings (`src/uda/validation.py`). ✅
- Fallback Gemini Vision para PDFs sem camada de texto (ADR-0006). ✅

**Resultado (2026-06-13)**: `prefilter.py` (Markdown via `find_tables()` +
`tem_camada_de_texto`), `extraction.py` (config determinística +
`extrair_indicadores_vision`), `validation.py` (novo) e `pipeline.py`
(classificação texto/scan + validação). Re-validado e2e contra o PDF de
exemplo: 14 indicadores conferindo com a tabela. 27 testes passando (novos em
`tests/test_validation.py` e `tests/test_prefilter.py`).

**Blocked by**: fase::2, fase::3, fase::4.

---

### [fase::6] [type::feature] [priority::p1] [status::done] Evoluções pós-validação: rótulo de empresa + variante/unidade

Evoluções derivadas da validação de 2º layout (`validacao-2-layout.md`).

**Critérios de aceite:**
- Prompt usa o nome da empresa emissora em docs de emissor único; ✅
  `TOTAL_SETOR` só para totais agregados de várias empresas.
- Contrato ganha `variante` e `unidade` (ADR-0007); API filtra por ambos. ✅
- Re-validado nos 2 PDFs sem regressão. ✅

**Resultado (2026-06-13)**: `schemas.py` (+`variante`/`unidade`), `db.py`
(+colunas e filtros), `api.py` (+filtros), prompt generalizado em
`extraction.py`, ADR-0007. Re-validado: boletim mantém 14 linhas e `TOTAL_SETOR`
correto (variante/unidade NULL); Cyrela passa a rotular "Cyrela Brazil Realty"
em todas as linhas, com `ex_permuta`/`permutas` e `unidade` separando
`empreendimentos` de `R$_milhoes`. 30 testes passando.

**Blocked by**: fase::6 validação com 2º layout.

---

### [fase::5] [type::feature] [priority::p1] [status::done] Scheduler + Docker + 3º layout (paridade)

Itens de paridade/robustez após comparação com entregas de colegas.

**Critérios de aceite:**
- Scheduler de ingestão contínua (`scheduler.py`) lendo `config/sources.yaml`. ✅
- Ambiente conteinerizado (`Dockerfile` + `docker-compose.yml`: API + scheduler). ✅
- 3º layout real validado (Release de Resultados da Tenda) no benchmark. ✅

**Resultado (2026-06-13)**: `scheduler.py` (ciclo + intervalo, fontes via YAML,
`pyyaml`) + `test_scheduler.py`; `Dockerfile`/`docker-compose.yml` (build e API
verificados em container); golden+snapshot da Tenda (`tenda_3T25`) com assert
por PDF. Guard amigável quando falta `GEMINI_API_KEY`; `DB_PATH` configurável
por env (volume Docker). 48 testes passando.

**Blocked by**: coletor (fase::5), benchmark.
