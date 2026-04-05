"""Tests for env-var placeholder resolution and the new loaders."""
from __future__ import annotations

import os
from unittest.mock import patch

import pytest

from scarfolder.config.resolver import resolve
from scarfolder.exceptions import ResolutionError
from scarfolder.loaders.console import Print


# ---------------------------------------------------------------------------
# Env-var resolution
# ---------------------------------------------------------------------------

def test_env_namespace():
    ns = {"args": {}, "steps": {}, "env": {"DB_PASS": "secret"}}
    assert resolve("${env.DB_PASS}", ns) == "secret"


def test_env_namespace_in_url():
    ns = {"args": {}, "steps": {}, "env": {"DB_PASS": "s3cr3t"}}
    result = resolve("postgres://user:${env.DB_PASS}@localhost/db", ns)
    assert result == "postgres://user:s3cr3t@localhost/db"


def test_bare_key_falls_back_to_os_environ():
    ns = {"args": {}, "steps": {}, "env": os.environ}
    with patch.dict(os.environ, {"MY_TOKEN": "abc123"}):
        assert resolve("${MY_TOKEN}", ns) == "abc123"


def test_bare_key_args_takes_priority_over_env():
    """args.KEY must win over an identically-named env var."""
    ns = {"args": {"LANG": "from_args"}, "steps": {}, "env": {"LANG": "from_env"}}
    with patch.dict(os.environ, {"LANG": "from_env"}):
        assert resolve("${LANG}", ns) == "from_args"


def test_bare_key_not_found_raises():
    ns = {"args": {}, "steps": {}, "env": {}}
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ResolutionError, match="not found in args or environment"):
            resolve("${TOTALLY_MISSING_XYZ}", ns)


def test_env_key_missing_raises():
    ns = {"args": {}, "steps": {}, "env": {}}
    with pytest.raises(ResolutionError):
        resolve("${env.TOTALLY_MISSING_XYZ}", ns)


# ---------------------------------------------------------------------------
# Console loader
# ---------------------------------------------------------------------------

def test_print_loader_basic(capsys):
    Print().load(["Alice", "Bob"])
    out = capsys.readouterr().out
    assert "Alice" in out
    assert "Bob" in out


def test_print_loader_template(capsys):
    Print(template="{index}: {value}", header="-- start --", footer="-- end --").load(["x", "y"])
    out = capsys.readouterr().out
    assert "0: x" in out
    assert "1: y" in out
    assert "-- start --" in out
    assert "-- end --" in out


def test_print_loader_empty(capsys):
    Print().load([])
    out = capsys.readouterr().out
    # Empty list → empty output (no crash)
    assert out.strip() == ""


# ---------------------------------------------------------------------------
# SQL loader — import error when SQLAlchemy is absent
# ---------------------------------------------------------------------------

def test_sql_loader_missing_sqlalchemy():
    """_engine() should raise PluginError if SQLAlchemy is not installed."""
    import sys

    real = sys.modules.get("sqlalchemy")
    sys.modules["sqlalchemy"] = None  # type: ignore[assignment]
    try:
        if "scarfolder.loaders.sql" in sys.modules:
            del sys.modules["scarfolder.loaders.sql"]

        from scarfolder.loaders.sql import _engine
        from scarfolder.exceptions import PluginError

        with pytest.raises(PluginError, match="SQLAlchemy"):
            _engine("sqlite:///:memory:")
    finally:
        if real is None:
            del sys.modules["sqlalchemy"]
        else:
            sys.modules["sqlalchemy"] = real
        if "scarfolder.loaders.sql" in sys.modules:
            del sys.modules["scarfolder.loaders.sql"]
