# Pré-filtro de páginas antes de enviar conteúdo à LLM

A extração de Indicadores precisa decidir entre Full-Scan (enviar todo o texto do
PDF à LLM) e Chunking Semântico completo (segmentação por estrutura/título com
recuperação seletiva). Optamos por uma estratégia intermediária: PyMuPDF extrai o
texto de cada página do PDF localmente, e um Pré-filtro de Páginas baseado em
palavras-chave (ex: "lançamentos", "vendas", "VGV", "unidades") seleciona apenas
as páginas candidatas. Só o **texto** dessas páginas (não o PDF como arquivo) é
enviado ao Gemini, reduzindo diretamente o volume de tokens do prompt — daí a
economia de custo/uso da API.

Mesmo o PDF de exemplo (poucas páginas) já demonstra a viabilidade da técnica;
o ganho de custo/latência fica mais evidente em Prévias Operacionais maiores
(ex: apresentações de slides com dezenas de páginas), que são o caso geral do
desafio. Full-Scan puro foi descartado por não escalar para esses documentos, e
Chunking Semântico completo (árvores hierárquicas/RAG) foi descartado pelo
trade-off de tempo de implementação dado o prazo de 1 dia.

## Extração table-aware (Markdown)

Para cada página selecionada, o conteúdo enviado à LLM não é o texto plano
(`get_text()`), e sim **Markdown** gerado a partir das tabelas detectadas com
`page.find_tables()` (PyMuPDF) mais o texto fora das tabelas. Os dados das
Prévias são essencialmente tabulares (empresa × indicador); preservar o
alinhamento linha/coluna em tabelas Markdown reduz erros de associação
(empresa↔valor) e alucinação na extração, comparado ao texto achatado, onde
colunas e linhas se misturam. O texto fora da área das tabelas é mantido (sem
duplicar o que já está estruturado) para preservar cabeçalhos como o trimestre
de referência.

## Status

accepted
