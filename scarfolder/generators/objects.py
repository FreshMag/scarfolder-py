"""Object composition generator."""
from __future__ import annotations

from typing import Any, Iterable

from scarfolder.core.base import Generator
from scarfolder.core.registry import make_generator, make_transformer

_MISSING = object()


class ObjectGenerator(Generator):
    """Produce a list of dicts by composing named field generators.

    Each entry in *fields* must have a ``name`` key and either a
    ``generator`` key, a ``stream`` key, or both.  An optional
    ``transformers`` list can be added to any field to post-process its
    values before they are zipped into objects.

    Field config shapes
    -------------------
    * Generator only::

        - name: id
          generator:
            name: scarfolder.generators.util.Range
            args: {stop: 3}

    * Step reference (shorthand for ``From`` — resolved before instantiation)::

        - name: label
          stream: ${steps.labels}

    * Generator + transformers::

        - name: tag
          generator:
            name: scarfolder.generators.util.Constant
            args: {value: "hello", count: 3}
          transformers:
            - name: scarfolder.transformers.text.upper
              args: {}

    * Step reference + transformers::

        - name: name
          stream: ${steps.raw_names}
          transformers:
            - name: scarfolder.transformers.text.capitalize_first
              args: {}

    Results from all field generators are zipped by position — the output
    length equals the shortest field stream.  Nesting is fully supported: a
    field's generator can itself be an ``ObjectGenerator``.

    Example::

        generator:
          name: scarfolder.generators.objects.ObjectGenerator
          args:
            fields:
              - name: id
                generator:
                  name: scarfolder.generators.util.Range
                  args: {stop: 3}
              - name: label
                stream: ${steps.labels}
                transformers:
                  - name: scarfolder.transformers.text.upper
                    args: {}
        # → [{"id": 0, "label": "ITEM"}, {"id": 1, "label": "ITEM"}, ...]
    """

    def __init__(self, fields: list[dict[str, Any]]) -> None:
        # Each entry: (field_name, generator_or_None, pre_resolved_stream_or_MISSING, transformer_configs)
        self._fields: list[tuple[str, Generator | None, Any, list[dict[str, Any]]]] = []
        for field in fields:
            name = field["name"]
            transformer_cfgs: list[dict[str, Any]] = [
                {"name": t["name"], "args": t.get("args", {})}
                for t in field.get("transformers", [])
            ]

            if "generator" in field:
                gen_cfg = field["generator"]
                gen = make_generator(gen_cfg["name"], gen_cfg.get("args", {}))
                self._fields.append((name, gen, _MISSING, transformer_cfgs))
            elif "stream" in field:
                # stream is already resolved to a list by the pipeline resolver
                self._fields.append((name, None, field["stream"], transformer_cfgs))
            else:
                raise ValueError(
                    f"Field '{name}' must have either a 'generator' or a 'stream' key."
                )

    def generate(self) -> Iterable[dict[str, Any]]:
        streams: list[list[Any]] = []
        keys: list[str] = []

        for name, gen, stream, transformer_cfgs in self._fields:
            keys.append(name)
            values: list[Any] = list(gen.generate()) if gen is not None else list(stream)

            for t_cfg in transformer_cfgs:
                values = list(
                    make_transformer(t_cfg["name"], {**t_cfg["args"], "values": values}).transform()
                )

            streams.append(values)

        return [dict(zip(keys, row)) for row in zip(*streams)]
