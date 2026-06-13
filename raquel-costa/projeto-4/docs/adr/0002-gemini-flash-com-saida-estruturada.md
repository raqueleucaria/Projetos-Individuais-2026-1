# Gemini 2.0 Flash com saída estruturada (response_schema)

A camada de extração precisa de um LLM que aceite texto livre (saída do
Pré-filtro de Páginas) e retorne dados aderentes ao Contrato Semântico. Optamos
pelo Gemini 2.0 Flash (free tier do Google AI Studio), usando o parâmetro nativo
`response_schema` para forçar a saída no formato do Pydantic, em vez de GPT-4/
Claude (sem free tier viável para o prazo) ou de parsing manual de JSON livre
(mais frágil contra alucinações de formato).

A chave de API ainda não existe no momento deste planejamento; a geração da key
é uma tarefa p0 do backlog, com um modo mock/offline como fallback caso a key não
fique disponível a tempo.

## Status

accepted
