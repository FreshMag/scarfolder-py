---
id: concepts
title: Concepts
sidebar_position: 2
---

# Concepts

## The pipeline model

A **Scarf** is a self-contained pipeline defined in a single `.yaml` file. It runs one or more **Steps**. Each step has three distinct plugin roles:

| Plugin | Role |
|---|---|
| **Generator** | Produces a list of values — from scratch, from args, or by consuming other steps' outputs via args |
| **Transformer** | Receives a list of values and returns a new list |
| **Loader** | Consumes a list of values as a terminal side-effect (write file, insert rows, print, …) — returns nothing |

## Steps

Every step has exactly one **primary producer** — either a `generator`, or a `transformer` that receives its input explicitly through args. On top of that, any step may declare chained transformers and fan-out loaders for a compact inline pipeline.

```
 generator (primary)
     │
     ▼
 transformer  ← values auto-injected
     │
     ▼
 transformer  ← values auto-injected
     │
     ├──▶ loader  ← values auto-injected
     └──▶ loader  ← values auto-injected
```

Each step can be given an `id`, making its output (the result after all chained transformers) available to downstream steps.

### Inline chaining

When a step declares a `generator` and also a `transformer` (or `transformers`), the transformer runs immediately after the generator. The pipeline automatically injects the generator's output as `values` into the transformer — no extra step or explicit `${steps.*}` reference needed:

```yaml
- id: names
  generator:
    name: scarfolder.generators.util.Constant
    args:
      value: alice
      count: 5
  transformer: scarfolder.transformers.text.capitalize_first   # values auto-injected
```

Multiple chained transformers are declared as a list:

```yaml
- id: greetings
  generator:
    name: scarfolder.generators.util.Constant
    args:
      value: hello
      count: 3
  transformers:
    - name: scarfolder.transformers.text.capitalize_first      # values auto-injected
    - name: scarfolder.transformers.text.format_template       # values auto-injected
      args:
        template: "Greeting: {value}"
```

### Inline loaders

A `loader` (or `loaders` list) attached to a step receives the final output automatically. Multiple loaders fan out from the same output:

```yaml
- generator:
    name: scarfolder.generators.util.Range
    args:
      stop: 10
  transformer:
    name: scarfolder.transformers.text.format_template
    args:
      template: "item {value}"
  loaders:
    - name: scarfolder.loaders.file.WriteLines
      args: { path: out.txt }
    - name: scarfolder.loaders.console.Print
```

### Standalone steps

When there is no generator, the first transformer acts as the primary producer and must carry explicit `args` — including any `${steps.*}` reference:

```yaml
- id: upper_names
  transformer:
    name: scarfolder.transformers.text.upper
    args:
      values: ${steps.names}    # explicit — no generator to auto-inject from
```

Loader-only steps work the same way:

```yaml
- loader:
    name: scarfolder.loaders.console.Print
    args:
      values: ${steps.greetings}
```

## Dependency resolution

Steps execute in **topological order** based on all `${steps.*}` references found anywhere in a step's args (including inside chained transformers and loaders). Declaration order in the YAML file does not matter. Scarfolder uses Kahn's algorithm and raises `CircularDependencyError` on cycles.

## Placeholders

All `args` values are resolved before the step runs using `${namespace.key}` syntax:

| Placeholder | Resolves to |
|---|---|
| `${args.key}` | A runtime argument (CLI or config default) |
| `${key}` | Shorthand for `${args.key}` |
| `${steps.id}` | The output list of a previously executed step |
| `${refname.key}` | A value from an external YAML file loaded via `refs:` |
| `${env.VAR}` | An OS environment variable |

**Type preservation:** a placeholder that is the entire value (e.g. `values: ${steps.names}`) receives the actual Python object — not its string representation. This is what allows lists to flow between steps.

## Plugin resolution

Every plugin is referenced by its **fully qualified dotted path**:

```
scarfolder.generators.util.Range
my_project.loaders.WriteCsv
```

Scarfolder supports two plugin styles:

- **Class-based** — subclass `Generator`, `Transformer`, or `Loader` from `scarfolder.core.base`. Constructor args come from the resolved `args` block. Action methods (`generate`, `transform`, `load`) take no positional arguments.
- **Function-based** — any plain callable. All resolved args are passed as keyword arguments. The data input (e.g. `values`) is just another named keyword argument.

See [Custom Plugins](./custom-plugins.md) for examples of both styles.
