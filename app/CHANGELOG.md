# Changelog do assistente

## 2026-08-12
- O assistente passa a receber a data e a hora atuais no início das instruções do modelo. Pedido do produto: responder perguntas que dependem do dia, como prazos de solicitação de férias.

## 2026-07-20
- Cache semântico de respostas no pgvector: perguntas parecidas reaproveitam uma resposta já gerada (similaridade mínima de 0,92). Objetivo: reduzir custo e tempo de resposta.

## 2026-07-01
- Cache exato de respostas: a mesma pergunta não chama o modelo de novo.

## 2026-06-10
- O RH de cada empresa publica e revoga documentos pelo painel (`/admin/documents`), com reindexação automática.

## 2026-05-15
- Traces enviados ao Jaeger com a pergunta, o prompt e a resposta, para facilitar o atendimento do suporte.

## 2026-05-02
- Lançamento do assistente para as duas primeiras empresas clientes: Padaria Estrela e Metalúrgica Boreal.
