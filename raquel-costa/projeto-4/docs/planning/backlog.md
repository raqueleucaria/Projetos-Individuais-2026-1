# Backlog — Pipeline de Conjuntura do Setor Habitacional

Itens em fatias verticais (tracer bullets), priorizados para o prazo de
13/06/2026 23:59. Labels seguem o vocabulário em
[`../agents/triage-labels.md`](../agents/triage-labels.md).

---

### [fase::0] [type::chore] [priority::p0] [status::todo] Setup do projeto

Estrutura `src/`/`tests/`, `requirements.txt`, `.env.example`, configuração de
acesso ao SQLite.

**Critérios de aceite:**
- `pip install -r requirements.txt` instala todas as deps (pymupdf, pydantic,
  fastapi, uvicorn, google-genai/google-generativeai, pytest).
- `.env.example` documenta `GEMINI_API_KEY`.
- Banco SQLite criado com as tabelas `relatorios` e `indicadores`
  (ADR-0004).

**Blocked by**: None - pode começar imediatamente.

---

### [fase::0] [type::spike] [priority::p0] [status::todo] Gerar chave do Gemini

Criar conta/chave no Google AI Studio para Gemini 2.0 Flash (free tier).

**Critérios de aceite:**
- `GEMINI_API_KEY` válida disponível em `.env` local (não commitado).
- Teste manual: chamada simples ao Gemini retorna resposta.

**Fallback**: se a chave não estiver disponível a tempo, a Camada de extração
(fase::2) deve suportar um "modo mock" que retorna uma resposta fixa/fixture
em vez de chamar a API real, para não bloquear o restante do pipeline.

**Blocked by**: None - pode começar imediatamente, em paralelo com fase::0 setup.

---

### [fase::1] [type::feature] [priority::p0] [status::todo] Hash/idempotência + catálogo SQLite

Função que calcula SHA-256 do PDF, consulta a tabela `relatorios` e decide se o
arquivo deve ser processado ou ignorado.

**Critérios de aceite:**
- Dado um PDF novo, hash não existe em `relatorios` → segue para extração.
- Dado um PDF já processado, hash existe → pipeline encerra sem chamar a LLM.
- Após processar um PDF novo, uma linha é inserida em `relatorios` com hash,
  `url_origem` e `arquivo_local`.
- Teste de integração: processar o mesmo PDF duas vezes não duplica chamadas à
  LLM (mockada) nem linhas em `indicadores`.

**Blocked by**: fase::0 setup do projeto.

---

### [fase::2] [type::feature] [priority::p0] [status::todo] Pré-filtro de páginas + extração via Gemini com Contrato Semântico

Extrai texto por página (PyMuPDF), seleciona páginas por palavras-chave
(ADR-0001), monta prompt e chama Gemini 2.0 Flash com `response_schema` derivado
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

**Blocked by**: fase::0 setup do projeto, fase::0 geração da chave (ou modo
mock).

---

### [fase::3] [type::feature] [priority::p0] [status::todo] Persistência das métricas extraídas (linhagem)

Grava os Indicadores extraídos na tabela `indicadores`, vinculados ao
`relatorio_hash` (Linhagem).

**Critérios de aceite:**
- Cada Indicador extraído gera uma linha em `indicadores` com
  `relatorio_hash` apontando para a linha correspondente em `relatorios`.
- Dado o PDF de exemplo, as linhas de `TOTAL_SETOR` e das 6 empresas
  (MRV, Cury, Tenda, Plano & Plano, Direcional, Pacaembu) para Lançamentos e
  Vendas são persistidas.

**Blocked by**: fase::1 hash/catálogo, fase::2 extração via Gemini.

---

### [fase::4] [type::feature] [priority::p0] [status::todo] API REST `/api/conjuntura`

Endpoint FastAPI que consulta `indicadores` (com join em `relatorios` para
`url_origem`/Linhagem) filtrando por `empresa`, `ano`, `trimestre` (todos
opcionais).

**Critérios de aceite:**
- `GET /api/conjuntura` sem filtros retorna todos os Indicadores.
- `GET /api/conjuntura?empresa=MRV&ano=2025&trimestre=3` retorna só os
  Indicadores de MRV no 3T25.
- Cada item da resposta inclui `url_origem` (Linhagem).
- Teste de integração com fixture do Catálogo de Dados populado.

**Blocked by**: fase::3 persistência das métricas.

---

### [fase::5] [type::feature] [priority::p1] [status::todo] Documentar gatilho de ingestão (polling) como próximo passo

Seção em `docs/planning/00-overview.md` (ou novo doc) descrevendo a estratégia
de polling/cron para detectar novas Prévias Operacionais nas Centrais de
Resultados, sem implementação no MVP.

**Critérios de aceite:**
- Documento descreve frequência sugerida, fontes (URLs de RI) e como o
  resultado se encaixa na Idempotência (fase::1) já implementada.

**Blocked by**: None - pode ser feito em paralelo, mas faz mais sentido após o
PRD estar fechado.

---

### [fase::6] [type::spike] [priority::p2] [status::todo] Validação com 2º layout de Prévia Operacional (pós-MVP)

Buscar uma Prévia Operacional real em outro layout (ex: MRV RI, apresentação em
slides), rodar o pipeline e documentar ajustes necessários para resiliência.

**Critérios de aceite:**
- PDF de outro layout processado com sucesso (mesmo que com campos NULL para o
  que não existir nesse layout).
- Diferenças de comportamento (Pré-filtro, schema) documentadas.

**Blocked by**: fase::2, fase::3, fase::4 (pipeline ponta-a-ponta funcionando
com o PDF de exemplo).
