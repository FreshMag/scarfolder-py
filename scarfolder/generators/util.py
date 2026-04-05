"""General-purpose built-in generators."""
from __future__ import annotations

from typing import Any, Iterable

from scarfolder.core.base import Generator


class Combine(Generator):
    """Zip multiple streams into tuples.

    Args:
        streams: list of lists to zip together.

    Example::

        streams: [${steps.first_names}, ${steps.last_names}]
        # → [("Alice", "Smith"), ("Bob", "Jones"), ...]
    """

    def __init__(self, streams: list[list[Any]]) -> None:
        self.streams = streams

    def generate(self) -> Iterable[tuple[Any, ...]]:
        return list(zip(*self.streams))


class From(Generator):
    """Pass a previous step's output through unchanged.

    Useful when you want to apply a transformer or loader to an existing
    step output without generating new data.

    Args:
        stream: the step output to re-use (e.g. ``${steps.names}``).

    Example::

        generator:
          name: scarfolder.generators.util.From
          args:
            stream: ${steps.full_names}
        loader: scarfolder.loaders.file.WriteLines
    """

    def __init__(self, stream: list[Any]) -> None:
        self.stream = stream

    def generate(self) -> list[Any]:
        return self.stream


class Range(Generator):
    """Generate a sequence of integers, analogous to Python's ``range()``.

    Args:
        start: first value (default 0).
        stop:  upper bound (exclusive, default 10).
        step:  increment (default 1).
    """

    def __init__(self, stop: int = 10, start: int = 0, step: int = 1) -> None:
        self.start = start
        self.stop = stop
        self.step = step

    def generate(self) -> Iterable[int]:
        return list(range(self.start, self.stop, self.step))


class Constant(Generator):
    """Repeat a single *value* exactly *count* times.

    Args:
        value: the value to repeat.
        count: how many copies to produce (default 1).

    Example::

        generator:
          name: scarfolder.generators.util.Constant
          args:
            value: hello
            count: 5
        # → ["hello", "hello", "hello", "hello", "hello"]
    """

    def __init__(self, value: Any, count: int = 1) -> None:
        self.value = value
        self.count = count

    def generate(self) -> list[Any]:
        return [self.value] * self.count


class Enumerate(Generator):
    """Pair each item in a stream with its index.

    Args:
        stream: input list (e.g. ``${steps.names}``).
        start:  starting index (default 0).

    Produces a list of ``(index, value)`` tuples.
    """

    def __init__(self, stream: list[Any], start: int = 0) -> None:
        self.stream = stream
        self.start = start

    def generate(self) -> list[tuple[int, Any]]:
        return list(enumerate(self.stream, self.start))
