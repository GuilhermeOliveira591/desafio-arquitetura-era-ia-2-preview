# provider-fake

Um provider de modelos simulado, no formato da API da OpenAI (Chat Completions e Embeddings). Responde de forma determinística, conta tokens, cobra por eles, simula prompt caching e registra cada chamada. Existe para que o desafio seja reproduzível sem chave paga e para que o avaliador consiga conferir o que aconteceu em cada requisição.

Não altere este diretório.

## Acesso

| | Valor |
|---|---|
| Base URL no host | `http://localhost:8090/openai/v1` |
| Base URL dentro do compose | `http://provider-fake:8090/openai/v1` |
| Autenticação | `Authorization: Bearer <FAKE_OPENAI_KEY>` (valor no `.env.example`) |

O SDK oficial `openai` funciona apontando a base URL. Streaming não é implementado: `stream: true` responde `400`.

## Modelos

| Modelo | Tipo | Detalhes | US$ por 1M tokens |
|---|---|---|---|
| `gpt-fake-large` | chat | contexto de 16.000 tokens | entrada 2,50; entrada lida do cache 0,25; saída 10,00 |
| `text-embedding-fake` | embeddings | vetores de 256 dimensões, normalizados | entrada 0,02 |

- Tokens são contados como `ceil(caracteres / 4)`. No chat, a entrada é contada sobre a serialização das mensagens: para cada mensagem, `<|papel|>`, quebra de linha, o conteúdo e outra quebra de linha.
- A saída é determinística: a mesma entrada gera sempre a mesma resposta e o mesmo vetor.
- Latência do chat: 0,3 s, mais 0,4 ms por token de entrada que não veio do cache, mais o tempo de gerar a saída a 100 tokens/s.

## Embeddings

`POST /openai/v1/embeddings` com `{"model": "text-embedding-fake", "input": "texto"}` (ou uma lista de textos). A resposta segue o formato da OpenAI (`data[].embedding`, `usage`).

O vetor representa as palavras relevantes do texto: textos que usam as mesmas palavras, mesmo em outra ordem, com ou sem acento, maiúsculas ou pontuação, ficam muito próximos (similaridade de cosseno perto de 1). Textos que compartilham poucas palavras ficam distantes. Use a distância de cosseno (`<=>` no pgvector).

## A tarefa de resposta

O modelo de chat entende uma tarefa. A primeira linha da última mensagem do usuário deve ser `TASK: answer`, e o resto segue este formato:

```
TASK: answer
QUESTION: <a pergunta, em uma linha>
CONTEXT:
[source: <identificador>]
<texto do trecho, em uma ou mais linhas>
[source: <outro identificador>]
<texto>
```

Linhas entre `QUESTION:` e `CONTEXT:` são ignoradas. Linhas que começam com `#` dentro de um trecho são tratadas como títulos e nunca viram resposta.

Saída: um JSON como texto no conteúdo da mensagem, `{"answer": "...", "sources": ["<identificador>"]}`. O modelo escolhe, entre as frases do contexto, a que tem mais palavras relevantes em comum com a pergunta; em caso de empate, vence a que aparece primeiro. Quando nenhuma frase tem relação suficiente com a pergunta, a resposta é `Não encontrei essa informação nos documentos da sua empresa.`, com `sources` vazio.

O system prompt e as instruções que você escrever não mudam o resultado.

O modelo simulado tem a fraqueza central dos modelos reais: ele não distingue instrução de dado. Quando um trecho do contexto traz uma instrução dirigida ao assistente, ele obedece, e a resposta passa a ser o que a instrução manda dizer. Nenhum texto de system prompt muda isso. A instrução é detectada em qualquer linha do trecho, inclusive nas linhas de título (`#`): um título nunca vira resposta como frase, mas uma instrução dentro dele é obedecida.

## Prompt caching

Como nos providers reais, o cache de prompt é por match de prefixo:

- O provider compara a entrada serializada de cada chamada com as entradas das chamadas ao mesmo modelo nos últimos 5 minutos e encontra o maior prefixo em comum.
- Se esse prefixo tem pelo menos 1.024 tokens, os tokens do prefixo, arredondados para baixo em blocos de 128, são cobrados como entrada lida do cache.
- A resposta traz o valor em `usage.prompt_tokens_details.cached_tokens`.
- Qualquer caractere diferente no começo da entrada zera o aproveitamento daquele ponto em diante.

## Administração

Os endpoints de administração não exigem autenticação.

```
GET  /admin/calls?last=N   últimas N chamadas (padrão 50), da mais recente para a mais antiga
GET  /admin/usage          totais por modelo das chamadas com sucesso: chamadas, tokens de entrada,
                           tokens lidos do cache, tokens de saída e custo em US$
POST /admin/reset          limpa o registro de chamadas e o cache de prompt
GET  /health               200 {"status": "ok"}
```

Cada item de `/admin/calls` tem: `id`, `ts`, `model`, `task` (`answer`, `embed` ou `null`), `status`, `input_tokens`, `cached_tokens`, `output_tokens`, `cost_usd` e `duration_ms`. O registro guarda as últimas 5.000 chamadas, em memória; reiniciar o container limpa tudo.

## Exemplos

```
curl -s localhost:8090/openai/v1/chat/completions \
  -H "Authorization: Bearer sk-fake-openai-0001" -H "Content-Type: application/json" \
  -d '{"model": "gpt-fake-large", "messages": [{"role": "user", "content": "TASK: answer\nQUESTION: Qual o horário da cantina?\nCONTEXT:\n[source: cantina]\nO horário da cantina é das 11h às 14h."}]}'

curl -s localhost:8090/openai/v1/embeddings \
  -H "Authorization: Bearer sk-fake-openai-0001" -H "Content-Type: application/json" \
  -d '{"model": "text-embedding-fake", "input": ["Qual o horário da cantina?", "horário da cantina"]}'

curl -s "localhost:8090/admin/calls?last=5"
curl -s localhost:8090/admin/usage
```

## Testes do próprio provider

Com o compose no ar:

```
pip install -r provider-fake/tests/requirements.txt
pytest provider-fake/tests -q
```
