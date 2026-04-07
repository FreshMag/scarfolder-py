---
id: intro
title: Getting Started
slug: /
sidebar_position: 1
---

# Getting Started

**Scarfolder** is a Python CLI tool for data and file scaffolding via configurable YAML pipelines.

Define **generators**, **transformers**, and **loaders** — wire them together in a single YAML file — run anywhere.

## Requirements

- Python 3.11+
- pip

## Installation

```bash
git clone https://github.com/FreshMag/scarfolder-py
cd scarfolder-py

python3.11 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -e .
```

The `scarfolder` command is now available in your shell.

## Your first pipeline

Create a file called `hello.yaml`:

```yaml
name: hello-world

steps:
  - id: numbers
    generator:
      name: scarfolder.generators.util.Range
      args:
        start: 1
        stop: 6
    transformer:
      name: scarfolder.transformers.text.format_template
      args:
        template: "item {value}"
    loader: scarfolder.loaders.console.Print
```

Run it:

```bash
scarfolder run hello.yaml
```

This pipeline runs three plugins in one step: the `Range` generator produces `[1, 2, 3, 4, 5]`, `format_template` transforms each into `"item 1"`, `"item 2"`, etc., and `Print` writes them to stdout. No intermediate steps or explicit `${steps.*}` references needed.

## A multi-step pipeline

Steps can reference each other's outputs via `${steps.<id>}` in their `args`:

```yaml
name: greetings

args:
  count: 3

steps:
  - id: first_names
    generator:
      name: scarfolder.generators.util.Constant
      args:
        value: Alice
        count: ${args.count}

  - id: last_names
    generator:
      name: scarfolder.generators.util.Constant
      args:
        value: Smith
        count: ${args.count}

  - generator:
      name: scarfolder.generators.util.Combine
      args:
        streams:
          - ${steps.first_names}
          - ${steps.last_names}
    transformers:
      - name: scarfolder.transformers.text.join
      - name: scarfolder.transformers.text.format_template
        args:
          template: "Hello, {value}!"
    loader: scarfolder.loaders.console.Print
```

```bash
scarfolder run greetings.yaml -pcount=5
```

## Next steps

- [Concepts](./concepts.md) — understand generators, transformers, loaders, and inline chaining
- [Configuration](./configuration.md) — full YAML reference including args, refs, and step chaining
- [Built-in Plugins](./plugins.md) — all built-in generators, transformers, and loaders
- [Custom Plugins](./custom-plugins.md) — write your own plugins
