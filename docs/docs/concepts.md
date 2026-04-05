---
id: concepts
title: Concepts
sidebar_position: 2
---

# Concepts

## The pipeline model

A **Scarf** is a self-contained pipeline defined in a single `.yaml` file. It runs one or more **Steps**, each composed of up to three plugins executed in sequence:

```
Generator  ──▶  Transformer  ──▶  Loader
(required)      (optional)        (optional)
```

| Plugin | Role |
|---|---|
| **Generator** | Produces a `list` of values |
| **Transformer** | Receives the list, returns a new list |
| **Loader** | Consumes the final list — a terminal side-effect (write file, insert rows, print, …) |

## Steps

Each step runs independently. Steps can optionally declare an `id`, which makes their output available to downstream steps:

```yaml
steps:
  - id: names          # other steps can reference ${steps.names}
    generator:
      name: my_pkg.generators.Name
      args:
        count: 5

  - generator:         # no id — cannot be referenced, but still runs
      name: scarfolder.generators.util.From
      args:
        stream: ${steps.names}
    loader: my_pkg.loaders.Print
```

## Dependency resolution

Steps are executed in **topological order** based on their `${steps.*}` references — not the order they appear in the file. Scarfolder uses Kahn's algorithm to sort them and raises an error if a circular dependency is detected.

## Placeholders

Values in `args` blocks are resolved before each step runs using `${namespace.key}` syntax:

| Placeholder | Resolves to |
|---|---|
| `${args.key}` | A runtime argument (CLI or config default) |
| `${key}` | Shorthand for `${args.key}` |
| `${steps.id}` | The output list of a previously executed step |
| `${refname.key}` | A value from an external YAML file loaded via `refs:` |

**Type preservation:** a placeholder that is the entire value (e.g. `stream: ${steps.names}`) receives the actual Python object, not its string representation. This is what allows lists to flow between steps.

## Plugin resolution

Every plugin is referenced by its **fully qualified dotted path** — the same string you would pass to Python's `importlib.import_module` plus an attribute. For example:

```
scarfolder.generators.util.Range
my_project.loaders.WriteCsv
```

Scarfolder supports two plugin styles:

- **Class-based** — subclass `Generator`, `Transformer`, or `Loader` from `scarfolder.core.base`. Constructor arguments come from the `args` block.
- **Function-based** — any plain callable. Generators receive `**kwargs`; transformers and loaders receive `(values, **kwargs)`.

See [Custom Plugins](./custom-plugins.md) for examples of both styles.
