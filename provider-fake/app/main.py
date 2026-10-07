"""Provider simulado no formato da OpenAI: Chat Completions e Embeddings, com prompt caching."""

import asyncio
import os
import time
import uuid
from collections import deque
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from . import tasks
from .embeddings import DIMENSIONS, embed
from .text import count_tokens

CHAT_MODELS = {
    "gpt-fake-large": {"context": 16000, "input_price": 2.50, "cached_input_price": 0.25, "output_price": 10.00},
}
EMBEDDING_MODELS = {
    "text-embedding-fake": {"dimensions": DIMENSIONS, "input_price": 0.02},
}

# Prompt caching: igual ao de muitos providers reais, é match de prefixo.
CACHE_MIN_TOKENS = 1024
CACHE_BLOCK_TOKENS = 128
CACHE_TTL_SECONDS = 300

# Latência: o tempo até o primeiro token cresce com a entrada que não veio do cache.
BASE_LATENCY_S = 0.3
UNCACHED_INPUT_S_PER_TOKEN = 0.0004
OUTPUT_TOKENS_PER_S = 100

API_KEY = os.environ.get("FAKE_OPENAI_KEY", "")

calls: deque = deque(maxlen=5000)
prefixes: deque = deque(maxlen=1000)

app = FastAPI(title="provider-fake", docs_url=None, redoc_url=None)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    return ""


def serialize(messages: list[dict]) -> str:
    return "".join(f"<|{m.get('role', '')}|>\n{text_of(m.get('content'))}\n" for m in messages)


def common_prefix_len(a: str, b: str) -> int:
    low, high = 0, min(len(a), len(b))
    while low < high:
        mid = (low + high + 1) // 2
        if a[:mid] == b[:mid]:
            low = mid
        else:
            high = mid - 1
    return low


def cached_tokens_for(model: str, prompt: str, input_tokens: int) -> int:
    """Tokens do prefixo já vistos em uma requisição recente ao mesmo modelo, em blocos de 128."""
    now = time.monotonic()
    longest = 0
    for ts, seen_model, seen in prefixes:
        if seen_model == model and now - ts <= CACHE_TTL_SECONDS:
            longest = max(longest, common_prefix_len(prompt, seen))
    prefixes.append((now, model, prompt))
    lcp_tokens = longest // 4
    if lcp_tokens < CACHE_MIN_TOKENS:
        return 0
    return min((lcp_tokens // CACHE_BLOCK_TOKENS) * CACHE_BLOCK_TOKENS, input_tokens)


def record_call(model, task) -> dict:
    entry = {"id": uuid.uuid4().hex[:12], "ts": now_iso(), "model": model, "task": task, "status": None,
             "input_tokens": None, "cached_tokens": None, "output_tokens": None, "cost_usd": None,
             "duration_ms": None, "_start": time.monotonic()}
    calls.append(entry)
    return entry


def finish_call(entry: dict, status: int) -> None:
    entry["status"] = status
    entry["duration_ms"] = round((time.monotonic() - entry["_start"]) * 1000)


def error(status: int, message: str, kind: str, code: str | None = None):
    body = {"error": {"message": message, "type": kind, "param": None, "code": code}}
    return JSONResponse(body, status_code=status)


def authorized(request: Request) -> bool:
    return bool(API_KEY) and request.headers.get("authorization", "") == f"Bearer {API_KEY}"


async def read_json(request: Request) -> dict:
    try:
        body = await request.json()
        return body if isinstance(body, dict) else {}
    except Exception:
        return {}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/openai/v1/models")
async def models(request: Request):
    if not authorized(request):
        return error(401, "Chave de API inválida.", "invalid_request_error", "invalid_api_key")
    data = [{"id": m, "object": "model", "created": 0, "owned_by": "provider-fake"}
            for m in [*CHAT_MODELS, *EMBEDDING_MODELS]]
    return {"object": "list", "data": data}


@app.post("/openai/v1/chat/completions")
async def chat(request: Request):
    body = await read_json(request)
    model = body.get("model")
    messages = body.get("messages") or []
    user_text = next((text_of(m.get("content")) for m in reversed(messages) if m.get("role") == "user"), "")
    task, content = tasks.detect(user_text)
    entry = record_call(model, task)

    if not authorized(request):
        finish_call(entry, 401)
        return error(401, "Chave de API inválida.", "invalid_request_error", "invalid_api_key")
    if model not in CHAT_MODELS:
        finish_call(entry, 404)
        return error(404, f"O modelo '{model}' não existe.", "invalid_request_error", "model_not_found")
    if body.get("stream"):
        finish_call(entry, 400)
        return error(400, "Este provider simulado não implementa streaming.", "invalid_request_error")

    profile = CHAT_MODELS[model]
    prompt = serialize(messages)
    input_tokens = count_tokens(prompt)
    entry["input_tokens"] = input_tokens
    if input_tokens > profile["context"]:
        finish_call(entry, 400)
        return error(400, f"A entrada tem {input_tokens} tokens e o contexto máximo do modelo é "
                          f"{profile['context']} tokens.", "invalid_request_error", "context_length_exceeded")

    cached = cached_tokens_for(model, prompt, input_tokens)
    text = tasks.generate(task, content)
    output_tokens = count_tokens(text)
    uncached = input_tokens - cached
    await asyncio.sleep(BASE_LATENCY_S + uncached * UNCACHED_INPUT_S_PER_TOKEN + output_tokens / OUTPUT_TOKENS_PER_S)

    cost = (uncached * profile["input_price"] + cached * profile["cached_input_price"]
            + output_tokens * profile["output_price"]) / 1_000_000
    entry.update(cached_tokens=cached, output_tokens=output_tokens, cost_usd=round(cost, 8))
    finish_call(entry, 200)
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:24]}", "object": "chat.completion", "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text, "refusal": None},
                     "logprobs": None, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": input_tokens, "completion_tokens": output_tokens,
                  "total_tokens": input_tokens + output_tokens,
                  "prompt_tokens_details": {"cached_tokens": cached}},
    }


@app.post("/openai/v1/embeddings")
async def embeddings(request: Request):
    body = await read_json(request)
    model = body.get("model")
    entry = record_call(model, "embed")

    if not authorized(request):
        finish_call(entry, 401)
        return error(401, "Chave de API inválida.", "invalid_request_error", "invalid_api_key")
    if model not in EMBEDDING_MODELS:
        finish_call(entry, 404)
        return error(404, f"O modelo '{model}' não existe.", "invalid_request_error", "model_not_found")
    raw = body.get("input")
    inputs = [raw] if isinstance(raw, str) else raw
    if not isinstance(inputs, list) or not inputs or not all(isinstance(i, str) for i in inputs):
        finish_call(entry, 400)
        return error(400, "input deve ser uma string ou uma lista de strings.", "invalid_request_error")

    tokens = sum(count_tokens(i) for i in inputs)
    await asyncio.sleep(0.03 + tokens * 0.00002)
    cost = tokens * EMBEDDING_MODELS[model]["input_price"] / 1_000_000
    entry.update(input_tokens=tokens, cached_tokens=0, output_tokens=0, cost_usd=round(cost, 8))
    finish_call(entry, 200)
    return {
        "object": "list", "model": model,
        "data": [{"object": "embedding", "index": i, "embedding": embed(text)} for i, text in enumerate(inputs)],
        "usage": {"prompt_tokens": tokens, "total_tokens": tokens},
    }


@app.get("/admin/calls")
async def admin_calls(last: int = 50):
    last = max(1, min(last, calls.maxlen))
    recent = list(calls)[-last:]
    recent.reverse()
    return [{k: v for k, v in e.items() if not k.startswith("_")} for e in recent]


@app.get("/admin/usage")
async def admin_usage():
    totals: dict[str, dict] = {}
    for e in calls:
        if e["status"] != 200:
            continue
        t = totals.setdefault(e["model"], {"calls": 0, "input_tokens": 0, "cached_tokens": 0,
                                           "output_tokens": 0, "cost_usd": 0.0})
        t["calls"] += 1
        t["input_tokens"] += e["input_tokens"] or 0
        t["cached_tokens"] += e["cached_tokens"] or 0
        t["output_tokens"] += e["output_tokens"] or 0
        t["cost_usd"] += e["cost_usd"] or 0.0
    for t in totals.values():
        t["cost_usd"] = round(t["cost_usd"], 6)
    return {"models": totals, "cost_usd": round(sum(t["cost_usd"] for t in totals.values()), 6)}


@app.post("/admin/reset")
async def admin_reset():
    calls.clear()
    prefixes.clear()
    return {"status": "ok"}
