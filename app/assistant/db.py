import time

import psycopg

from . import config

SCHEMA = f"""
CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS documents (
    tenant_id    TEXT NOT NULL,
    doc_id       TEXT NOT NULL,
    title        TEXT NOT NULL,
    content      TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (tenant_id, doc_id)
);

CREATE TABLE IF NOT EXISTS chunks (
    id        BIGSERIAL PRIMARY KEY,
    tenant_id TEXT NOT NULL,
    doc_id    TEXT NOT NULL,
    doc_hash  TEXT NOT NULL,
    ordinal   INT NOT NULL,
    title     TEXT NOT NULL,
    content   TEXT NOT NULL,
    embedding VECTOR({config.EMBEDDING_DIMENSIONS}) NOT NULL
);

CREATE TABLE IF NOT EXISTS answer_cache (
    cache_key  TEXT PRIMARY KEY,
    question   TEXT NOT NULL,
    response   JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS semantic_cache (
    id         BIGSERIAL PRIMARY KEY,
    question   TEXT NOT NULL,
    embedding  VECTOR({config.EMBEDDING_DIMENSIONS}) NOT NULL,
    response   JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
"""


def connect() -> psycopg.Connection:
    return psycopg.connect(config.DATABASE_URL, autocommit=True)


def init(retries: int = 30) -> None:
    for attempt in range(retries):
        try:
            with connect() as conn:
                conn.execute(SCHEMA)
            return
        except psycopg.OperationalError:
            if attempt == retries - 1:
                raise
            time.sleep(1)


def vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{v:.6f}" for v in values) + "]"
