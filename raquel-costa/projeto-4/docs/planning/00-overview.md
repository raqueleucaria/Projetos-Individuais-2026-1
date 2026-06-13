# Overview — Fluxo de Planejamento

Este projeto adapta o fluxo de planejamento ágil das skills de
[mattpocock/skills](https://github.com/mattpocock/skills) para um repositório
compartilhado (sem issue tracker do GitHub nem CI da disciplina) e um prazo
curto (entrega 13/06/2026 23:59).

## Fluxo adotado

1. **Concepção / domínio** (`/grill-with-docs`) — interview sobre o enunciado
   (`projeto-individual-4/README.md`) e o PDF de exemplo para fechar decisões de
   arquitetura, chunking e modelo de dados. Resultado: [`../CONTEXT.md`](../CONTEXT.md)
   e [ADRs](../adr/).
2. **PRD** (`/to-prd`) — síntese das decisões em [`PRD.md`](./PRD.md), cobrindo
   as 3 camadas obrigatórias (extração/idempotência, contrato semântico,
   API) e o gatilho de ingestão.
3. **Backlog em markdown** (`/to-issues` + `/triage`, adaptado) — em vez de
   issues do GitHub, o PRD foi quebrado em fatias verticais em
   [`backlog.md`](./backlog.md), cada item com labels de
   [`../agents/triage-labels.md`](../agents/triage-labels.md) (`fase`, `type`,
   `priority`, `status`).
4. **Diagrama de arquitetura** — [`../diagrams/architecture.md`](../diagrams/architecture.md),
   fluxo PDF → hash/dedup → pré-filtro → Gemini → catálogo SQLite → API.
5. **Implementação** — fase a fase, seguindo `backlog.md` em ordem de
   prioridade/dependência. Um PR por item de backlog (ou item agrupado, quando
   pequeno), referenciando o item correspondente.

## Adaptação: por que backlog em markdown e não issues do GitHub?

O repositório é compartilhado entre todos os alunos da disciplina
(`unb-Sistemas-de-Machine-learning/Projetos-Individuais-2026-1`), sem branch
protection nem CI configurados para os projetos individuais, e o trabalho é
feito no fork pessoal (`raqueleucaria/Projetos-Individuais-2026-1`). Abrir
issues no repositório upstream poluiria o tracker compartilhado com itens de um
único aluno; por isso o backlog vive em `docs/planning/backlog.md`, usando o
mesmo vocabulário de labels (`type`, `priority`, `status`) que as skills de
triagem usariam em issues reais.

## Gatilho de ingestão (próximo passo, fora do MVP)

O enunciado exige uma estratégia de detecção de novas Prévias Operacionais nas
Centrais de Resultados (RI) das construtoras. O MVP processa uma lista fixa
(o PDF de exemplo em `data/`); o próximo passo planejado é:

- **Polling/CronJob** diário sobre as páginas de Central de Resultados das
  empresas-alvo (MRV, Cury, Tenda, Plano & Plano, Direcional, Pacaembu),
  comparando os links de PDF encontrados com os hashes já registrados em
  `relatorios` (reaproveitando a Idempotência da fase::1 do backlog).
- Alternativa de RSS/webhook não é viável para a maioria dos portais de RI
  observados (não publicam feed), por isso polling é a estratégia recomendada.

## Restaurando as skills (mattpocock)

As skills curadas (12) já estão instaladas em `.agents/skills/` (ignorado pelo
git) e linkadas em `.claude/skills/`. Para restaurar em outra máquina/checkout,
dentro de `raquel-costa/projeto-4/`:

```sh
npx skills@latest add mattpocock/skills
mkdir -p .claude/skills && for d in .agents/skills/*/; do n=$(basename "$d"); ln -sf "../../.agents/skills/$n" ".claude/skills/$n"; done
```

O `npx skills@latest add` lê o `skills-lock.json` versionado e instala/realinha
apenas as skills nele listadas.
