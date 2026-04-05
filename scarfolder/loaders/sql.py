"""SQL loaders (requires SQLAlchemy: ``pip install sqlalchemy``).

Each value passed to the loader is expected to be a ready-to-execute SQL
string (produced by a transformer).  For bulk inserts of structured data,
use ``ExecuteMany`` with a parameterised query template instead.

Connection URL format (SQLAlchemy):
  postgresql+psycopg2://user:pass@host:5432/dbname
  mysql+pymysql://user:pass@host:3306/dbname
  sqlite:///path/to/file.db
  sqlite:///:memory:
"""
from __future__ import annotations

from typing import Any

from scarfolder.core.base import Loader
from scarfolder.exceptions import PluginError


def _sqlalchemy():
    """Return the sqlalchemy module, raising a clean error if absent."""
    try:
        import sqlalchemy
        return sqlalchemy
    except ImportError as exc:
        raise PluginError(
            "SQLAlchemy is required for SQL loaders. "
            "Install it with: pip install scarfolder[sql]"
        ) from exc


def _engine(url: str) -> Any:
    sa = _sqlalchemy()
    return sa.create_engine(url)


class ExecuteStatements(Loader):
    """Execute each value as a raw SQL statement.

    Values are expected to be complete, ready-to-run SQL strings produced
    by an upstream transformer (e.g. ``INSERT INTO …``).

    Args:
        url:         SQLAlchemy connection URL.
        echo:        Log every executed statement (default ``false``).
        stop_on_error: Abort the batch on the first failure (default ``true``).

    Example::

        loader:
          name: scarfolder.loaders.sql.ExecuteStatements
          args:
            url: postgresql+psycopg2://postgres:${env.DB_PASSWORD}@localhost:5432/mydb
    """

    def __init__(
        self,
        url: str,
        echo: bool = False,
        stop_on_error: bool = True,
    ) -> None:
        self.url = url
        self.echo = echo
        self.stop_on_error = stop_on_error

    def load(self, values: list[Any]) -> None:
        text = _sqlalchemy().text

        engine = _engine(self.url)
        if self.echo:
            engine.echo = True

        errors: list[tuple[int, str, Exception]] = []
        with engine.begin() as conn:
            for i, stmt in enumerate(values):
                try:
                    conn.execute(text(str(stmt)))
                except Exception as exc:
                    if self.stop_on_error:
                        raise
                    errors.append((i, str(stmt), exc))

        if errors:
            summary = "\n".join(
                f"  [{i}] {stmt!r}: {exc}" for i, stmt, exc in errors
            )
            raise RuntimeError(
                f"{len(errors)} statement(s) failed:\n{summary}"
            )


class ExecuteMany(Loader):
    """Execute one parameterised SQL statement for every value in the stream.

    Each value is passed as a parameter dict (or will be wrapped in one if
    it is a plain scalar or tuple).

    Args:
        url:      SQLAlchemy connection URL.
        query:    Parameterised SQL with ``:name`` placeholders, e.g.
                  ``INSERT INTO people (name, dob) VALUES (:name, :dob)``
        mapping:  When values are tuples/lists, map positional indices to
                  parameter names: ``["name", "dob"]``.
                  When values are already dicts, this can be omitted.
        echo:     Log every executed statement (default ``false``).

    Example (values are tuples from a Combine step)::

        loader:
          name: scarfolder.loaders.sql.ExecuteMany
          args:
            url: postgresql+psycopg2://postgres:${env.DB_PASSWORD}@localhost/mydb
            query: "INSERT INTO people (first_name, last_name) VALUES (:first_name, :last_name)"
            mapping: [first_name, last_name]
    """

    def __init__(
        self,
        url: str,
        query: str,
        mapping: list[str] | None = None,
        echo: bool = False,
    ) -> None:
        self.url = url
        self.query = query
        self.mapping = mapping
        self.echo = echo

    def _to_dict(self, value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if self.mapping is None:
            raise ValueError(
                "ExecuteMany: 'mapping' must be set when values are not dicts. "
                f"Got: {type(value).__name__}"
            )
        # Treat lists and tuples as positional sequences.
        # Wrap scalars (including strings/bytes) as a 1-item sequence rather
        # than iterating over them, which would split "abc" into ['a','b','c'].
        if isinstance(value, (list, tuple)):
            items: list[Any] = list(value)
        elif isinstance(value, (str, bytes, bytearray)) or not hasattr(value, "__iter__"):
            items = [value]
        else:
            # Other iterables (e.g. generators) — consume once into a list.
            items = list(value)
        if len(items) != len(self.mapping):
            raise ValueError(
                f"ExecuteMany: mapping has {len(self.mapping)} keys but "
                f"value has {len(items)} element(s). "
                f"Mapping: {self.mapping!r}, value: {value!r}"
            )
        return dict(zip(self.mapping, items))

    def load(self, values: list[Any]) -> None:
        text = _sqlalchemy().text

        engine = _engine(self.url)
        if self.echo:
            engine.echo = True

        params = [self._to_dict(v) for v in values]
        with engine.begin() as conn:
            conn.execute(text(self.query), params)
