# Fallback Gemini Vision para PDFs sem camada de texto

O Pré-filtro de Páginas (ADR-0001) depende de texto extraível via PyMuPDF
(`get_text()`/`find_tables()`). Prévias Operacionais, porém, aparecem em
layouts variados, e algumas são PDFs **escaneados** (imagem, sem camada de
texto) — nesse caso a extração de texto retorna vazio e o pipeline enviaria
conteúdo nulo à LLM, falhando silenciosamente.

Decisão: antes da extração, classificar o PDF pela presença de camada de texto
(`tem_camada_de_texto`, somando o texto extraível das páginas). Se o total
ficar abaixo de um limiar mínimo, o pipeline trata o documento como escaneado e
recorre ao **Gemini Vision**: as páginas são renderizadas como imagens PNG e
enviadas ao mesmo modelo (`gemini-2.5-flash`) com o **mesmo** `response_schema`
do Contrato Semântico, garantindo saída idêntica (ADR-0002, ADR-0005).

Alternativa descartada: stack de OCR dedicado (Marker / PaddleOCR / Surya).
Traria dependências de ML pesadas e custo de GPU injustificáveis para o escopo
e o free tier; o Gemini Vision cobre o mesmo caso (documento sem texto) sem
dependências adicionais — o `fitz` (renderização) e o `google-genai` já fazem
parte do projeto. O número de páginas enviadas ao Vision é limitado
(`MAX_PAGINAS_VISION`) para conter custo/tokens.

Isso fecha a resiliência a um 2º layout (`fase::6` do backlog) no caso de
Prévias escaneadas, sem alterar o caminho principal (PDFs nativos digitais).

## Status

accepted
