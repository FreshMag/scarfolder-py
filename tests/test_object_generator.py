"""Tests for ObjectGenerator."""
from __future__ import annotations

import pytest

from scarfolder.generators.objects import ObjectGenerator
from scarfolder.core.pipeline import Pipeline
from scarfolder.config.schema import ScarConfig, StepConfig


def _fields(*pairs: tuple[str, str, dict]) -> list[dict]:
    """Build a fields list from (field_name, gen_name, gen_args) triples."""
    return [
        {"name": name, "generator": {"name": gen, "args": args}}
        for name, gen, args in pairs
    ]


# ---------------------------------------------------------------------------
# Basic flat object
# ---------------------------------------------------------------------------

def test_flat_object():
    gen = ObjectGenerator(fields=_fields(
        ("id",    "scarfolder.generators.util.Range",    {"stop": 3}),
        ("label", "scarfolder.generators.util.Constant", {"value": "x", "count": 3}),
    ))
    result = list(gen.generate())
    assert result == [
        {"id": 0, "label": "x"},
        {"id": 1, "label": "x"},
        {"id": 2, "label": "x"},
    ]


# ---------------------------------------------------------------------------
# Zips to shortest stream
# ---------------------------------------------------------------------------

def test_zips_to_shortest():
    gen = ObjectGenerator(fields=_fields(
        ("a", "scarfolder.generators.util.Range",    {"stop": 5}),
        ("b", "scarfolder.generators.util.Constant", {"value": "y", "count": 3}),
    ))
    result = list(gen.generate())
    assert len(result) == 3
    assert result[0] == {"a": 0, "b": "y"}


# ---------------------------------------------------------------------------
# Nested ObjectGenerator
# ---------------------------------------------------------------------------

def test_nested_object():
    gen = ObjectGenerator(fields=[
        {"name": "id", "generator": {
            "name": "scarfolder.generators.util.Range",
            "args": {"stop": 2},
        }},
        {"name": "meta", "generator": {
            "name": "scarfolder.generators.objects.ObjectGenerator",
            "args": {
                "fields": _fields(
                    ("active", "scarfolder.generators.util.Constant",
                     {"value": True, "count": 2}),
                )
            },
        }},
    ])
    result = list(gen.generate())
    assert result == [
        {"id": 0, "meta": {"active": True}},
        {"id": 1, "meta": {"active": True}},
    ]


# ---------------------------------------------------------------------------
# Single-field object
# ---------------------------------------------------------------------------

def test_single_field():
    gen = ObjectGenerator(fields=_fields(
        ("value", "scarfolder.generators.util.Constant", {"value": 42, "count": 2}),
    ))
    assert list(gen.generate()) == [{"value": 42}, {"value": 42}]


# ---------------------------------------------------------------------------
# Transformer on a generated field
# ---------------------------------------------------------------------------

def test_field_with_transformer():
    gen = ObjectGenerator(fields=[
        {
            "name": "tag",
            "generator": {
                "name": "scarfolder.generators.util.Constant",
                "args": {"value": "hello", "count": 2},
            },
            "transformers": [
                {"name": "scarfolder.transformers.text.upper", "args": {}},
            ],
        },
    ])
    assert list(gen.generate()) == [{"tag": "HELLO"}, {"tag": "HELLO"}]


# ---------------------------------------------------------------------------
# stream shorthand (pre-resolved list, no generator)
# ---------------------------------------------------------------------------

def test_field_with_stream():
    gen = ObjectGenerator(fields=[
        {"name": "id",   "generator": {"name": "scarfolder.generators.util.Range",
                                       "args": {"stop": 2}}},
        {"name": "name", "stream": ["Alice", "Bob"]},
    ])
    assert list(gen.generate()) == [
        {"id": 0, "name": "Alice"},
        {"id": 1, "name": "Bob"},
    ]


# ---------------------------------------------------------------------------
# stream + transformer
# ---------------------------------------------------------------------------

def test_field_with_stream_and_transformer():
    gen = ObjectGenerator(fields=[
        {
            "name": "label",
            "stream": ["hello", "world"],
            "transformers": [
                {"name": "scarfolder.transformers.text.upper", "args": {}},
            ],
        },
    ])
    assert list(gen.generate()) == [{"label": "HELLO"}, {"label": "WORLD"}]


# ---------------------------------------------------------------------------
# Missing generator and stream raises
# ---------------------------------------------------------------------------

def test_field_missing_source_raises():
    with pytest.raises(ValueError, match="'generator' or a 'stream'"):
        ObjectGenerator(fields=[{"name": "x"}])


def test_field_both_generator_and_stream_raises():
    with pytest.raises(ValueError, match="both 'generator' and 'stream'"):
        ObjectGenerator(fields=[{
            "name": "x",
            "generator": {"name": "scarfolder.generators.util.Constant",
                          "args": {"value": 1, "count": 1}},
            "stream": [1],
        }])


# ---------------------------------------------------------------------------
# Integration: step reference resolved by pipeline, transformer applied
# ---------------------------------------------------------------------------

def test_pipeline_step_ref_with_transformer():
    config = ScarConfig(
        name="object-step-ref-test",
        steps=[
            StepConfig(
                id="tags",
                generator={
                    "name": "scarfolder.generators.util.Constant",
                    "args": {"value": "hello", "count": 2},
                },
            ),
            StepConfig(
                id="records",
                generator={
                    "name": "scarfolder.generators.objects.ObjectGenerator",
                    "args": {
                        "fields": [
                            {
                                "name": "n",
                                "generator": {
                                    "name": "scarfolder.generators.util.Range",
                                    "args": {"stop": 2},
                                },
                            },
                            {
                                "name": "tag",
                                "stream": "${steps.tags}",
                                "transformers": [
                                    {"name": "scarfolder.transformers.text.upper",
                                     "args": {}},
                                ],
                            },
                        ]
                    },
                },
            ),
        ],
    )
    ctx = Pipeline(config, {}, {}).run()
    assert ctx.get_step_output("records") == [
        {"n": 0, "tag": "HELLO"},
        {"n": 1, "tag": "HELLO"},
    ]


# ---------------------------------------------------------------------------
# Integration: ObjectGenerator inside a Pipeline step
# ---------------------------------------------------------------------------

def test_pipeline_integration():
    config = ScarConfig(
        name="object-gen-test",
        steps=[
            StepConfig(
                id="records",
                generator={
                    "name": "scarfolder.generators.objects.ObjectGenerator",
                    "args": {
                        "fields": _fields(
                            ("n", "scarfolder.generators.util.Range",
                             {"stop": 3}),
                            ("tag", "scarfolder.generators.util.Constant",
                             {"value": "ok", "count": 3}),
                        )
                    },
                },
            )
        ],
    )
    ctx = Pipeline(config, {}, {}).run()
    assert ctx.get_step_output("records") == [
        {"n": 0, "tag": "ok"},
        {"n": 1, "tag": "ok"},
        {"n": 2, "tag": "ok"},
    ]
