"""Abstract base classes that all plugins must implement.

Plugin authors can subclass these **or** supply plain callables — the
registry wraps bare functions automatically (see ``core.registry``).

All configuration — including references to other steps' outputs — is
passed through resolved ``args`` and received by the constructor.  The
action methods (``generate``, ``transform``, ``load``) take no positional
arguments; they operate entirely on state set up in ``__init__``.
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
    YAML step config.  Any argument may reference a previous step's
    output via ``${steps.<id>}``::

        class NameGenerator(Generator):
            def __init__(self, values: list[str], count: int = 10):
                self.values = values   # e.g. from ${steps.name_pool}
                self.count = count

            def generate(self) -> list[str]:
                import random
                return random.choices(self.values, k=self.count)
    """

    @abstractmethod
    def generate(self) -> Iterable[Any]: ...


class Transformer(ABC):
    """Transforms one or more sequences into another sequence.

    Constructor arguments come from the resolved ``args`` block.  At
    least one argument should reference a previous step's output so
    the transformer has data to work with::

        class JoinTransformer(Transformer):
            def __init__(self, values: list[Any], separator: str = " "):
                self.values = values   # from ${steps.zipped_names}
                self.separator = separator

            def transform(self) -> list[str]:
                return [self.separator.join(map(str, row)) for row in self.values]
    """

    @abstractmethod
    def transform(self) -> Iterable[Any]: ...


class Loader(ABC):
    """Consumes a sequence — a terminal side-effect operation.

    Constructor arguments come from the resolved ``args`` block.  The
    input data should be declared as a named argument referencing a
    previous step's output::

        class WriteLines(Loader):
            def __init__(self, path: str, values: list[Any]):
                self.path = Path(path)
                self.values = values   # from ${steps.results}

            def load(self) -> None:
                Path(self.path).write_text("\\n".join(map(str, self.values)))
    """

    @abstractmethod
    def load(self) -> None: ...
