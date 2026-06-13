# Validação com 2º layout de Prévia Operacional (fase::6)

Validação da resiliência do pipeline contra uma Prévia Operacional real em
layout diferente do PDF de exemplo. Critério de aceite da `fase::6`: processar
um PDF de outro layout e documentar as diferenças de comportamento.

## Documento testado

- **Empresa:** Cyrela Brazil Realty (B3: CYRE3).
- **Documento:** Prévia Operacional 3T25 (`origin: api.mziq.com`), 8 páginas.
- **Layout:** comunicado de **empresa única**, em **prosa + tabelas** (parágrafos
  como "A Companhia lançou 18 empreendimentos... R$ 5.050 milhões, 62% superior
  ao 3T24..."), com **valores absolutos** em R$ milhões — diferente do PDF de
  exemplo, que é um **boletim agregado** de 6 empresas só com **percentuais**.
- O documento **não** foi versionado (PDF de terceiros); rodado a partir de cópia
  local, com `url_origem` apontando para a fonte.

## Resultado: processado com sucesso

O pipeline rodou ponta-a-ponta (`status=processado`) pelo caminho de texto
(o PDF tem camada de texto). Pontos confirmados:

- **`valor_absoluto` agora é populado** — ao contrário do exemplo (sempre NULL),
  aqui vêm R$ 5.050M / R$ 3.411M (lançamentos) e R$ 2.459M (vendas), validando
  que o Contrato Semântico (ADR-0005) cobre absolutos quando presentes.
- **Números conferem com a fonte:**
  - Lançamentos (com permuta): R$ 5.050M, +22% QoQ, +62% YoY — bate com o texto.
  - Lançamentos ex-permuta (%CBR): R$ 3.411M, +19% QoQ, +38% YoY, +105% no ano
    (R$ 9.658M vs R$ 4.711M) — bate com o texto.
  - Permutas: R$ 126M (vs R$ 195M no 2T25 = −35%; vs R$ 98M no 3T24 = +29%).
  - Vendas ex-permuta (%CBR): R$ 2.459M — bate com o título do comunicado.
- **Extração table-aware (ADR-0001)** e **geração determinística** funcionaram
  sem ajustes para o novo layout.

## Diferenças de comportamento observadas

1. **Rótulo `empresa` impreciso em doc de empresa única.** O prompt instrui usar
   `TOTAL_SETOR` para totais do setor — conceito do boletim agregado. Num
   comunicado de uma empresa só, o modelo aplicou `TOTAL_SETOR` a algumas linhas
   que, na verdade, são recortes da própria Cyrela (com permuta / permutas /
   total de vendas). Em vez de "setor", deveriam todas ser "Cyrela".
2. **Múltiplas linhas por (empresa, indicador).** O modelo de dados assume uma
   linha por (empresa, ano, trimestre, indicador) (ADR-0004). Este layout expõe
   **variantes** do mesmo indicador (com permuta, ex-permuta %CBR, permutas),
   gerando 3 linhas de "lançamentos". O schema não distingue essas variantes.
3. **Unidade ambígua em `valor_absoluto`.** Uma linha trouxe `valor_absoluto=18`
   (contagem: "18 empreendimentos"), convivendo com R$ milhões na mesma coluna.
   O Contrato não tem campo de **unidade**, então contagem e R$ ficam
   indistinguíveis.

## Recomendações (próximos passos)

- **Generalizar o rótulo de empresa:** ajustar o prompt para usar o nome da
  empresa do cabeçalho quando o documento for de emissor único, reservando
  `TOTAL_SETOR` para boletins agregados.
- **Campo `unidade`/`variante` no Contrato:** acrescentar `unidade`
  ("R$_milhoes" | "unidades" | "empreendimentos") e/ou `variante`
  ("com_permuta" | "ex_permuta") para desambiguar absolutos e variantes — sem
  quebrar o modelo de uma-linha-por-indicador (a chave passaria a incluir a
  variante).

Estas são evoluções de robustez; o critério da `fase::6` (processar 2º layout +
documentar diferenças) está atendido.
