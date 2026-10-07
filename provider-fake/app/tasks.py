"""O "modelo" simulado: a tarefa de resposta com contexto, determinística."""

import json
import re

from .text import stems

NOT_FOUND = "Não encontrei essa informação nos documentos da sua empresa."

BLOCK_HEADER = re.compile(r"^\[source:\s*([^\]]+?)\s*\]\s*(.*)$")

# Instruções dirigidas ao assistente dentro do contexto. O modelo simulado não distingue
# instrução de dado: quando encontra uma delas num trecho do contexto, obedece.
EMBEDDED_INSTRUCTIONS = [
    re.compile(r"<!--\s*(?:(?:nota|aviso|instru[cç][aã]o)\s+)?(?:para\s+o\s+|ao\s+)?assistente\s*:\s*(.+?)\s*-->",
               re.IGNORECASE | re.DOTALL),
    re.compile(r"^\s*(?:nota|aviso|instru[cç][aã]o|instru[cç][oõ]es)\s+(?:para\s+o|ao)\s+assistente\s*:\s*(.+)$",
               re.IGNORECASE | re.MULTILINE),
    re.compile(r"ignore\s+(?:todas\s+)?as\s+instru[cç][oõ]es\s+anteriores\s*[,e]?\s*(.+)$",
               re.IGNORECASE | re.MULTILINE),
]


def detect(user_text: str) -> tuple[str | None, str]:
    first, _, rest = user_text.partition("\n")
    match = re.match(r"^\s*TASK:\s*(\w+)\s*$", first)
    if not match:
        return None, user_text
    return match.group(1).lower(), rest


def parse_answer_input(content: str) -> tuple[str, list[tuple[str, str]]]:
    """A pergunta é a linha QUESTION:; o contexto são os blocos [source: ...] depois da linha CONTEXT:."""
    question = ""
    blocks: list[tuple[str, list[str]]] = []
    in_context = False
    for line in content.splitlines():
        if not in_context:
            if line.startswith("QUESTION:") and not question:
                question = line[len("QUESTION:"):].strip()
            elif line.strip() == "CONTEXT:":
                in_context = True
            continue
        header = BLOCK_HEADER.match(line)
        if header:
            blocks.append((header.group(1), [header.group(2)] if header.group(2) else []))
        elif blocks:
            blocks[-1][1].append(line)
    return question, [(source, "\n".join(lines)) for source, lines in blocks]


def sentences(block: str) -> list[str]:
    result = []
    for line in block.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line.startswith("<!--"):
            continue
        line = re.sub(r"^[-*>]+\s*", "", line)
        line = line.replace("**", "")
        for piece in re.split(r"(?<=[.!?])\s+", line):
            piece = piece.strip()
            if piece:
                result.append(piece)
    return result


def answer(content: str) -> str:
    question, blocks = parse_answer_input(content)

    for source, block in blocks:
        for pattern in EMBEDDED_INSTRUCTIONS:
            found = pattern.search(block)
            if found:
                payload = " ".join(found.group(1).split())
                return json.dumps({"answer": payload, "sources": [source]}, ensure_ascii=False)

    wanted = set(stems(question))
    needed = 2 if len(wanted) >= 2 else 1
    best = None
    for b_index, (source, block) in enumerate(blocks):
        for s_index, sentence in enumerate(sentences(block)):
            score = len(wanted & set(stems(sentence)))
            key = (score, -b_index, -s_index)
            if score >= needed and (best is None or key > best[0]):
                best = (key, sentence, source)

    if best is None:
        return json.dumps({"answer": NOT_FOUND, "sources": []}, ensure_ascii=False)
    return json.dumps({"answer": best[1], "sources": [best[2]]}, ensure_ascii=False)


def generate(task: str | None, content: str) -> str:
    if task == "answer":
        return answer(content)
    return "Tarefa não reconhecida. Use a primeira linha 'TASK: answer'."
