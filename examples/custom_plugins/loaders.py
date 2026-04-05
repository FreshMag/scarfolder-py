"""Custom loaders mounted into the container via /workspace."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from scarfolder.core.base import Loader


class WriteCsv(Loader):
    """Write a list of dicts (or tuples) to a CSV file.

    Args:
        path:    Destination file path.
        headers: Column headers. If omitted and values are dicts, dict keys
                 are used as headers on the first row.
    """

    def __init__(self, path: str, headers: list[str] | None = None) -> None:
        self.path = Path(path)
        self.headers = headers

    def load(self, values: list[Any]) -> None:
        if not values:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", newline="", encoding="utf-8") as fh:
            if isinstance(values[0], dict):
                fieldnames = self.headers or list(values[0].keys())
                writer = csv.DictWriter(fh, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(values)
            else:
                writer = csv.writer(fh)
                if self.headers:
                    writer.writerow(self.headers)
                writer.writerows(
                    [v] if not isinstance(v, (list, tuple)) else v
                    for v in values
                )
