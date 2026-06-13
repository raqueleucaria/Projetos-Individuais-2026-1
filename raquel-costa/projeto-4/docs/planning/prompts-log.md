# Log de decisões e uso de skills

Log datado das principais decisões tomadas durante o planejamento do projeto e
das skills usadas para chegar a elas.

## 2026-06-12 — Curadoria de skills

Skills do `mattpocock/skills` instaladas via `npx skills@latest add` e curadas
para o subconjunto de planejamento/prototipagem deste projeto (12 skills,
registradas em `skills-lock.json`):

- **Núcleo de planejamento**: `grill-with-docs`, `to-prd`, `to-issues`,
  `triage`, `zoom-out`.
- **Implementação futura**: `tdd`, `diagnose`, `qa`, `request-refactor-plan`,
  `prototype`.
- **Mantidos mas não usados nesta fase**: `setup-pre-commit`,
  `git-guardrails-claude-code`, `write-a-skill`.

Motivo: o repositório é compartilhado (sem `gh`/issue tracker da disciplina
configurado para projetos individuais), então `setup-matt-pocock-skills`
(que assume issue tracker via gh/glab) não se aplica — `docs/agents/` foi
criado manualmente.

## 2026-06-13 — `/grill-with-docs`: decisões de arquitetura via interview

Sessão de `/grill-with-docs` contra o enunciado (`projeto-individual-4/README.md`)
e o PDF de exemplo, resolvendo:

1. **Prazo**: confirmado 13/06/2026 23:59 (hoje), apesar do README genérico
   indicar 08/06 — tratado como prazo real desta entrega.
2. **Chave do Gemini**: ainda não existe. Adicionada como tarefa p0 do backlog
   (`fase::0`, spike), com modo mock como fallback para a extração.
3. **2º layout (resiliência a layouts diferentes)**: adiado para pós-MVP
   (`fase::6` do backlog), dado o prazo de 1 dia.
4. **Chunking**: decidido implementar o Pré-filtro de Páginas por palavras-chave
   desde o MVP (ADR-0001), em vez de full-scan puro — mesmo o PDF de exemplo
   sendo pequeno, a estratégia é o que escala para Prévias maiores (slides).
5. **Valores absolutos vs. percentuais**: identificada contradição entre o PDF
   de exemplo (só percentuais) e o critério de avaliação (valores absolutos).
   Resolvida no Contrato Semântico cobrindo ambos, com NULL explícito para
   absolutos no exemplo (ADR-0005).
6. **Modelo de dados**: uma linha por (empresa, ano, trimestre, indicador) em
   `indicadores`, em vez de tabela "wide" (ADR-0004) — favorece extensibilidade
   para novos indicadores em layouts futuros.
7. **Ingestão do MVP**: apenas o PDF de exemplo (`data/exemplo_Boletim_Conjuntura_2025_3T.pdf`).
   Gatilho de polling documentado como próximo passo em `00-overview.md`.
8. **Stack**: Python com pip + `requirements.txt` + venv (sem poetry/uv), pela
   simplicidade dado o prazo.

Resultado: [`../CONTEXT.md`](../CONTEXT.md) (glossário), ADRs 0001-0005 em
[`../adr/`](../adr/), [`PRD.md`](./PRD.md), [`backlog.md`](./backlog.md),
[`../diagrams/architecture.md`](../diagrams/architecture.md).

## 2026-06-13 — Chave do Gemini gerada e testada

Chave do Gemini gerada no Google AI Studio, configurada em `.env` local
(`GEMINI_API_KEY`, não versionado) e validada com a lib `google-genai`.

- `gemini-2.0-flash` (modelo originalmente planejado): `429 RESOURCE_EXHAUSTED`,
  `limit: 0` no free tier — sem cota disponível para esta chave.
- `gemini-1.5-flash`: `404 NOT_FOUND` — descontinuado.
- `gemini-2.5-flash` e `gemini-flash-latest`: respondem normalmente.

Decisão: usar `gemini-2.5-flash` na camada de extração. ADR-0002, PRD,
backlog, README e diagrama de arquitetura atualizados de "Gemini 2.0 Flash"
para "Gemini 2.5 Flash". `.env.example` criado (`GEMINI_API_KEY=`), `.env`
confirmado no `.gitignore`. Item "Gerar chave do Gemini" do backlog marcado
como `status::done`.
