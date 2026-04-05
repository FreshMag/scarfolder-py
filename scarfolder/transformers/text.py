"""Text-processing transformer functions.

All functions follow the signature ``fn(values: list, **kwargs) -> list``
so they work both as plain functions *and* when wrapped by the registry's
``_FuncTransformer`` adapter.
"""
from __future__ import annotations

from typing import Any


def capitalize_first(values: list[str], **_: Any) -> list[str]:
    """Capitalise the first letter of each string."""
    return [v.capitalize() for v in values]


def upper(values: list[str], **_: Any) -> list[str]:
    """Convert each string to upper-case."""
    return [v.upper() for v in values]


def lower(values: list[str], **_: Any) -> list[str]:
    """Convert each string to lower-case."""
    return [v.lower() for v in values]


def strip(values: list[str], chars: str | None = None, **_: Any) -> list[str]:
    """Strip leading/trailing whitespace (or *chars*) from each string."""
    return [v.strip(chars) for v in values]


def join(values: list[Any], separator: str = " ", **_: Any) -> list[str]:
    """Join each item (expected to be a sequence) into a single string.

    Example::

        # values = [("Alice", "Smith"), ("Bob", "Jones")]
        # separator = " "
        # → ["Alice Smith", "Bob Jones"]
    """
    return [separator.join(str(part) for part in item) for item in values]


def prefix(values: list[str], text: str = "", **_: Any) -> list[str]:
    """Prepend *text* to every string in *values*."""
    return [f"{text}{v}" for v in values]


def suffix(values: list[str], text: str = "", **_: Any) -> list[str]:
    """Append *text* to every string in *values*."""
    return [f"{v}{text}" for v in values]


def format_template(values: list[Any], template: str = "{value}", **_: Any) -> list[str]:
    """Apply a Python format-string *template* to each value.

    The value is exposed as ``{value}`` inside the template.

    Example::

        template: "Hello, {value}!"
        # values = ["Alice", "Bob"]
        # → ["Hello, Alice!", "Hello, Bob!"]
    """
    return [template.format(value=v) for v in values]
