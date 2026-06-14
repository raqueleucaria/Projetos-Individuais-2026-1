# Benchmark de qualidade da leitura

Medição objetiva da qualidade da extração, comparando a saída do pipeline
contra uma verdade-base (golden dataset) em `benchmark/golden/`. As métricas
são mapeadas aos critérios de avaliação do desafio.

## Como rodar

```bash
# Relatório (roda o pipeline real; baixa PDFs de terceiros sob demanda):
PYTHONPATH=src python -m uda.benchmark

# Asserts de qualidade separados por PDF (offline, via snapshot — rodam no CI):
PYTHONPATH=src pytest tests/test_benchmark_qualidade.py -q

# Testes determinísticos do medidor (sem LLM):
PYTHONPATH=src pytest tests/test_benchmark_metrics.py -q
```

## Separação por PDF e snapshots

Os asserts são **separados por PDF**, conforme a `fonte` do golden:

- **`boletim_3T25` (`fonte: data`)** — PDF versionado em `data/`. Roda no
  benchmark ao vivo e tem assert offline no CI.
- **`cyrela_3T25` (`fonte: externo`)** — PDF de terceiros que **não está em
  `data/`**. No benchmark ao vivo é baixado sob demanda; nos testes do CI a
  qualidade é checada contra um **snapshot** gravado em `benchmark/snapshots/`,
  sem precisar do PDF.

Cada `benchmark/snapshots/<nome>.json` é uma gravação de uma extração real; o
assert compara golden × snapshot de forma determinística
(`tests/test_benchmark_qualidade.py`). Regravar um snapshot que divergir do
golden além da tolerância faz o teste falhar — sinalizando regressão. A deriva
do LLM ao vivo é verificada rodando `python -m uda.benchmark`.

## Métricas

| Métrica | O que mede | Critério de avaliação |
| --- | --- | --- |
| `cobertura` | recall: linhas esperadas que foram extraídas | robustez |
| `precisao` | linhas extraídas que eram esperadas (penaliza alucinação) | robustez |
| `acuracia_numerica` | campos numéricos corretos (tol. ±0,5 p.p.; absolutos ±1%) | extração de valores |
| `disciplina_null` | campos NULL esperados que vieram NULL | Contrato Semântico |
| `consistencia_temporal` | linhas com `ano`/`trimestre` corretos | modelagem temporal |

## Resultado (2026-06-13, `gemini-2.5-flash`)

| PDF | esperadas | extraídas | cobertura | precisão | acur. num. | disc. NULL | temporal |
| --- | --- | --- | --- | --- | --- | --- | --- |
| boletim_3T25 | 14 | 14 | 100% | 100% | 100% | 100% | 100% |
| cyrela_3T25 | 3 | 6 | 100% | 50% | 100% | 100% | 100% |

### Leitura dos números

- **boletim_3T25** (PDF versionado, agregado, só percentuais): 100% em todas as
  métricas — referência limpa e reprodutível. Em especial, `disciplina_null`
  100% confirma que o pipeline **não inventa** valores absolutos onde o
  documento só traz percentuais.
- **cyrela_3T25** (PDF de terceiros, baixado sob demanda; empresa única com
  valores absolutos): as métricas de **qualidade** são 100% — achou os 3
  âncoras de valor absoluto (R$ 5.050M / 3.411M / 2.459M), com numéricos
  corretos e sem alucinar NULLs. A `precisao` 50% **não indica erro de
  leitura**: o golden da Cyrela é um subconjunto mínimo *verificado* (3 linhas),
  enquanto o pipeline extrai linhas reais adicionais (permutas R$ 126M, vendas
  com permuta R$ 3.547M) e a contagem "18 empreendimentos" colide na chave
  `(empresa, indicador, variante)` com a linha de lançamentos com permuta. São
  limitações do golden/chave, não da extração.

## Notas de modelagem

- A tabela do boletim tem 4 colunas de variação (X 2T25, X 3T24, 9m 24/23,
  9m 25/24); o schema modela 3 (`var_qoq`, `var_yoy`, `var_acumulado_aa`), com
  `var_acumulado_aa = 9m 25/24`. A coluna `9m 24/23` não é capturada — decisão
  consciente refletida na verdade-base.
- O golden suporta `pdf_path` (versionado) e/ou `pdf_url` (download sob
  demanda). PDFs de terceiros não são versionados; entradas sem PDF disponível
  são puladas. Adicionar um novo layout é só incluir um JSON em
  `benchmark/golden/`.
