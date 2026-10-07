# INC-06: CPF e salário na telemetria

- Aberto em: 2026-09-25
- Empresa: todas (plataforma)
- Aberto por: Encarregado de dados (DPO) da Vereda RH
- Severidade atribuída pelo suporte: alta

## Relato

"Numa auditoria de acesso a dados pessoais, encontramos CPF e salário de colaboradores das empresas clientes nos traces do Jaeger de produção. Todo o time de engenharia tem acesso ao Jaeger, e os traces ficam guardados por semanas. O suporte diz que precisa ver o que o assistente recebeu para investigar reclamações. Precisamos das duas coisas: investigar incidentes e não espalhar dado pessoal."

## O que o suporte já verificou

- Os dados aparecem em traces de perguntas sobre a situação do próprio colaborador (férias, benefícios).
- A aplicação roda com `APP_ENV=production`.
