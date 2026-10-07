# hr-fake

O sistema de RH simulado: cadastro, folha e saldo de férias dos colaboradores de cada empresa cliente. É a fonte de verdade sobre a situação de cada colaborador, e os dados mudam ao longo do tempo (o saldo de férias diminui quando a pessoa tira férias, um benefício é incluído). Não altere este diretório.

Base URL no host: `http://localhost:8091`. Dentro do compose: `http://hr-fake:8091`. Os dados ficam em memória; reiniciar o container volta ao estado inicial.

```
GET   /tenants/{tenant_id}/employees/{employee_id}
      200 {"tenant_id", "employee_id", "name", "cpf", "salary", "vacation_days", "benefits": [...]}
      404 quando o colaborador não existe naquela empresa

PATCH /admin/tenants/{tenant_id}/employees/{employee_id}
      altera vacation_days, salary e/ou benefits, simulando uma mudança feita pelo RH
      ex.: {"vacation_days": 5}

POST  /admin/reset      volta todos os colaboradores ao estado inicial
GET   /health           200 {"status": "ok"}
```

Colaboradores no estado inicial:

| tenant_id | employee_id | Nome | Saldo de férias |
|---|---|---|---|
| `estrela` | `E001` | Ana Souza | 18 dias |
| `estrela` | `E002` | Carlos Lima | 7 dias |
| `boreal` | `B001` | Bruno Alves | 25 dias |
| `boreal` | `B002` | Daniela Rocha | 12 dias |
