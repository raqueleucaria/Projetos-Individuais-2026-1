# Projeto Individual 4 — Pipeline de Conjuntura do Setor Habitacional (UDA)

Pipeline de Engenharia/Análise de Dados Não Estruturados (UDA) que extrai, via
LLM (Gemini 2.5 Flash), métricas operacionais (lançamentos e vendas) de Prévias
Operacionais em PDF de Relações com Investidores de construtoras, com três
camadas: extração com idempotência por hash, contrato semântico (Pydantic) e
API REST de consulta.

> Status: fase de planejamento concluída. Implementação em andamento, fase a
> fase, conforme [`docs/planning/backlog.md`](docs/planning/backlog.md).

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
src/
tests/
data/                # PDFs de entrada (ex: Prévia Operacional de exemplo)
```

## Setup (planejado)

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencher GEMINI_API_KEY
```

## Skills (mattpocock)

As skills curadas para este projeto estão em `.agents/skills/` (não versionado)
e linkadas em `.claude/skills/`. Para restaurar:

```sh
npx skills@latest add mattpocock/skills
mkdir -p .claude/skills && for d in .agents/skills/*/; do n=$(basename "$d"); ln -sf "../../.agents/skills/$n" ".claude/skills/$n"; done
```
