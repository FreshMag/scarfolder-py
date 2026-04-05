"""Placeholder resolution engine.

Placeholder syntax: ``${namespace.key.subkey}``

Supported namespaces
--------------------
* ``args``        – runtime arguments (CLI + config defaults).
* ``steps``       – outputs of completed pipeline steps.
* ``env``         – OS environment variables: ``${env.DB_PASSWORD}``.
* ``<ref_name>``  – any key loaded from the ``refs`` section of the scarf.
* *(bare)*        – ``${KEY}`` with no dot checks ``args`` first, then ``os.environ``.

Type preservation
-----------------
When an *entire* string value is a single placeholder (e.g. ``"${steps.names}"``),
the **actual Python object** is returned (e.g. a ``list``), not its string
representation.  When a placeholder appears *within* a larger string
(``"Hello, ${args.name}!"``), all placeholders are stringified.
"""
from __future__ import annotations

import re
from typing import Any

from scarfolder.exceptions import ResolutionError

_PLACEHOLDER_RE = re.compile(r"\$\{([^}]+)\}")


# ---------------------------------------------------------------------------
# Placeholder discovery
# ---------------------------------------------------------------------------

def find_placeholders(value: Any) -> set[str]:
    """Recursively collect all placeholder *keys* inside *value*."""
    keys: set[str] = set()
    if value is None:
        return keys
    if isinstance(value, str):
        keys.update(m.group(1) for m in _PLACEHOLDER_RE.finditer(value))
    elif isinstance(value, dict):
        for v in value.values():
            keys |= find_placeholders(v)
    elif isinstance(value, (list, tuple)):
        for v in value:
            keys |= find_placeholders(v)
    return keys


def extract_step_deps(value: Any) -> set[str]:
    """Return the set of step IDs that *value* depends on.

    Scans for ``${steps.<id>}`` placeholders.
    """
    return {
        key[len("steps."):]
        for key in find_placeholders(value)
        if key.startswith("steps.")
    }


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

def resolve(value: Any, namespace: dict[str, Any]) -> Any:
    """Recursively resolve all ``${...}`` placeholders in *value*.

    *namespace* is the dict returned by
    :meth:`~scarfolder.core.context.ExecutionContext.to_namespace_dict`.
    """
    if value is None:
        return None
    if isinstance(value, str):
        # Optimisation: full-string match → return the object as-is (type-safe)
        full = _PLACEHOLDER_RE.fullmatch(value)
        if full:
            return _lookup(full.group(1), namespace)
        # Mixed string → stringify every placeholder
        return _PLACEHOLDER_RE.sub(
            lambda m: str(_lookup(m.group(1), namespace)), value
        )
    if isinstance(value, dict):
        return {k: resolve(v, namespace) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        resolved = [resolve(v, namespace) for v in value]
        return type(value)(resolved)
    # Scalars (int, float, bool, …) pass through unchanged
    return value


def _lookup(key: str, namespace: dict[str, Any]) -> Any:
    """Navigate a dotted *key* through *namespace*.

    ``"args.language"``  →  ``namespace["args"]["language"]``
    ``"env.DB_PASS"``    →  ``os.environ["DB_PASS"]``
    ``"MY_VAR"``         →  checks ``args`` first, then ``os.environ``
    """
    import os

    # Bare key (no dot): check args first, then fall back to env vars.
    if "." not in key:
        args = namespace.get("args", {})
        if key in args:
            return args[key]
        if key in os.environ:
            return os.environ[key]
        raise ResolutionError(
            f"'{key}' not found in args or environment variables."
        )

    parts = key.split(".")
    root, rest = parts[0], parts[1:]

    if root not in namespace:
        available = sorted(namespace)
        raise ResolutionError(
            f"Unknown namespace '{root}' in placeholder '${{{key}}}'. "
            f"Available namespaces: {available}"
        )

    current: Any = namespace[root]
    for part in rest:
        if isinstance(current, dict):
            if part not in current:
                raise ResolutionError(
                    f"Key '{part}' not found while resolving '${{{key}}}' "
                    f"(available: {sorted(current)})"
                )
            current = current[part]
        else:
            raise ResolutionError(
                f"Cannot navigate into '{part}' while resolving '${{{key}}}': "
                f"expected a dict but got {type(current).__name__}."
            )
    return current
