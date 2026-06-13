# Vocabulário de labels do backlog (markdown)

Como este repositório não tem issue tracker do GitHub, o backlog vive em
`docs/planning/backlog.md` e usa labels textuais no estilo `categoria::valor`,
inspiradas no fluxo de `/triage`.

## Labels

- **fase::N** — fase do plano de implementação a que o item pertence (`fase::0`
  = setup, `fase::1`, `fase::2`, ... conforme o backlog).
- **type::feature | type::chore | type::spike** — natureza do item.
  - `feature`: entrega funcional do pipeline (extração, API, etc.)
  - `chore`: setup, configuração, infraestrutura.
  - `spike`: investigação/exploração com resultado incerto (ex: obter PDF de
    outro layout).
- **priority::p0 | priority::p1 | priority::p2** — prioridade dado o prazo de
  13/06 23:59.
  - `p0`: bloqueador do MVP (sem isso, nada funciona).
  - `p1`: necessário para atender aos critérios de avaliação do enunciado.
  - `p2`: desejável, mas pode ficar para depois do prazo.
- **status::todo | status::doing | status::done** — estado atual do item.

## Exemplo de item

```md
### [fase::0] [type::chore] [priority::p0] [status::todo] Configurar projeto e dependências

Descrição...

**Critérios de aceite:**
- ...
```
