"""Pydantic models for the Scarf YAML configuration.

Normalisation rules applied during parsing:
* A plugin reference that is a plain string ``"pkg.Cls"`` is expanded to
  ``{"name": "pkg.Cls", "args": {}}``.
* ``args`` defaults to ``{}`` when omitted.
* A step without an ``id`` is valid (it cannot be referenced by other steps).
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
    # dict form: ensure 'args' key exists
    return {"name": raw["name"], "args": raw.get("args") or {}}


class StepConfig(BaseModel):
    """Configuration for a single pipeline step."""

    id: Optional[str] = None
    generator: PluginRef
    transformer: Optional[PluginRef] = None
    loader: Optional[PluginRef] = None

    @model_validator(mode="before")
    @classmethod
    def _normalise(cls, data: dict) -> dict:
        for field in ("generator", "transformer", "loader"):
            data[field] = _normalise_plugin(data.get(field))
        return data


class ScarConfig(BaseModel):
    """Top-level Scarf pipeline configuration."""

    name: str
    description: Optional[str] = None

    # External YAML references: {ref_name: relative_path}
    # Resolved values are accessible via ${ref_name.key} in placeholders.
    refs: dict[str, str] = Field(default_factory=dict)

    # Default arg values.  A null value marks a *required* arg that must be
    # supplied at runtime (via CLI or interactive prompt).
    args: dict[str, Any] = Field(default_factory=dict)

    steps: list[StepConfig]
