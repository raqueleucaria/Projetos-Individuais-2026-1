# Modelo de dados: uma linha por (empresa, ano, trimestre, indicador)

A tabela de Indicadores no Catálogo de Dados usa granularidade fina: cada linha
representa um Indicador (ex: Lançamentos, Vendas) de uma empresa em um trimestre,
com colunas para valor absoluto e variações percentuais (QoQ, YoY, acumulado 9
meses). Totais agregados do setor (ex: "Total lançamentos +14%") são registrados
com `empresa = "TOTAL_SETOR"`.

A alternativa considerada — uma linha por (empresa, trimestre) com colunas wide
(uma coluna por indicador × variação) — foi descartada porque o enunciado pede
resiliência a layouts diferentes, que podem trazer Indicadores adicionais (ex:
VGV, repasses, distratos) não previstos hoje. O modelo fino permite adicionar
novos tipos de Indicador sem alterar o schema da tabela, apenas o vocabulário de
valores aceitos para a coluna `indicador`.

A chave lógica da linha foi posteriormente estendida para incluir `variante`
(recortes do mesmo indicador, ex: com/ex-permuta) e a unidade do valor absoluto
foi explicitada — ver [ADR-0007](0007-variante-e-unidade-no-contrato.md).

## Status

accepted
