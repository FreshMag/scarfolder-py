"""Runtime state threaded through a pipeline execution."""
from __future__ import annotations

import os
from typing import Any

from scarfolder.exceptions import ResolutionError


class ExecutionContext:
    """Holds all state available during a pipeline run.

    Exposes three namespaces to the placeholder resolver:

    * ``args``  – merged CLI params + config defaults.
    * ``steps`` – outputs of completed steps, keyed by step ``id``.
    * ``env``   – OS environment variables (``${env.MY_VAR}``).
    * Any ref name loaded from the ``refs`` section of the scarf YAML
      (e.g. ``queries`` → contents of ``queries.yaml``).
    """

    def __init__(
        self,
        args: dict[str, Any],
        refs: dict[str, Any] | None = None,
    ) -> None:
        self.args: dict[str, Any] = args
        self.refs: dict[str, Any] = refs or {}
        self._steps: dict[str, list[Any]] = {}

    # ------------------------------------------------------------------
    # Step output management
    # ------------------------------------------------------------------

    def set_step_output(self, step_id: str, values: list[Any]) -> None:
        self._steps[step_id] = values

    def get_step_output(self, step_id: str) -> list[Any]:
        if step_id not in self._steps:
            raise ResolutionError(
                f"Step output '{step_id}' is not available. "
                "Either the step hasn't run yet or it has no 'id'."
            )
        return self._steps[step_id]

    # ------------------------------------------------------------------
    # Namespace dict (fed into the resolver)
    # ------------------------------------------------------------------

    def to_namespace_dict(self) -> dict[str, Any]:
        """Return a flat namespace mapping used by placeholder resolution.

        Structure::

            {
                "args":   {"lang": "it", ...},
                "steps":  {"names": [...], ...},
                "env":    {"DB_PASSWORD": "...", ...},  # os.environ
                "<ref>":  {...},   # one entry per loaded refs YAML
            }
        """
        return {
            "args": self.args,
            "steps": self._steps,
            "env": os.environ,
            **self.refs,
        }
