# Golden dataset inicial

`golden.jsonl` traz um conjunto pequeno de perguntas reais dos colaboradores, com o comportamento esperado do assistente. Um item por linha:

| Campo | Significado |
|---|---|
| `id` | identificador estável do item |
| `token` | o token com que a pergunta é feita pela borda (define empresa e colaborador) |
| `question` | a pergunta |
| `expected_sources` | os `document_id` que a resposta deve citar, exatamente (lista vazia quando a resposta não vem de documento) |
| `required_terms` | trechos que precisam aparecer no texto da resposta |

Os valores esperados das perguntas pessoais (saldo de férias, benefícios) correspondem ao estado inicial do `hr-fake`.

Na aplicação recebida, rodados nesta ordem e logo depois de subir com o banco vazio (`docker compose down -v` antes de subir), todos os itens passam.
