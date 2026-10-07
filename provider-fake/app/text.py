"""Normalização de texto compartilhada pelos embeddings e pela tarefa de resposta."""

import math
import re
import unicodedata

STOPWORDS = {
    "a", "o", "as", "os", "um", "uma", "uns", "umas", "de", "do", "da", "dos", "das", "em", "no", "na",
    "nos", "nas", "por", "pelo", "pela", "para", "pra", "com", "sem", "e", "ou", "que", "qual", "quais",
    "quanto", "quanta", "quantos", "quantas", "como", "quando", "onde", "eu", "meu", "minha", "meus",
    "minhas", "voce", "seu", "sua", "seus", "suas", "ele", "ela", "isso", "isto", "esse", "essa", "este",
    "esta", "ser", "sao", "tem", "tenho", "temos", "ter", "posso", "pode", "podem", "preciso", "sobre",
    "mais", "menos", "muito", "ja", "nao", "sim", "se", "ao", "aos", "ate", "entre", "tambem", "cada",
    "vez", "fazer", "faco", "existe", "ha", "foi", "estou", "esta", "estao", "nosso", "nossa", "empresa",
    "regra", "regras", "funciona", "atual", "hoje",
}

SYNONYMS = {
    "descanso": "ferias",
    "vr": "refeicao",
    "va": "alimentacao",
    "remoto": "home",
    "teletrabalho": "home",
    "gympass": "academia",
    "convenio": "plano",
}


def strip_accents(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c))


def words(text: str) -> list[str]:
    clean = re.sub(r"[^a-z0-9]+", " ", strip_accents(text.lower()))
    return clean.split()


def stems(text: str) -> list[str]:
    """Palavras relevantes do texto, reduzidas a um radical de até 5 caracteres."""
    result = []
    for word in words(text):
        word = SYNONYMS.get(word, word)
        if word in STOPWORDS:
            continue
        if word.isdigit():
            result.append(word)
            continue
        if len(word) < 3:
            continue
        result.append(word[:5])
    return result


def count_tokens(text: str) -> int:
    return math.ceil(len(text) / 4) if text else 0
