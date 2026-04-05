"""Unit tests for the placeholder resolver."""
import pytest

from scarfolder.config.resolver import (
    extract_step_deps,
    find_placeholders,
    resolve,
)
from scarfolder.exceptions import ResolutionError


# ---------------------------------------------------------------------------
# find_placeholders
# ---------------------------------------------------------------------------

def test_find_in_string():
    phs = find_placeholders("${args.lang}")
    assert phs == {"args.lang"}


def test_find_in_nested_dict():
    value = {"a": "${args.lang}", "b": {"c": "${steps.names}"}}
    phs = find_placeholders(value)
    assert phs == {"args.lang", "steps.names"}


def test_find_in_list():
    phs = find_placeholders(["${steps.a}", "${steps.b}"])
    assert phs == {"steps.a", "steps.b"}


def test_find_none_returns_empty():
    assert find_placeholders(None) == set()


def test_find_non_string_scalar():
    assert find_placeholders(42) == set()


# ---------------------------------------------------------------------------
# extract_step_deps
# ---------------------------------------------------------------------------

def test_extract_step_deps_simple():
    args = {"streams": ["${steps.names}", "${steps.surnames}"]}
    assert extract_step_deps(args) == {"names", "surnames"}


def test_extract_step_deps_no_step_refs():
    assert extract_step_deps({"lang": "${args.language}"}) == set()


# ---------------------------------------------------------------------------
# resolve — basic cases
# ---------------------------------------------------------------------------

def test_resolve_args_namespace():
    ns = {"args": {"lang": "it"}, "steps": {}}
    assert resolve("${args.lang}", ns) == "it"


def test_resolve_bare_key_shorthand():
    ns = {"args": {"lang": "it"}, "steps": {}}
    assert resolve("${lang}", ns) == "it"


def test_resolve_mixed_string():
    ns = {"args": {"name": "Alice"}, "steps": {}}
    result = resolve("Hello, ${args.name}!", ns)
    assert result == "Hello, Alice!"


def test_resolve_preserves_list_type():
    ns = {"args": {}, "steps": {"names": ["Alice", "Bob"]}}
    result = resolve("${steps.names}", ns)
    assert result == ["Alice", "Bob"]
    assert isinstance(result, list)


def test_resolve_nested_ref_key():
    ns = {"args": {}, "steps": {}, "queries": {"person": "INSERT INTO people …"}}
    assert resolve("${queries.person}", ns) == "INSERT INTO people …"


def test_resolve_dict_recursively():
    ns = {"args": {"lang": "it", "count": 5}, "steps": {}}
    result = resolve({"language": "${args.lang}", "n": "${args.count}"}, ns)
    assert result == {"language": "it", "n": 5}


def test_resolve_list_of_step_outputs():
    ns = {"args": {}, "steps": {"a": [1, 2], "b": [3, 4]}}
    result = resolve(["${steps.a}", "${steps.b}"], ns)
    assert result == [[1, 2], [3, 4]]


def test_resolve_scalar_passthrough():
    ns = {"args": {}, "steps": {}}
    assert resolve(42, ns) == 42
    assert resolve(3.14, ns) == 3.14
    assert resolve(True, ns) is True


# ---------------------------------------------------------------------------
# resolve — error cases
# ---------------------------------------------------------------------------

def test_resolve_unknown_namespace():
    with pytest.raises(ResolutionError, match="unknown"):
        resolve("${unknown.key}", {"args": {}, "steps": {}})


def test_resolve_missing_args_key():
    with pytest.raises(ResolutionError):
        resolve("${args.missing}", {"args": {}, "steps": {}})
