"""Cache de respostas: exato (chave pela pergunta) e semântico (pgvector)."""

import hashlib
import re

from psycopg.types.json import Jsonb

from . import config, db


def normalize(question: str) -> str:
    return re.sub(r"\s+", " ", question).strip().lower()


def exact_key(question: str) -> str:
    return hashlib.sha256(normalize(question).encode()).hexdigest()


def get_exact(question: str) -> dict | None:
    with db.connect() as conn:
        row = conn.execute("SELECT response FROM answer_cache WHERE cache_key = %s",
                           (exact_key(question),)).fetchone()
    return row[0] if row else None


def put_exact(question: str, response: dict) -> None:
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO answer_cache (cache_key, question, response) VALUES (%s, %s, %s) "
            "ON CONFLICT (cache_key) DO UPDATE SET response = EXCLUDED.response, created_at = NOW()",
            (exact_key(question), question, Jsonb(response)),
        )


def get_semantic(embedding: list[float]) -> tuple[dict, float] | None:
    with db.connect() as conn:
        row = conn.execute(
            "SELECT response, 1 - (embedding <=> %s::vector) AS similarity FROM semantic_cache "
            "ORDER BY embedding <=> %s::vector LIMIT 1",
            (db.vector_literal(embedding), db.vector_literal(embedding)),
        ).fetchone()
    if row and row[1] >= config.SEMANTIC_CACHE_THRESHOLD:
        return row[0], float(row[1])
    return None


def put_semantic(question: str, embedding: list[float], response: dict) -> None:
    with db.connect() as conn:
        conn.execute("INSERT INTO semantic_cache (question, embedding, response) VALUES (%s, %s::vector, %s)",
                     (question, db.vector_literal(embedding), Jsonb(response)))
