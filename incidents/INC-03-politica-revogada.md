# INC-03: benefício revogado continua sendo oferecido

- Aberto em: 2026-09-15
- Empresa: Padaria Estrela
- Aberto por: RH da Padaria Estrela
- Severidade atribuída pelo suporte: alta

## Relato

"Revogamos o auxílio academia em 1º de setembro e removemos o documento pelo painel. O documento não aparece mais na nossa lista, mas o assistente continua dizendo aos colaboradores que o auxílio é de R$ 80,00 por mês e cita o documento como fonte. Já recebemos 14 pedidos de reembolso de academia."

## O que o suporte já verificou

- `GET /admin/documents` (com o token do RH da Estrela) não lista mais o `auxilio-academia`.
- A remoção respondeu com sucesso e disparou a reindexação.
- Perguntas sobre academia feitas com palavras diferentes das que os colaboradores já tinham usado também recebem o valor antigo.
