from . import config, db


def search(tenant_id: str, embedding: list[float], k: int = config.RETRIEVAL_TOP_K) -> list[dict]:
    """Os k trechos da base da empresa mais próximos da pergunta."""
    vector = db.vector_literal(embedding)
    with db.connect() as conn:
        rows = conn.execute(
            "SELECT doc_id, title, content, 1 - (embedding <=> %s::vector) AS similarity FROM chunks "
            "WHERE tenant_id = %s ORDER BY embedding <=> %s::vector LIMIT %s",
            (vector, tenant_id, vector, k),
        ).fetchall()
    return [{"doc_id": r[0], "title": r[1], "content": r[2], "similarity": float(r[3])} for r in rows]
