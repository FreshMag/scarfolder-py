"""File-system loaders."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scarfolder.core.base import Loader


class WriteLines(Loader):
    """Write each value as a line to a text file.

    Args:
        values:   The sequence to write — typically ``${steps.<id>}``.
        path:     Destination file path (parent dirs are created automatically).
        mode:     Open mode — ``"w"`` (overwrite, default) or ``"a"`` (append).
        encoding: File encoding (default ``"utf-8"``).

    Example::

        loader:
          name: scarfolder.loaders.file.WriteLines
          args:
            values: ${steps.greetings}
            path: output.txt
    """

    def __init__(
        self,
        values: list[Any],
        path: str,
        mode: str = "w",
        encoding: str = "utf-8",
    ) -> None:
        self.values = values
        self.path = Path(path)
        self.mode = mode
        self.encoding = encoding

    def load(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open(self.mode, encoding=self.encoding) as fh:
            for value in self.values:
                fh.write(str(value) + "\n")


class WriteJson(Loader):
    """Serialise *values* as a JSON array to a file.

    Args:
        values:   The sequence to serialise — typically ``${steps.<id>}``.
        path:     Destination file path.
        indent:   Pretty-print indent (default 2, ``null`` for compact).
        encoding: File encoding (default ``"utf-8"``).
    """

    def __init__(
        self,
        values: list[Any],
        path: str,
        indent: int | None = 2,
        encoding: str = "utf-8",
    ) -> None:
        self.values = values
        self.path = Path(path)
        self.indent = indent
        self.encoding = encoding

    def load(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding=self.encoding) as fh:
            json.dump(self.values, fh, indent=self.indent, default=str)


# ---------------------------------------------------------------------------
# Convenience function (usable without subclassing)
# ---------------------------------------------------------------------------

def print_values(values: list[Any], **_: Any) -> None:
    """Print each value to stdout — handy for debugging pipelines.

    Args:
        values: The sequence to print — typically ``${steps.<id>}``.
    """
    for value in values:
        print(value)
