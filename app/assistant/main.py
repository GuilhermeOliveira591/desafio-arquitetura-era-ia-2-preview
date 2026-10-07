import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException

from . import cache, db, hr, knowledge, llm, retrieval, telemetry
from .prompt import build_messages
from .schemas import AskRequest, AskResponse, DocumentRequest

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")


@asynccontextmanager
async def lifespan(_: FastAPI):
    telemetry.setup()
    db.init()
    knowledge.seed()
    yield


app = FastAPI(title="Vereda RH - assistente", lifespan=lifespan)


def require_tenant(tenant_id: str | None) -> str:
    if not tenant_id:
        raise HTTPException(status_code=401, detail="tenant não identificado")
    return tenant_id


def require_hr(role: str | None) -> None:
    if role != "hr":
        raise HTTPException(status_code=403, detail="apenas o RH da empresa pode gerenciar documentos")


def parse_model_output(text: str) -> tuple[str, list[str]]:
    try:
        data = json.loads(text)
        return str(data["answer"]), [str(s) for s in data.get("sources", [])]
    except (ValueError, KeyError, TypeError):
        return text, []


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask(body: AskRequest,
        x_tenant_id: str | None = Header(default=None),
        x_employee_id: str | None = Header(default=None)):
    tenant_id = require_tenant(x_tenant_id)
    question = body.question

    with telemetry.tracer.start_as_current_span("ask") as span:
        span.set_attribute("app.tenant_id", tenant_id)
        span.set_attribute("app.employee_id", x_employee_id or "")
        span.set_attribute("app.question", question)

        cached = cache.get_exact(question)
        if cached is not None:
            span.set_attribute("app.origin", "exact_cache")
            return {**cached, "origin": "exact_cache"}

        embedding = llm.embed([question])[0]
        semantic = cache.get_semantic(embedding)
        if semantic is not None:
            response, similarity = semantic
            span.set_attribute("app.origin", "semantic_cache")
            span.set_attribute("app.semantic_similarity", similarity)
            return {**response, "origin": "semantic_cache"}

        employee = None
        if x_employee_id and hr.is_personal(question):
            employee = hr.get_employee(tenant_id, x_employee_id)
        chunks = retrieval.search(tenant_id, embedding)
        messages = build_messages(tenant_id, question, chunks, employee)
        text, usage = llm.chat(messages)
        answer, cited = parse_model_output(text)

        titles = {c["doc_id"]: c["title"] for c in chunks}
        sources = [{"document_id": doc_id, "title": titles[doc_id]} for doc_id in dict.fromkeys(cited)
                   if doc_id in titles]
        response = {"answer": answer, "sources": sources}

        cache.put_exact(question, response)
        cache.put_semantic(question, embedding, response)

        span.set_attribute("app.origin", "model")
        span.set_attribute("app.prompt", messages[1]["content"])
        span.set_attribute("app.answer", answer)
        span.set_attribute("app.total_tokens", usage.get("total_tokens", 0))
        return {**response, "origin": "model"}


@app.get("/admin/documents")
def list_documents(x_tenant_id: str | None = Header(default=None), x_role: str | None = Header(default=None)):
    tenant_id = require_tenant(x_tenant_id)
    require_hr(x_role)
    return knowledge.list_documents(tenant_id)


@app.post("/admin/documents")
def publish_document(body: DocumentRequest,
                     x_tenant_id: str | None = Header(default=None),
                     x_role: str | None = Header(default=None)):
    tenant_id = require_tenant(x_tenant_id)
    require_hr(x_role)
    knowledge.upsert_document(tenant_id, body.doc_id, body.title, body.content)
    return {"doc_id": body.doc_id, "reindex": knowledge.reindex(tenant_id)}


@app.delete("/admin/documents/{doc_id}")
def revoke_document(doc_id: str,
                    x_tenant_id: str | None = Header(default=None),
                    x_role: str | None = Header(default=None)):
    tenant_id = require_tenant(x_tenant_id)
    require_hr(x_role)
    if not knowledge.delete_document(tenant_id, doc_id):
        raise HTTPException(status_code=404, detail="documento não encontrado")
    return {"doc_id": doc_id, "reindex": knowledge.reindex(tenant_id)}
