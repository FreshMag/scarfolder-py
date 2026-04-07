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
# Transform pipeline (Constant → capitalize_first transformer)
# ---------------------------------------------------------------------------

def test_transform_pipeline():
    config, args, refs = load_scarf(FIXTURES / "transform.yaml", {})
    ctx = Pipeline(config, args, refs).run()
    result = ctx.get_step_output("words")
    assert result == ["Hello", "Hello", "Hello"]


# ---------------------------------------------------------------------------
# Step dependency pipeline (Combine + join transformer)
# ---------------------------------------------------------------------------

def test_dependency_pipeline():
    config, args, refs = load_scarf(FIXTURES / "dependency.yaml", {})
    ctx = Pipeline(config, args, refs).run()
    full_names = ctx.get_step_output("full_names")
    assert full_names == ["Alice Smith", "Alice Smith"]


# ---------------------------------------------------------------------------
# CLI arg override
# ---------------------------------------------------------------------------

def test_cli_arg_override():
    config, args, refs = load_scarf(FIXTURES / "with_args.yaml", {"lang": "en"})
    assert args["lang"] == "en"


# ---------------------------------------------------------------------------
# Schema: generator + chained transformer is valid
# ---------------------------------------------------------------------------

def test_generator_with_chained_transformer_is_valid():
    step = StepConfig(
        id="x",
        generator={"name": "pkg.G", "args": {}},
        transformer={"name": "pkg.T", "args": {}},
    )
    assert step.generator is not None
    assert len(step.transformers) == 1


def test_transformer_list_normalised():
    step = StepConfig(
        transformers=[
            {"name": "pkg.T1", "args": {}},
            {"name": "pkg.T2", "args": {}},
        ]
    )
    assert len(step.transformers) == 2


def test_loader_list_normalised():
    step = StepConfig(
        generator={"name": "pkg.G", "args": {}},
        loaders=[
            {"name": "pkg.L1", "args": {}},
            {"name": "pkg.L2", "args": {}},
        ],
    )
    assert len(step.loaders) == 2


def test_step_with_no_plugin_raises():
    with pytest.raises(Exception):
        StepConfig()


def test_both_transformer_and_transformers_raises():
    with pytest.raises(Exception):
        StepConfig(
            generator={"name": "pkg.G", "args": {}},
            transformer={"name": "pkg.T1", "args": {}},
            transformers=[{"name": "pkg.T2", "args": {}}],
        )


# ---------------------------------------------------------------------------
# Inline chaining integration test
# ---------------------------------------------------------------------------

def test_generator_with_inline_transformer_chain():
    """Generator + two chained transformers in one step, no extra steps needed."""
    config = ScarConfig(
        name="chain-test",
        steps=[
            StepConfig(
                id="result",
                generator={"name": "scarfolder.generators.util.Constant", "args": {"value": "hello", "count": 2}},
                transformers=[
                    {"name": "scarfolder.transformers.text.capitalize_first", "args": {}},
                    {"name": "scarfolder.transformers.text.upper", "args": {}},
                ],
            )
        ],
    )
    ctx = Pipeline(config, {}, {}).run()
    assert ctx.get_step_output("result") == ["HELLO", "HELLO"]


def test_generator_with_inline_loader(tmp_path):
    """Generator + inline loader, values auto-injected into loader."""
    out = tmp_path / "out.txt"
    config = ScarConfig(
        name="loader-test",
        steps=[
            StepConfig(
                generator={"name": "scarfolder.generators.util.Constant", "args": {"value": "x", "count": 3}},
                loaders=[{"name": "scarfolder.loaders.file.WriteLines", "args": {"path": str(out)}}],
            )
        ],
    )
    Pipeline(config, {}, {}).run()
    assert out.read_text().splitlines() == ["x", "x", "x"]


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


def test_toposort_picks_up_deps_in_chained_transformer_args():
    """A ${steps.*} ref in a chained transformer's args contributes to deps."""
    step_a = StepConfig(id="a", generator={"name": "pkg.G", "args": {"value": "x"}})
    step_b = StepConfig(
        id="b",
        generator={"name": "pkg.G", "args": {"value": "y"}},
        transformers=[{"name": "pkg.T", "args": {"extra": "${steps.a}"}}],
    )
    result = _topological_sort([step_a, step_b])
    assert result[0].id == "a"
    assert result[1].id == "b"
