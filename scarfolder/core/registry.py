"""Dynamic plugin loader.

Imports classes or callables by dotted path and wraps bare functions into
the appropriate base-class adapter, so both patterns work in YAML configs:

    generator: my_package.generators.MyGenerator   # class-based
    generator: my_package.generators.make_names    # function-based

Function convention
-------------------
All data — including references to other steps' outputs — arrives via the
resolved ``args`` dict and is passed as keyword arguments.  Plain-function
plugins therefore follow these signatures:

    generator: fn(**kwargs) -> Iterable
    transformer: fn(**kwargs) -> Iterable
    loader: fn(**kwargs) -> None

For transformers and loaders the primary data input is simply another named
keyword argument (e.g. ``values``) whose value is resolved from
``${steps.<id>}`` in the YAML args block.
"""
from __future__ import annotations

import importlib
from typing import Any

from scarfolder.core.base import Generator, Transformer, Loader
from scarfolder.exceptions import PluginError


# ---------------------------------------------------------------------------
# Import helper
# ---------------------------------------------------------------------------

def _import_symbol(dotted_path: str) -> Any:
    """Import an attribute from a dotted module path.

    ``"pkg.sub.ClassName"`` → imports ``pkg.sub`` and returns ``ClassName``.
    """
    if "." not in dotted_path:
        raise PluginError(
            f"Invalid plugin path '{dotted_path}': must be a dotted path "
            "like 'my_package.module.ClassName'."
        )
    module_path, _, attr = dotted_path.rpartition(".")
    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise PluginError(
            f"Cannot import module '{module_path}' (from path '{dotted_path}'): {exc}"
        ) from exc
    try:
        return getattr(module, attr)
    except AttributeError:
        raise PluginError(
            f"Module '{module_path}' has no attribute '{attr}'."
        )


# ---------------------------------------------------------------------------
# Function adapters (wrap callables into the required ABC)
# ---------------------------------------------------------------------------

class _FuncGenerator(Generator):
    """Wraps a plain function ``fn(**kwargs) -> Iterable``."""

    def __init__(self, fn: Any, kwargs: dict[str, Any]) -> None:
        self._fn = fn
        self._kwargs = kwargs

    def generate(self) -> Any:
        return self._fn(**self._kwargs)


class _FuncTransformer(Transformer):
    """Wraps a plain function ``fn(**kwargs) -> Iterable``.

    The primary data input (e.g. ``values``) arrives as a keyword argument
    resolved from ``${steps.<id>}`` in the YAML args block.
    """

    def __init__(self, fn: Any, kwargs: dict[str, Any]) -> None:
        self._fn = fn
        self._kwargs = kwargs

    def transform(self) -> Any:
        return self._fn(**self._kwargs)


class _FuncLoader(Loader):
    """Wraps a plain function ``fn(**kwargs) -> None``.

    The primary data input arrives as a keyword argument (e.g. ``values``).
    """

    def __init__(self, fn: Any, kwargs: dict[str, Any]) -> None:
        self._fn = fn
        self._kwargs = kwargs

    def load(self) -> None:
        self._fn(**self._kwargs)


# ---------------------------------------------------------------------------
# Public factory functions
# ---------------------------------------------------------------------------

def make_generator(path: str, args: dict[str, Any]) -> Generator:
    obj = _import_symbol(path)
    if isinstance(obj, type) and issubclass(obj, Generator):
        try:
            return obj(**args)
        except TypeError as exc:
            raise PluginError(
                f"Failed to instantiate generator '{path}' with args {args}: {exc}"
            ) from exc
    if callable(obj):
        return _FuncGenerator(obj, args)
    raise PluginError(f"'{path}' is neither a Generator subclass nor a callable.")


def make_transformer(path: str, args: dict[str, Any]) -> Transformer:
    obj = _import_symbol(path)
    if isinstance(obj, type) and issubclass(obj, Transformer):
        try:
            return obj(**args)
        except TypeError as exc:
            raise PluginError(
                f"Failed to instantiate transformer '{path}' with args {args}: {exc}"
            ) from exc
    if callable(obj):
        return _FuncTransformer(obj, args)
    raise PluginError(f"'{path}' is neither a Transformer subclass nor a callable.")


def make_loader(path: str, args: dict[str, Any]) -> Loader:
    obj = _import_symbol(path)
    if isinstance(obj, type) and issubclass(obj, Loader):
        try:
            return obj(**args)
        except TypeError as exc:
            raise PluginError(
                f"Failed to instantiate loader '{path}' with args {args}: {exc}"
            ) from exc
    if callable(obj):
        return _FuncLoader(obj, args)
    raise PluginError(f"'{path}' is neither a Loader subclass nor a callable.")
