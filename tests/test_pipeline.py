"""Integration tests for the Pipeline."""
from pathlib import Path

import pytest

from scarfolder.config.loader import load_scarf
from scarfolder.core.pipeline import Pipeline, _topological_sort
from scarfolder.config.schema import ScarConfig, StepConfig
from scarfolder.exceptions import CircularDependencyError, ConfigError

FIXTURES = Path(__file__).parent / "fixtures"


# ---------------------------------------------------------------------------
# Simple pipeline (Range generator, no transformer/loader)
# ---------------------------------------------------------------------------

def test_simple_range_pipeline():
    config, args, refs = load_scarf(FIXTURES / "simple.yaml", {})
    ctx = Pipeline(config, args, refs).run()
    assert ctx.get_step_output("numbers") == list(range(5))


# ---------------------------------------------------------------------------
# Transform pipeline (Constant + capitalize_first)
# ---------------------------------------------------------------------------

def test_transform_pipeline():
    config, args, refs = load_scarf(FIXTURES / "transform.yaml", {})
    ctx = Pipeline(config, args, refs).run()
    result = ctx.get_step_output("words")
    assert result == ["Hello", "Hello", "Hello"]


# ---------------------------------------------------------------------------
# Step dependency pipeline (Combine + join)
# ---------------------------------------------------------------------------

def test_dependency_pipeline():
    config, args, refs = load_scarf(FIXTURES / "dependency.yaml", {})
    ctx = Pipeline(config, args, refs).run()
    full_names = ctx.get_step_output("full_names")
    # Constant("Alice", 2) x Constant("Smith", 2) → zip → join
    assert full_names == ["Alice Smith", "Alice Smith"]


# ---------------------------------------------------------------------------
# CLI arg override
# ---------------------------------------------------------------------------

def test_cli_arg_override():
    config, args, refs = load_scarf(FIXTURES / "with_args.yaml", {"lang": "en"})
    assert args["lang"] == "en"


# ---------------------------------------------------------------------------
# Topological sort
# ---------------------------------------------------------------------------

def _make_step(id_: str | None, dep_ids: list[str]) -> StepConfig:
    """Build a minimal StepConfig with step dependencies in generator args."""
    streams = {f"s{i}": f"${{steps.{dep}}}" for i, dep in enumerate(dep_ids)}
    return StepConfig(
        id=id_,
        generator={"name": "scarfolder.generators.util.Constant", "args": streams or {"value": "x"}},
    )


def test_toposort_respects_deps():
    steps = [
        _make_step("a", []),
        _make_step("b", ["a"]),
        _make_step("c", ["a", "b"]),
    ]
    result = _topological_sort(steps)
    ids = [s.id for s in result]
    assert ids.index("a") < ids.index("b")
    assert ids.index("b") < ids.index("c")


def test_toposort_detects_cycle():
    # Build a cycle manually by giving both steps fake dep args
    step_a = StepConfig(
        id="a",
        generator={"name": "pkg.G", "args": {"x": "${steps.b}"}},
    )
    step_b = StepConfig(
        id="b",
        generator={"name": "pkg.G", "args": {"x": "${steps.a}"}},
    )
    with pytest.raises(CircularDependencyError):
        _topological_sort([step_a, step_b])


def test_toposort_unknown_dep():
    step = StepConfig(
        id="x",
        generator={"name": "pkg.G", "args": {"s": "${steps.nonexistent}"}},
    )
    with pytest.raises(ConfigError, match="unknown step id"):
        _topological_sort([step])
