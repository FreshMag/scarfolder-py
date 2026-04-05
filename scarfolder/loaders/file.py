"""File-system loaders."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from scarfolder.core.base import Loader


class WriteLines(Loader):
    """Write each value as a line to a text file.

    Args:
        path:     Destination file path (parent dirs are created automatically).
        mode:     Open mode - ``"w"`` (overwrite, default) or ``"a"`` (append).
        encoding: File encoding (default ``"utf-8"``).
    """

    def __init__(
        self,
        path: str,
        mode: str = "w",
        encoding: str = "utf-8",
    ) -> None:
        self.path = Path(path)
        self.mode = mode
        self.encoding = encoding

    def load(self, values: list[Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open(self.mode, encoding=self.encoding) as fh:
            for value in values:
                fh.write(str(value) + "\n")


class WriteJson(Loader):
    """Serialise *values* as a JSON array to a file.

    Args:
        path:    Destination file path.
        indent:  Pretty-print indent (default 2, ``null`` for compact).
        encoding: File encoding (default ``"utf-8"``).
    """

    def __init__(
        self,
        path: str,
        indent: int | None = 2,
        encoding: str = "utf-8",
    ) -> None:
        self.path = Path(path)
        self.indent = indent
        self.encoding = encoding

    def load(self, values: list[Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", encoding=self.encoding) as fh:
            json.dump(values, fh, indent=self.indent, default=str)


# ---------------------------------------------------------------------------
# Convenience function (usable without args)
# ---------------------------------------------------------------------------

def print_values(values: list[Any], **_: Any) -> None:
    """Print each value to stdout — handy for debugging pipelines."""
    for value in values:
        print(value)
