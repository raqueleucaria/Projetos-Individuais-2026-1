# Gatilho de ingestão por polling (próximo passo, fora do MVP)

O enunciado pede uma estratégia para **detectar novas Prévias Operacionais**
publicadas nas Centrais de Resultados (RI) das construtoras, sem que alguém
precise baixar e alimentar o pipeline manualmente. O MVP atual processa uma
lista fixa (o PDF de exemplo em `data/`); este documento descreve como a
ingestão automática se encaixaria, **reaproveitando a Idempotência já
implementada** (fase::1), sem nova implementação no escopo do MVP.

## Estratégia recomendada: polling

A maioria dos portais de RI das construtoras-alvo **não publica feed RSS nem
webhook**, então não há um canal de _push_ confiável para novos documentos. A
estratégia recomendada é **polling**: visitar periodicamente as páginas de
Central de Resultados, descobrir os links de PDF e comparar com o que já foi
processado.

### Frequência sugerida

Prévias Operacionais são divulgadas em ciclo **trimestral** (poucos dias após o
fim de cada trimestre fiscal). Não há ganho em verificar de hora em hora.

- **Polling diário** (1×/dia, ex: cron às 08:00) é suficiente e barato.
- Janelas de maior probabilidade de publicação: primeiras ~3 semanas após o
  fim de cada trimestre (abril, julho, outubro, janeiro). Opcionalmente, o cron
  pode rodar com maior frequência (ex: a cada 6h) apenas nessas janelas.

### Fontes (Centrais de Resultados / RI)

As empresas-alvo (as mesmas que aparecem na Prévia de exemplo) e seus portais
de Relações com Investidores. **As URLs exatas das páginas de "Central de
Resultados" / "Comunicados e Fatos Relevantes" devem ser confirmadas antes da
implementação** (os portais mudam de caminho com frequência):

| Empresa        | Portal de RI (base)            |
| -------------- | ------------------------------ |
| MRV            | ri.mrv.com.br                  |
| Cury           | ri.cury.net                    |
| Tenda          | ri.tenda.com                   |
| Plano & Plano  | ri.planoeplano.com.br          |
| Direcional     | ri.direcional.com.br           |
| Pacaembu       | ri.pacaembu.com                |

Para cada portal, o coletor procura, na página de resultados/comunicados, os
links `<a href="...pdf">` cujo texto/título contenha termos como "Prévia
Operacional", "Prévia", "Operacional" ou o trimestre (ex: "3T25").

## Como se encaixa na Idempotência (fase::1)

O ponto-chave é que o gatilho de polling **não precisa de estado próprio para
saber o que já foi processado** — ele delega isso ao Catálogo de Dados via o
hash SHA-256 (ver [ADR-0003](../adr/0003-idempotencia-via-sha256-em-sqlite.md)).

Fluxo proposto do coletor:

1. Para cada portal de RI, listar os links de PDF candidatos (filtro por
   palavras-chave no texto do link).
2. Baixar cada PDF candidato para um arquivo temporário.
3. Chamar `processar_pdf(caminho_pdf, url_origem=<link>)`
   ([`src/uda/pipeline.py`](../../src/uda/pipeline.py)).
4. O próprio `processar_pdf` calcula o hash do conteúdo, consulta
   `relatorio_existe` e:
   - retorna `"ignorado"` se o PDF já foi processado (hash já em `relatorios`)
     — caso comum no polling diário, já que o mesmo PDF reaparece todo dia;
   - retorna `"processado"` e persiste os Indicadores se for um documento novo.

Consequências dessa delegação:

- **Dedup por conteúdo, não por URL.** Se a empresa republicar o mesmo PDF em
  outra URL, o hash idêntico evita reprocessamento. Se corrigir o documento
  (conteúdo diferente), o novo hash é tratado como um documento novo.
- **Sem tabela de "URLs já vistas".** O coletor pode ser _stateless_: a única
  fonte de verdade sobre "já processei isto?" é a tabela `relatorios`.
- **Reexecução segura.** Rodar o coletor várias vezes ao dia (ou após uma
  falha parcial) não duplica dados.

## Fora de escopo no MVP

- Implementação do coletor/cron em si.
- Tratamento de portais com JavaScript pesado (alguns RI carregam a lista de
  documentos via XHR) — exigiria um cliente que execute JS ou uma chamada à
  API interna do portal, a ser avaliado por empresa.
- Notificação/alerta quando um novo documento é processado.
