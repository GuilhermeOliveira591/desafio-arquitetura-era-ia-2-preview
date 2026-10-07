import httpx

from . import config

_client = httpx.Client(
    base_url=config.PROVIDER_BASE_URL,
    headers={"Authorization": f"Bearer {config.PROVIDER_API_KEY}"},
    timeout=20.0,
)


def chat(messages: list[dict]) -> tuple[str, dict]:
    """Devolve o texto gerado e o objeto usage do provider."""
    response = _client.post("/chat/completions", json={"model": config.CHAT_MODEL, "messages": messages})
    response.raise_for_status()
    body = response.json()
    return body["choices"][0]["message"]["content"], body.get("usage", {})


def embed(texts: list[str]) -> list[list[float]]:
    response = _client.post("/embeddings", json={"model": config.EMBEDDING_MODEL, "input": texts})
    response.raise_for_status()
    data = sorted(response.json()["data"], key=lambda item: item["index"])
    return [item["embedding"] for item in data]
