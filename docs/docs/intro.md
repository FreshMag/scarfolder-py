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
description: Print a sequence of integers

steps:
  - id: numbers
    generator:
      name: scarfolder.generators.util.Range
      args:
        start: 1
        stop: 6
    transformer: scarfolder.transformers.text.format_template
```

Wait — `format_template` needs a `template` arg. Let's add it:

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
```

Run it:

```bash
scarfolder run hello.yaml
```

You should see the generated values printed to stdout.

## Next steps

- [Concepts](./concepts.md) — understand the Generator → Transformer → Loader model
- [Configuration](./configuration.md) — full YAML reference including args and refs
- [Built-in Plugins](./plugins.md) — all built-in generators, transformers, and loaders
- [Custom Plugins](./custom-plugins.md) — write your own plugins
