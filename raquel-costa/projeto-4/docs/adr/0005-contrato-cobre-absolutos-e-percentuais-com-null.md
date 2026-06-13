# Contrato Semântico cobre valores absolutos e percentuais, com NULL explícito

O critério de avaliação exige que o pipeline extraia valores absolutos (ignorando
percentuais de variação usados como marketing). Porém o PDF de exemplo fornecido
(`exemplo_Boletim_Conjuntura_2025_3T.pdf`) contém **apenas** variações percentuais
(QoQ, YoY, 9m24/23, 9m25/24) por empresa/Indicador — nenhum valor absoluto
(R$, unidades) aparece nesse documento.

Decisão: o Contrato Semântico (Pydantic) inclui campos para valor absoluto E para
as variações percentuais desde o MVP. No PDF de exemplo, os campos de valor
absoluto resultam em NULL (tratamento explícito de ausentes, também exigido pelo
enunciado) — não é um bug, é o comportamento esperado para esse layout
específico. Prévias Operacionais de outras empresas (ex: MRV, fora do MVP)
tipicamente trazem valores absolutos, e o pipeline já está preparado para
capturá-los sem mudança de schema.

Alternativa descartada: restringir o schema do MVP a apenas percentuais, deixando
valores absolutos como dívida técnica — rejeitada porque o esquema é o artefato
mais avaliado e teria que ser refeito na primeira Prévia com valores absolutos.

## Status

accepted
