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


def test_env_namespace_via_os_environ():
    """${env.VAR} must work when env is os.environ (a Mapping, not a dict)."""
    with patch.dict(os.environ, {"DB_HOST": "localhost"}):
        ns = {"args": {}, "steps": {}, "env": os.environ}
        assert resolve("${env.DB_HOST}", ns) == "localhost"


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
    assert out == ""


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


# ---------------------------------------------------------------------------
# ExecuteMany._to_dict — unit tests (no DB required)
# ---------------------------------------------------------------------------

from scarfolder.loaders.sql import ExecuteMany


def _em(mapping):
    return ExecuteMany(url="sqlite:///:memory:", query="SELECT 1", mapping=mapping)


def test_to_dict_from_tuple():
    assert _em(["a", "b"])._to_dict(("x", "y")) == {"a": "x", "b": "y"}


def test_to_dict_from_list():
    assert _em(["a", "b"])._to_dict(["x", "y"]) == {"a": "x", "b": "y"}


def test_to_dict_from_dict_passthrough():
    d = {"a": 1, "b": 2}
    assert _em(["a", "b"])._to_dict(d) is d


def test_to_dict_scalar_single_mapping():
    """A scalar value with a 1-key mapping should be wrapped, not iterated."""
    assert _em(["name"])._to_dict("Alice") == {"name": "Alice"}


def test_to_dict_scalar_int():
    assert _em(["count"])._to_dict(42) == {"count": 42}


def test_to_dict_string_not_split():
    """'abc' must NOT become ['a','b','c'] — it is a scalar here."""
    assert _em(["code"])._to_dict("abc") == {"code": "abc"}


def test_to_dict_bytes_not_split():
    assert _em(["raw"])._to_dict(b"abc") == {"raw": b"abc"}


def test_to_dict_length_mismatch_raises():
    with pytest.raises(ValueError, match="mapping has 2 keys but value has 1"):
        _em(["a", "b"])._to_dict(("only_one",))


def test_to_dict_no_mapping_raises():
    em = ExecuteMany(url="sqlite:///:memory:", query="SELECT 1", mapping=None)
    with pytest.raises(ValueError, match="'mapping' must be set"):
        em._to_dict(("x", "y"))


# ---------------------------------------------------------------------------
# ExecuteStatements / ExecuteMany — positive-path tests against SQLite
# ---------------------------------------------------------------------------

sa = pytest.importorskip("sqlalchemy", reason="sqlalchemy not installed")


def _create_table(engine, ddl: str) -> None:
    with engine.begin() as conn:
        conn.execute(sa.text(ddl))


def _fetchall(engine, query: str) -> list:
    with engine.connect() as conn:
        return conn.execute(sa.text(query)).fetchall()


def test_execute_statements_inserts_rows():
    from scarfolder.loaders.sql import ExecuteStatements

    engine = sa.create_engine("sqlite:///:memory:")
    _create_table(engine, "CREATE TABLE names (name TEXT)")

    loader = ExecuteStatements(url="sqlite:///:memory:")
    # Re-use the same engine by monkeypatching _engine
    import scarfolder.loaders.sql as sql_mod
    original = sql_mod._engine
    sql_mod._engine = lambda _url: engine
    try:
        loader.load([
            "INSERT INTO names VALUES ('Alice')",
            "INSERT INTO names VALUES ('Bob')",
        ])
    finally:
        sql_mod._engine = original

    rows = _fetchall(engine, "SELECT name FROM names ORDER BY name")
    assert [r[0] for r in rows] == ["Alice", "Bob"]


def test_execute_statements_stop_on_error():
    from scarfolder.loaders.sql import ExecuteStatements

    engine = sa.create_engine("sqlite:///:memory:")
    _create_table(engine, "CREATE TABLE t (id INTEGER PRIMARY KEY)")

    import scarfolder.loaders.sql as sql_mod
    original = sql_mod._engine
    sql_mod._engine = lambda _url: engine
    try:
        loader = ExecuteStatements(url="sqlite:///:memory:", stop_on_error=True)
        with pytest.raises(sa.exc.IntegrityError):
            loader.load([
                "INSERT INTO t VALUES (1)",
                "INSERT INTO t VALUES (1)",  # duplicate PK — should abort
            ])
    finally:
        sql_mod._engine = original


def test_execute_many_inserts_rows():
    from scarfolder.loaders.sql import ExecuteMany

    engine = sa.create_engine("sqlite:///:memory:")
    _create_table(engine, "CREATE TABLE people (first TEXT, last TEXT)")

    import scarfolder.loaders.sql as sql_mod
    original = sql_mod._engine
    sql_mod._engine = lambda _url: engine
    try:
        loader = ExecuteMany(
            url="sqlite:///:memory:",
            query="INSERT INTO people (first, last) VALUES (:first, :last)",
            mapping=["first", "last"],
        )
        loader.load([("Alice", "Smith"), ("Bob", "Jones")])
    finally:
        sql_mod._engine = original

    rows = _fetchall(engine, "SELECT first, last FROM people ORDER BY first")
    assert rows == [("Alice", "Smith"), ("Bob", "Jones")]


def test_execute_many_with_dict_values():
    from scarfolder.loaders.sql import ExecuteMany

    engine = sa.create_engine("sqlite:///:memory:")
    _create_table(engine, "CREATE TABLE items (code TEXT, qty INTEGER)")

    import scarfolder.loaders.sql as sql_mod
    original = sql_mod._engine
    sql_mod._engine = lambda _url: engine
    try:
        loader = ExecuteMany(
            url="sqlite:///:memory:",
            query="INSERT INTO items (code, qty) VALUES (:code, :qty)",
        )
        loader.load([{"code": "A1", "qty": 10}, {"code": "B2", "qty": 5}])
    finally:
        sql_mod._engine = original

    rows = _fetchall(engine, "SELECT code, qty FROM items ORDER BY code")
    assert rows == [("A1", 10), ("B2", 5)]
