"""Pipeline orchestration: dependency resolution and step execution."""
from __future__ import annotations

from collections import deque
from typing import Any

from scarfolder.config.resolver import extract_step_deps, resolve
from scarfolder.config.schema import ScarConfig, StepConfig
from scarfolder.core.context import ExecutionContext
from scarfolder.core.registry import make_generator, make_loader, make_transformer
from scarfolder.exceptions import (
    CircularDependencyError,
    ConfigError,
    ScarfolderError,
    StepExecutionError,
)


# ---------------------------------------------------------------------------
# Topological sort (Kahn's algorithm)
# ---------------------------------------------------------------------------

def _topological_sort(steps: list[StepConfig]) -> list[StepConfig]:
    """Return *steps* in an order that satisfies all ``${steps.xxx}`` deps.

    Raises :class:`~scarfolder.exceptions.ConfigError` if a step references
    an unknown step id, and
    :class:`~scarfolder.exceptions.CircularDependencyError` when a cycle is
    detected.
    """
    id_to_idx: dict[str, int] = {
        s.id: i for i, s in enumerate(steps) if s.id is not None
    }

    # in_degree[i]  = number of steps i must wait for
    # dependents[j] = list of step indices that depend on j
    in_degree: list[int] = [0] * len(steps)
    dependents: list[list[int]] = [[] for _ in range(len(steps))]

    for i, step in enumerate(steps):
        step_label = step.id or f"(index {i})"
        for dep_id in extract_step_deps(step.model_dump()):
            if dep_id not in id_to_idx:
                raise ConfigError(
                    f"Step '{step_label}' references unknown step id '{dep_id}'."
                )
            j = id_to_idx[dep_id]
            dependents[j].append(i)
            in_degree[i] += 1

    queue: deque[int] = deque(i for i in range(len(steps)) if in_degree[i] == 0)
    result: list[StepConfig] = []

    while queue:
        i = queue.popleft()
        result.append(steps[i])
        for j in dependents[i]:
            in_degree[j] -= 1
            if in_degree[j] == 0:
                queue.append(j)

    if len(result) != len(steps):
        raise CircularDependencyError(
            "Circular dependency detected between steps. "
            "Check your ${steps.*} references."
        )
    return result


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

class Pipeline:
    """Orchestrates execution of a full Scarf pipeline.

    Usage::

        config, merged_args, refs = load_scarf(path, cli_args)
        ctx = Pipeline(config, merged_args, refs).run()
    """

    def __init__(
        self,
        config: ScarConfig,
        merged_args: dict[str, Any],
        refs: dict[str, Any],
    ) -> None:
        self.config = config
        self.context = ExecutionContext(args=merged_args, refs=refs)

    def run(self) -> ExecutionContext:
        """Execute all steps in dependency order.

        Returns the :class:`~scarfolder.core.context.ExecutionContext` so
        callers can inspect step outputs after the run.
        """
        ordered = _topological_sort(self.config.steps)
        for step in ordered:
            self._execute_step(step)
        return self.context

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _execute_step(self, step: StepConfig) -> None:
        label = step.id or "(unnamed)"
        ns = self.context.to_namespace_dict()

        try:
            # --- Generator -------------------------------------------
            gen_args = resolve(step.generator.args, ns)
            generator = make_generator(step.generator.name, gen_args)
            values: list[Any] = list(generator.generate())

            # --- Transformer (optional) ------------------------------
            if step.transformer is not None:
                tr_args = resolve(step.transformer.args, ns)
                transformer = make_transformer(step.transformer.name, tr_args)
                values = list(transformer.transform(values))

            # --- Store output for downstream steps -------------------
            if step.id is not None:
                self.context.set_step_output(step.id, values)

            # --- Loader (optional, terminal) -------------------------
            if step.loader is not None:
                ld_args = resolve(step.loader.args, ns)
                loader = make_loader(step.loader.name, ld_args)
                loader.load(values)

        except ScarfolderError:
            raise
        except Exception as exc:
            raise StepExecutionError(
                f"Step '{label}' raised an unexpected error: {exc}"
            ) from exc
