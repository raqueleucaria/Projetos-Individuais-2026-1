# PRD — Pipeline de Conjuntura do Setor Habitacional (UDA)

## Problem Statement

O Ministério das Cidades precisa consolidar dados operacionais (lançamentos e
vendas) de construtoras para o Relatório de Conjuntura do Setor Habitacional, mas
esses dados ficam pulverizados em Prévias Operacionais em PDF, publicadas
trimestralmente nas Centrais de Resultados de cada empresa, em layouts
diferentes entre empresas e ao longo do tempo.

## Solution

Um pipeline que: (A) coleta Prévias Operacionais e evita reprocessamento via
Idempotência (hash SHA-256); (B) usa um Pré-filtro de Páginas + Gemini 2.0 Flash
com Contrato Semântico (Pydantic) para extrair Indicadores (Lançamentos, Vendas)
por empresa/trimestre, com valores absolutos e percentuais, tratando ausentes
como NULL; (C) expõe os Indicadores via API REST filtrável por empresa e
período.

## User Stories

1. Como responsável pelo Relatório de Conjuntura, quero que o pipeline ignore
   Prévias Operacionais já processadas, para não gastar cota da API do Gemini
   reprocessando o mesmo PDF.
2. Como responsável pelo Relatório de Conjuntura, quero consultar os Indicadores
   de Lançamentos e Vendas de uma empresa em um trimestre específico via API, sem
   precisar abrir o PDF original.
3. Como responsável pelo Relatório de Conjuntura, quero que valores ausentes em
   uma Prévia (ex: valor absoluto não divulgado) apareçam como NULL na API, em
   vez de um valor inventado pela LLM.
4. Como auditor de dados, quero que cada Indicador no Catálogo de Dados aponte
   para a Prévia Operacional (Linhagem) de onde foi extraído, para validar a
   origem do dado.
5. Como desenvolvedor que vai estender o pipeline, quero que o Contrato Semântico
   já cubra valores absolutos (não só percentuais), para que Prévias de outras
   empresas (com valores absolutos) não exijam mudança de schema.
6. Como desenvolvedor que vai estender o pipeline, quero que o Pré-filtro de
   Páginas reduza o conteúdo enviado à LLM por meio de palavras-chave, para que
   Prévias longas (apresentações de slides) não inflem custo/latência.

## Implementation Decisions

- **Ingestão (MVP)**: lista fixa contendo 1 Prévia Operacional
  (`exemplo_Boletim_Conjuntura_2025_3T.pdf`, em `data/`). Gatilho via
  agendamento/polling fica documentado como próximo passo (fora do MVP), ver
  [`00-overview.md`](./00-overview.md) e [Out of Scope](#out-of-scope).
- **Idempotência**: SHA-256 do conteúdo do PDF, calculado antes de qualquer
  chamada à LLM. Ver [ADR-0003](../adr/0003-idempotencia-via-sha256-em-sqlite.md).
- **Pré-filtro de Páginas**: extração de texto por página via PyMuPDF, seleção
  das páginas que contêm palavras-chave (`lançamentos`, `vendas`, `VGV`,
  `unidades`, e variantes). Ver [ADR-0001](../adr/0001-pre-filtro-de-paginas-antes-da-llm.md).
- **Extração**: o texto das páginas selecionadas pelo Pré-filtro (não o PDF como
  arquivo) é enviado ao Gemini 2.0 Flash via API, com `response_schema` derivado
  do Contrato Semântico (Pydantic). Ver [ADR-0002](../adr/0002-gemini-flash-com-saida-estruturada.md).
- **Contrato Semântico** (Pydantic, por Indicador extraído):
  - `empresa: str`
  - `ano: int`
  - `trimestre: int` (1-4)
  - `indicador: Literal["lancamentos", "vendas"]`
  - `valor_absoluto: float | None` — NULL quando não divulgado
  - `var_qoq: float | None` — variação trimestre anterior, em %
  - `var_yoy: float | None` — variação mesmo trimestre ano anterior, em %
  - `var_acumulado_aa: float | None` — variação acumulado 9m/ano-a-ano, em %
  - Empresa especial `"TOTAL_SETOR"` para os totais agregados do boletim.
  - Ver [ADR-0005](../adr/0005-contrato-cobre-absolutos-e-percentuais-com-null.md).
- **Modelo de dados (SQLite)**:
  - Tabela `relatorios`: `hash (PK)`, `url_origem`, `arquivo_local`,
    `data_processamento`.
  - Tabela `indicadores`: `id (PK)`, `relatorio_hash (FK -> relatorios.hash)`,
    `empresa`, `ano`, `trimestre`, `indicador`, `valor_absoluto`, `var_qoq`,
    `var_yoy`, `var_acumulado_aa`.
  - Ver [ADR-0004](../adr/0004-modelo-de-dados-uma-linha-por-indicador.md).
- **API (FastAPI)**: `GET /api/conjuntura?empresa=&ano=&trimestre=` retornando a
  lista de Indicadores que casam os filtros informados (filtros opcionais),
  incluindo o `relatorio_hash` e `url_origem` (Linhagem) de cada linha.
- **Stack**: Python, pip + `requirements.txt` + venv. Bibliotecas previstas:
  `pymupdf`, `google-generativeai` (ou `google-genai`), `pydantic`, `fastapi`,
  `uvicorn`, `sqlite3` (stdlib).
- **Config**: chave do Gemini via variável de ambiente (`.env`, não versionado).
  Modo mock/offline (sem chamar a API) como fallback caso a chave não esteja
  disponível — ver backlog item de geração de key.

## Testing Decisions

- Testes unitários do Contrato Semântico: validar que campos ausentes resultam
  em `None`/NULL e que tipos/ranges (ex: `trimestre` 1-4) são respeitados.
- Teste de integração da Idempotência: processar o mesmo PDF duas vezes e
  verificar que a segunda execução não chama a LLM (mockada) e não duplica
  linhas em `indicadores`.
- Teste de integração da API: dado um Catálogo de Dados populado via fixture,
  `GET /api/conjuntura?empresa=MRV&ano=2025&trimestre=3` retorna as linhas
  esperadas e filtros parciais (só `empresa`, ou nenhum filtro) funcionam.
- Chamadas reais ao Gemini não são exercitadas em testes automatizados (custo/
  rede); usar fixtures com a resposta esperada da LLM para testar o
  parsing/validação do Contrato Semântico.

## Out of Scope

- Gatilho de ingestão automatizado (polling/cron, webhooks/RSS) — documentado
  como próximo passo em `docs/planning/00-overview.md`, não implementado no MVP.
- Segundo layout de Prévia Operacional (ex: apresentação de slides da MRV) para
  validar resiliência — adiado para pós-MVP (ver backlog).
- Interface gráfica (explicitamente fora do critério de avaliação do
  enunciado).
- Chunking Semântico completo (árvores hierárquicas / RAG) — o MVP usa
  Pré-filtro de Páginas por palavras-chave, ver ADR-0001.

## Further Notes

- O PDF de exemplo fornecido contém apenas variações percentuais, sem valores
  absolutos — ver ADR-0005 para como o Contrato Semântico lida com essa lacuna.
- Prazo de entrega: 13/06/2026 23:59.
