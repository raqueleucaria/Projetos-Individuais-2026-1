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

## Status

accepted
