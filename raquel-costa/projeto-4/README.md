# Projeto Individual 4 — Pipeline de Conjuntura do Setor Habitacional (UDA)

![projeto-4 CI](https://github.com/raqueleucaria/Projetos-Individuais-2026-1/actions/workflows/projeto-4-ci.yml/badge.svg)

Pipeline de Engenharia/Análise de Dados Não Estruturados (UDA) que extrai, via
LLM (Gemini 2.5 Flash), métricas operacionais (lançamentos e vendas) de Prévias
Operacionais em PDF de Relações com Investidores de construtoras, com três
camadas: extração com idempotência por hash, contrato semântico (Pydantic) e
API REST de consulta. Inclui pré-filtro table-aware, fallback Gemini Vision para
PDFs escaneados, validação semântica pós-LLM, coletor de ingestão e um benchmark
de qualidade da leitura.

> Status: MVP + pós-MVP concluídos (fase::0 → fase::6 e evoluções), conforme
> [`docs/planning/backlog.md`](docs/planning/backlog.md).

## Documentação

- [`documento-engenharia.md`](documento-engenharia.md) — documento de engenharia
  (preenchido ao longo das fases).
- [`docs/CONTEXT.md`](docs/CONTEXT.md) — glossário do domínio.
- [`docs/adr/`](docs/adr/) — decisões de arquitetura (ADRs).
- [`docs/planning/PRD.md`](docs/planning/PRD.md) — PRD do MVP.
- [`docs/planning/backlog.md`](docs/planning/backlog.md) — backlog em fatias
  verticais, com labels de triagem.
- [`docs/planning/00-overview.md`](docs/planning/00-overview.md) — fluxo de
  planejamento adotado.
- [`docs/diagrams/architecture.md`](docs/diagrams/architecture.md) — diagrama
  de arquitetura (mermaid).

## Estrutura

```
README.md
documento-engenharia.md
docs/
  CONTEXT.md
  adr/
  agents/
  planning/
  diagrams/
src/uda/             # config, prefilter, extraction, schemas, db, pipeline, api,
                     # validation, coletor, benchmark, hashing
tests/
benchmark/golden/    # verdade-base do benchmark de qualidade
data/                # PDFs de entrada (ex: Prévia Operacional de exemplo)
```

## Setup

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencher GEMINI_API_KEY
```

## Como rodar

Todos os comandos usam `PYTHONPATH=src` (o `pytest.ini` já cuida disso nos testes).

```sh
# Testes (41, todos offline — não chamam a API)
PYTHONPATH=src pytest -q

# Processar o PDF de exemplo (popula o catálogo SQLite) — chama o Gemini
PYTHONPATH=src python -m uda.pipeline

# API REST (filtros: empresa, ano, trimestre, variante, unidade)
PYTHONPATH=src uvicorn uda.api:app --reload
# curl 'http://127.0.0.1:8000/api/conjuntura?empresa=MRV&ano=2025&trimestre=3'

# Coletor de ingestão: baixa PDFs de fontes e processa (idempotente)
PYTHONPATH=src python -m uda.coletor "<url_de_um_pdf>" ["<outra_url>" ...]

# Benchmark de qualidade da leitura (golden dataset) — chama o Gemini
PYTHONPATH=src python -m uda.benchmark
```

## CI

O workflow [`.github/workflows/projeto-4-ci.yml`](../../.github/workflows/projeto-4-ci.yml)
roda a suíte de testes a cada push/PR que toca `raquel-costa/projeto-4/**`. Os
testes são offline (não exigem `GEMINI_API_KEY`): a extração via LLM é mockada e
o medidor do benchmark é testado de forma determinística.

## Skills (mattpocock)

As skills curadas para este projeto estão em `.agents/skills/` (não versionado)
e linkadas em `.claude/skills/`. Para restaurar:

```sh
npx skills@latest add mattpocock/skills
mkdir -p .claude/skills && for d in .agents/skills/*/; do n=$(basename "$d"); ln -sf "../../.agents/skills/$n" ".claude/skills/$n"; done
```
