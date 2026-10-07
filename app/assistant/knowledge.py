"""Base de conhecimento de cada empresa: documentos publicados pelo RH, chunking e indexação."""

import hashlib
import logging
from pathlib import Path

from . import config, db, llm

log = logging.getLogger("assistant.knowledge")


def content_hash(title: str, content: str) -> str:
    return hashlib.sha256(f"{title}\n{content}".encode()).hexdigest()


def parse_markdown(text: str, fallback_title: str) -> tuple[str, str]:
    """Separa o front matter (só o campo title é lido) do corpo do documento."""
    title = fallback_title
    body = text
    if text.startswith("---\n"):
        header, _, body = text[4:].partition("\n---\n")
        for line in header.splitlines():
            key, _, value = line.partition(":")
            if key.strip() == "title" and value.strip():
                title = value.strip()
    return title, body.strip()


def chunk(title: str, content: str) -> list[str]:
    sections: list[tuple[str, list[str]]] = [("", [])]
    for line in content.splitlines():
        if line.startswith("## "):
            sections.append((line[3:].strip(), []))
        elif not line.startswith("# "):
            sections[-1][1].append(line)

    chunks = []
    for section, lines in sections:
        body = "\n".join(lines).strip()
        if not body:
            continue
        header = f"# {title} | {section}" if section else f"# {title}"
        current = ""
        for paragraph in body.split("\n\n"):
            if current and len(current) + len(paragraph) > config.CHUNK_MAX_CHARS:
                chunks.append(f"{header}\n{current.strip()}")
                current = ""
            current += paragraph + "\n\n"
        if current.strip():
            chunks.append(f"{header}\n{current.strip()}")
    return chunks


def upsert_document(tenant_id: str, doc_id: str, title: str, content: str) -> None:
    with db.connect() as conn:
        conn.execute(
            "INSERT INTO documents (tenant_id, doc_id, title, content, content_hash) VALUES (%s, %s, %s, %s, %s) "
            "ON CONFLICT (tenant_id, doc_id) DO UPDATE SET title = EXCLUDED.title, content = EXCLUDED.content, "
            "content_hash = EXCLUDED.content_hash, updated_at = NOW()",
            (tenant_id, doc_id, title, content, content_hash(title, content)),
        )


def delete_document(tenant_id: str, doc_id: str) -> bool:
    with db.connect() as conn:
        deleted = conn.execute("DELETE FROM documents WHERE tenant_id = %s AND doc_id = %s",
                               (tenant_id, doc_id)).rowcount
    return deleted > 0


def list_documents(tenant_id: str) -> list[dict]:
    with db.connect() as conn:
        rows = conn.execute("SELECT doc_id, title, updated_at FROM documents WHERE tenant_id = %s ORDER BY doc_id",
                            (tenant_id,)).fetchall()
    return [{"doc_id": r[0], "title": r[1], "updated_at": r[2].isoformat()} for r in rows]


def reindex(tenant_id: str) -> dict:
    """Indexa os documentos novos ou alterados da empresa. Documentos sem mudança são pulados."""
    with db.connect() as conn:
        documents = conn.execute("SELECT doc_id, title, content, content_hash FROM documents WHERE tenant_id = %s",
                                 (tenant_id,)).fetchall()
        indexed = {r[0]: r[1] for r in conn.execute(
            "SELECT DISTINCT doc_id, doc_hash FROM chunks WHERE tenant_id = %s", (tenant_id,)).fetchall()}

    summary = {"indexed": [], "unchanged": []}
    for doc_id, title, content, doc_hash in documents:
        if indexed.get(doc_id) == doc_hash:
            summary["unchanged"].append(doc_id)
            continue
        pieces = chunk(title, content)
        vectors = llm.embed(pieces) if pieces else []
        with db.connect() as conn:
            conn.execute("DELETE FROM chunks WHERE tenant_id = %s AND doc_id = %s", (tenant_id, doc_id))
            for ordinal, (text, vector) in enumerate(zip(pieces, vectors)):
                conn.execute(
                    "INSERT INTO chunks (tenant_id, doc_id, doc_hash, ordinal, title, content, embedding) "
                    "VALUES (%s, %s, %s, %s, %s, %s, %s::vector)",
                    (tenant_id, doc_id, doc_hash, ordinal, title, text, db.vector_literal(vector)),
                )
        summary["indexed"].append(doc_id)
    log.info("reindex tenant=%s indexed=%s unchanged=%s", tenant_id, summary["indexed"], summary["unchanged"])
    return summary


def seed() -> None:
    """Carrega a base inicial de cada empresa quando o banco está vazio."""
    with db.connect() as conn:
        if conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0] > 0:
            return
    base = Path(config.KNOWLEDGE_BASE_DIR)
    for tenant_dir in sorted(p for p in base.iterdir() if p.is_dir()):
        for path in sorted(tenant_dir.glob("*.md")):
            title, body = parse_markdown(path.read_text(encoding="utf-8"), path.stem)
            upsert_document(tenant_dir.name, path.stem, title, body)
        reindex(tenant_dir.name)
