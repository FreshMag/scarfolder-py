"""Abstract base classes that all plugins must implement.

Plugin authors can subclass these **or** supply plain callables — the
registry wraps bare functions automatically (see ``core.registry``).
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Iterable


class Generator(ABC):
    """Produces a sequence of values.

    Subclass and implement :meth:`generate`.  The pipeline calls
    ``list(instance.generate())`` so you may return any ``Iterable``,
    including a lazy Python generator.

    Constructor arguments come from the resolved ``args`` block in the
    YAML step config::

        class MyGenerator(Generator):
            def __init__(self, count: int = 10, lang: str = "en"):
                self.count = count
                self.lang = lang

            def generate(self) -> list[str]:
                ...
    """

    @abstractmethod
    def generate(self) -> Iterable[Any]: ...


class Transformer(ABC):
    """Transforms one sequence into another.

    Receives the full output list produced by the step's generator (or the
    previous transformer in a future chained design) and returns a new list.

    Constructor arguments come from the resolved ``args`` block::

        class MyTransformer(Transformer):
            def __init__(self, separator: str = " "):
                self.separator = separator

            def transform(self, values: list[Any]) -> list[str]:
                return [self.separator.join(v) for v in values]
    """

    @abstractmethod
    def transform(self, values: list[Any]) -> Iterable[Any]: ...


class Loader(ABC):
    """Consumes a sequence — a terminal side-effect operation.

    Constructor arguments come from the resolved ``args`` block::

        class WriteLines(Loader):
            def __init__(self, path: str):
                self.path = path

            def load(self, values: list[Any]) -> None:
                Path(self.path).write_text("\\n".join(map(str, values)))
    """

    @abstractmethod
    def load(self, values: list[Any]) -> None: ...
