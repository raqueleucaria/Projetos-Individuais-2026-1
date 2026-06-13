# `variante` e `unidade` no Contrato Semântico

A validação com um 2º layout (Prévia 3T25 da Cyrela — ver
[`../planning/validacao-2-layout.md`](../planning/validacao-2-layout.md))
expôs duas ambiguidades no Contrato original (ADR-0004, ADR-0005):

1. **Variantes do mesmo indicador.** Comunicados de empresa única apresentam o
   mesmo indicador em recortes diferentes (lançamentos "com permuta", "ex-permuta
   %CBR", "permutas"). Com a chave `(empresa, ano, trimestre, indicador)`, esses
   recortes colidiam em linhas indistinguíveis.
2. **Unidade de `valor_absoluto`.** O campo misturava R$ milhões com contagens
   (ex: "18 empreendimentos"), sem como diferenciar a unidade.

Decisão: estender `IndicadorExtraido` (e a tabela `indicadores`) com dois
campos opcionais:

- **`variante`** (`str | None`): recorte do indicador — `"com_permuta"`,
  `"ex_permuta"`, `"permutas"`, ou `NULL` quando não há recorte. Passa a fazer
  parte da chave lógica da linha: `(empresa, ano, trimestre, indicador,
  variante)`.
- **`unidade`** (`Literal["R$_milhoes", "unidades", "empreendimentos", "m2"]
  | None`): unidade de `valor_absoluto`; `NULL` quando o valor absoluto é `NULL`.

Ambos são **opcionais e retrocompatíveis**: o boletim agregado de exemplo (só
percentuais) continua com `variante=NULL` e `unidade=NULL`, sem mudança de
comportamento. A API ganhou filtros opcionais `variante` e `unidade`.

Em conjunto, o prompt de extração foi generalizado para usar o nome da empresa
emissora em documentos de empresa única, reservando `TOTAL_SETOR` apenas para
totais agregados de várias empresas — corrigindo o uso indevido observado na
validação.

Migração: `catalogo.db` é artefato gerado por `init_db` (não versionado,
recriado), então a mudança de schema não exige migração de dados.

## Status

accepted
