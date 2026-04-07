"""Pydantic models for the Scarf YAML configuration.

Normalisation rules applied during parsing:

* A plugin reference that is a plain string ``"pkg.Cls"`` is expanded to
  ``{"name": "pkg.Cls", "args": {}}``.
* ``args`` defaults to ``{}`` when omitted.
* ``transformer`` and ``transformers`` are aliases for the same field; a
  single value is normalised into a one-element list.
* ``loader`` and ``loaders`` follow the same alias rule.

Step execution model
--------------------
Each step executes in three phases:

1. **Primary producer** — exactly one of:
   - A ``generator`` (produces values from scratch or from other steps' args).
   - The *first* transformer in ``transformers`` when no generator is present
     (must carry explicit ``args`` including any ``${steps.*}`` references).

2. **Chained transformers** — any remaining ``transformers`` after the primary.
   The pipeline auto-injects ``values=<previous_output>`` into each one.

3. **Fan-out loaders** — all ``loaders`` consume the final output in sequence.
   The pipeline auto-injects ``values=<final_output>`` into each one.

The step ``id`` refers to the output produced *after* phase 2 (before loaders).
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field, model_validator


class PluginRef(BaseModel):
    """Reference to a Generator, Transformer, or Loader plugin."""

    name: str
    args: dict[str, Any] = Field(default_factory=dict)


def _normalise_plugin(raw: str | dict | None) -> dict | None:
    """Expand a bare string plugin reference into the canonical dict form."""
    if raw is None:
        return None
    if isinstance(raw, str):
        return {"name": raw, "args": {}}
    return {"name": raw["name"], "args": raw.get("args") or {}}


def _normalise_plugin_list(raw: Any) -> list[dict]:
    """Normalise a single plugin ref or a list of them into a list of dicts."""
    if raw is None:
        return []
    if isinstance(raw, list):
        return [_normalise_plugin(item) for item in raw]
    return [_normalise_plugin(raw)]


class StepConfig(BaseModel):
    """Configuration for a single pipeline step.

    A step must declare at least one of ``generator``, ``transformer`` /
    ``transformers``, or ``loader`` / ``loaders``.

    When a ``generator`` is present, all declared transformers are *chained*
    after it (``values`` auto-injected).  When no generator is present the
    first transformer acts as the primary producer and must supply explicit
    args; remaining transformers are chained.  All loaders always receive
    ``values`` from the final output automatically.
    """

    id: Optional[str] = None
    generator: Optional[PluginRef] = None
    transformers: list[PluginRef] = Field(default_factory=list)
    loaders: list[PluginRef] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalise(cls, data: dict) -> dict:
        data = dict(data)  # avoid mutating the caller's dict

        # Generator
        data["generator"] = _normalise_plugin(data.pop("generator", None))

        # Transformers — accept "transformer" (single or list) or "transformers"
        raw_single = data.pop("transformer", None)
        raw_plural = data.pop("transformers", None)
        if raw_single is not None and raw_plural is not None:
            raise ValueError(
                "Specify either 'transformer' or 'transformers', not both."
            )
        data["transformers"] = _normalise_plugin_list(
            raw_single if raw_single is not None else raw_plural
        )

        # Loaders — accept "loader" (single or list) or "loaders"
        raw_single = data.pop("loader", None)
        raw_plural = data.pop("loaders", None)
        if raw_single is not None and raw_plural is not None:
            raise ValueError(
                "Specify either 'loader' or 'loaders', not both."
            )
        data["loaders"] = _normalise_plugin_list(
            raw_single if raw_single is not None else raw_plural
        )

        return data

    @model_validator(mode="after")
    def _validate(self) -> "StepConfig":
        if not self.generator and not self.transformers and not self.loaders:
            raise ValueError(
                "A step must have at least one of: generator, transformer(s), loader(s)."
            )
        return self

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def all_plugin_args(self) -> list[dict[str, Any]]:
        """All raw args dicts across every plugin in this step.

        Used by the topological sort to discover ``${steps.*}`` dependencies.
        """
        args: list[dict[str, Any]] = []
        if self.generator:
            args.append(self.generator.args)
        for t in self.transformers:
            args.append(t.args)
        for ld in self.loaders:
            args.append(ld.args)
        return args


class ScarConfig(BaseModel):
    """Top-level Scarf pipeline configuration."""

    name: str
    description: Optional[str] = None

    # External YAML references: {ref_name: relative_path}
    refs: dict[str, str] = Field(default_factory=dict)

    # Default arg values.  A null value marks a *required* arg that must be
    # supplied at runtime (via CLI or interactive prompt).
    args: dict[str, Any] = Field(default_factory=dict)

    steps: list[StepConfig]
