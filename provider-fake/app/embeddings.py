"""Embeddings determinísticos: saco de radicais projetado em um vetor de dimensão fixa."""

import hashlib
import math

from .text import stems

DIMENSIONS = 256


def _slot(stem: str) -> tuple[int, float]:
    digest = hashlib.sha256(stem.encode()).digest()
    index = int.from_bytes(digest[:4], "big") % DIMENSIONS
    sign = 1.0 if digest[4] % 2 == 0 else -1.0
    return index, sign


def embed(text: str) -> list[float]:
    vector = [0.0] * DIMENSIONS
    for stem in set(stems(text)):
        index, sign = _slot(stem)
        vector[index] += sign
    norm = math.sqrt(sum(v * v for v in vector))
    if norm == 0:
        # Texto sem nenhuma palavra relevante: vetor fixo, para a similaridade continuar definida.
        vector[0] = 1.0
        return vector
    return [round(v / norm, 6) for v in vector]
