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

(A preencher na fase::1 do backlog.)

## 4. Camada B — Contrato Semântico e Chunking

(A preencher nas fases::2 do backlog. Decisões já registradas em
[ADR-0001](docs/adr/0001-pre-filtro-de-paginas-antes-da-llm.md),
[ADR-0002](docs/adr/0002-gemini-flash-com-saida-estruturada.md),
[ADR-0005](docs/adr/0005-contrato-cobre-absolutos-e-percentuais-com-null.md).)

## 5. Camada C — API REST

(A preencher na fase::4 do backlog.)

## 6. Modelo de dados e linhagem

(A preencher nas fases::1/3 do backlog. Decisão de modelo em
[ADR-0004](docs/adr/0004-modelo-de-dados-uma-linha-por-indicador.md).)

## 7. Gatilho de ingestão (próximos passos)

(Ver [`docs/planning/00-overview.md`](docs/planning/00-overview.md).)

## 8. Limitações conhecidas e próximos passos

- Validação com 2º layout de Prévia Operacional ainda não realizada
  (`fase::6` do backlog).
- Gatilho de ingestão (polling) ainda não implementado.
