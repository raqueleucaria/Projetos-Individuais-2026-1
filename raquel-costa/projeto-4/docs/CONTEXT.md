# Pipeline de Conjuntura do Setor Habitacional (UDA)

Pipeline de Engenharia/Análise de Dados Não Estruturados (UDA) que extrai, via LLM,
métricas operacionais (lançamentos e vendas) de PDFs de Relações com Investidores
(RI) de construtoras, e as expõe via API para alimentar o Relatório de Conjuntura
do Setor Habitacional.

## Language

**Prévia Operacional**:
Documento em PDF publicado por uma construtora logo após o fim do trimestre, com
dados brutos de obras/vendas (lançamentos, vendas, VGV, unidades). É o tipo de
documento de entrada que o pipeline coleta e processa.
_Avoid_: Relatório financeiro, demonstração de resultados (DRE) — são documentos
mais extensos e fora do escopo deste pipeline.

**Central de Resultados**:
Seção do portal de Relações com Investidores (RI) de uma construtora onde as
Prévias Operacionais e relatórios financeiros são publicados, organizados por
ano e trimestre.
_Avoid_: Central de downloads, área do investidor (usar como sinônimos do mesmo
conceito, mas o termo canônico é "Central de Resultados").

**Indicador**:
Uma métrica operacional rastreada pelo pipeline para uma empresa em um trimestre
(ex: Lançamentos, Vendas). Cada indicador carrega um valor absoluto (quando
disponível na Prévia) e variações percentuais (QoQ, YoY, acumulado 9 meses).
_Avoid_: Métrica (usar "Indicador" como termo canônico no contrato semântico e no
catálogo).

**Contrato Semântico**:
O esquema (Pydantic/JSON Schema) que define os campos, tipos e regras de
preenchimento (incluindo NULL para ausentes) que a saída da LLM deve obedecer ao
extrair Indicadores de uma Prévia Operacional. É a camada de blindagem contra
alucinações e variações de layout.
_Avoid_: Schema de extração (usar "Contrato Semântico" como termo canônico).

**Catálogo de Dados**:
O repositório (SQLite) que registra cada Prévia Operacional processada (por hash)
e os Indicadores extraídos dela, preservando a Linhagem.
_Avoid_: Banco de dados, base de dados (usar "Catálogo de Dados" quando o foco for
o papel de registro/idempotência; "banco" é aceitável em contexto puramente
técnico de implementação).

**Linhagem**:
A associação entre uma linha de Indicador no Catálogo de Dados e a Prévia
Operacional (PDF/URL/hash) de onde ela foi extraída, permitindo rastrear a origem
de qualquer valor.
_Avoid_: Rastreabilidade, proveniência.

**Pré-filtro de Páginas**:
Etapa que reduz o conjunto de páginas de uma Prévia Operacional às páginas
candidatas a conter Indicadores (via busca de palavras-chave como "lançamentos",
"vendas", "VGV", "unidades"), antes de enviar o conteúdo à LLM. Reduz custo/tokens
sem ser uma estratégia de Chunking Semântico completa.
_Avoid_: Chunking (ver "Chunking Semântico" — são estratégias diferentes; o
Pré-filtro de Páginas é mais simples).

**Idempotência**:
Propriedade do pipeline de não reprocessar (e não re-chamar a LLM para) uma
Prévia Operacional já registrada no Catálogo de Dados, verificada via hash
SHA-256 do conteúdo do PDF.
_Avoid_: Deduplicação (usar "Idempotência" como termo canônico, pois o foco é
evitar custo de reprocessamento, não apenas remover duplicatas).
