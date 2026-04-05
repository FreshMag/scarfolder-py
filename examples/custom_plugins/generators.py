"""Custom generators mounted into the container via /workspace."""
from __future__ import annotations

import random
from typing import Iterable

from scarfolder.core.base import Generator

FIRST_NAMES = {
    "it": ["Luca", "Sofia", "Marco", "Giulia", "Andrea", "Chiara"],
    "en": ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank"],
}

LAST_NAMES = {
    "it": ["Rossi", "Ferrari", "Bianchi", "Esposito", "Romano"],
    "en": ["Smith", "Jones", "Williams", "Taylor", "Brown"],
}


class Name(Generator):
    def __init__(self, language: str = "en", count: int = 5, distinct: bool = False) -> None:
        self.pool = FIRST_NAMES.get(language, FIRST_NAMES["en"])
        self.count = count
        self.distinct = distinct

    def generate(self) -> Iterable[str]:
        if self.distinct:
            return random.sample(self.pool, min(self.count, len(self.pool)))
        return [random.choice(self.pool) for _ in range(self.count)]


class Surname(Generator):
    def __init__(self, language: str = "en", count: int = 5, distinct: bool = False) -> None:
        self.pool = LAST_NAMES.get(language, LAST_NAMES["en"])
        self.count = count
        self.distinct = distinct

    def generate(self) -> Iterable[str]:
        if self.distinct:
            return random.sample(self.pool, min(self.count, len(self.pool)))
        return [random.choice(self.pool) for _ in range(self.count)]
