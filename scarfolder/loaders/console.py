"""Console / stdout loaders."""
from __future__ import annotations

from typing import Any

from scarfolder.core.base import Loader


class Print(Loader):
    """Print each value to stdout.

    Args:
        template: Optional Python format string. The value is exposed as
                  ``{value}`` and its index as ``{index}``.
                  Default: ``"{value}"``
        separator: String printed between items. Default: ``"\\n"``.
        header:   Optional line printed once before all values.
        footer:   Optional line printed once after all values.

    Example::

        loader:
          name: scarfolder.loaders.console.Print
          args:
            header: "--- Results ---"
            template: "  {index}. {value}"
    """

    def __init__(
        self,
        template: str = "{value}",
        separator: str = "\n",
        header: str | None = None,
        footer: str | None = None,
    ) -> None:
        self.template = template
        self.separator = separator
        self.header = header
        self.footer = footer

    def load(self, values: list[Any]) -> None:
        if self.header is not None:
            print(self.header)
        lines = [
            self.template.format(value=v, index=i)
            for i, v in enumerate(values)
        ]
        print(self.separator.join(lines))
        if self.footer is not None:
            print(self.footer)
