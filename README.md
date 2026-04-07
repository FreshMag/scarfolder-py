<div align="center">
  <img src="./images/logo.png" alt="Scarfolder logo" width="480" />
  <br/>
  <br/>
  <p>
    <strong>Data and file scaffolding via configurable YAML pipelines.</strong>
  </p>
  <p>
    Define generators, transformers, and loaders — wire them together in YAML — run anywhere.
  </p>
  <br/>
</div>

---

## Table of Contents

- [Concepts](#concepts)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Pipeline Configuration](#pipeline-configuration)
  - [Structure](#structure)
  - [Inline Chaining](#inline-chaining)
  - [Args & Placeholders](#args--placeholders)
  - [External Refs](#external-refs)
- [CLI Reference](#cli-reference)
- [Built-in Plugins](#built-in-plugins)
- [Writing Custom Plugins](#writing-custom-plugins)
- [Running with Docker](#running-with-docker)

---

## Concepts

A **Scarf** is a full pipeline defined in a single `.yaml` file. It contains one or more **Steps**. Each step has three plugin roles:

| Plugin | Role |
|---|---|
| **Generator** | Produces a list of values |
| **Transformer** | Receives a list and returns a new list |
| **Loader** | Consumes a list — writes files, runs queries, prints, etc. |

Each step can be given an `id` so its output can be referenced by downstream steps via `${steps.id}`.

Steps are executed in **topological order** — declaration order in the file does not matter.

---

## Installation

**Requirements:** Python 3.11+

```bash
git clone <repo-url> scarfolder-py
cd scarfolder-py

python3.11 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate

pip install -e .               # add [dev] for pytest
```

The `scarfolder` command is now available in your shell.

---

## Quick Start

```bash
# Run the included hello-world example
scarfolder run examples/hello_world/scarf.yaml

# Override a config arg at runtime
scarfolder run examples/hello_world/scarf.yaml -pcount=10 -poutput=out.txt

# Check a config file without running it
scarfolder validate examples/hello_world/scarf.yaml

# Inspect the steps of a pipeline
scarfolder list-steps examples/hello_world/scarf.yaml
```

---

## Pipeline Configuration

### Structure

```yaml
name: my-pipeline
description: Optional description

# (optional) External YAML files accessible via ${ref_name.key}
refs:
  queries: ./sql/queries.yaml

# Default argument values.
# Set a value to null to mark it as required — the CLI will prompt for it.
args:
  language: en
  count: 10
  output: null       # required — must be supplied via -p or interactive prompt

steps:
  - id: names                         # optional; required if referenced downstream
    generator:
      name: my_pkg.generators.Name
      args:
        language: ${args.language}
        count: ${args.count}

  - generator:
      name: scarfolder.generators.util.Combine
      args:
        streams:
          - ${steps.names}
          - ${steps.surnames}
    transformer: scarfolder.transformers.text.join
    loader:
      name: scarfolder.loaders.file.WriteLines
      args:
        path: ${args.output}
```

### Inline Chaining

A step can combine a generator, one or more transformers, and one or more loaders into a single declaration. The pipeline automatically injects the output of each stage as `values` into the next — no intermediate steps or explicit `${steps.*}` references needed.

```yaml
- id: greetings
  generator:
    name: scarfolder.generators.util.Constant
    args:
      value: hello
      count: 5
  transformers:
    - name: scarfolder.transformers.text.capitalize_first   # values auto-injected
    - name: scarfolder.transformers.text.format_template    # values auto-injected
      args:
        template: "Greeting: {value}"
  loaders:
    - name: scarfolder.loaders.console.Print                # values auto-injected
    - name: scarfolder.loaders.file.WriteLines              # values auto-injected
      args:
        path: output.txt
```

Use `transformer` (singular) and `loader` (singular) for the common single-item case. The plural forms accept a YAML list.

When a step has **no generator**, the first transformer is the primary producer and must declare its input explicitly:

```yaml
- id: upper_names
  transformer:
    name: scarfolder.transformers.text.upper
    args:
      values: ${steps.names}    # explicit — no generator to inject from
```

### Args & Placeholders

Placeholders use `${namespace.key}` syntax and are resolved before each step runs.

| Placeholder | Resolves to |
|---|---|
| `${args.key}` | A runtime argument (CLI or config default) |
| `${key}` | Shorthand for `${args.key}` |
| `${steps.id}` | The output list of a previously executed step |
| `${refname.key}` | A value from an external YAML file (see `refs:`) |
| `${env.VAR}` | An OS environment variable |

**Type preservation:** a value that is entirely a placeholder (e.g. `${steps.names}`) receives the actual Python object — not its string representation. This allows lists to flow between steps.

**Required args** are declared with a `null` default. If not provided via `-p`, the CLI prompts interactively.

### External Refs

```yaml
refs:
  queries: ./sql/queries.yaml

steps:
  - generator:
      name: my_pkg.generators.SqlRows
      args:
        query: ${queries.select_users}
```

---

## CLI Reference

```
scarfolder [OPTIONS] COMMAND [ARGS]
```

### `run`

```bash
scarfolder run SCARF_FILE [OPTIONS]

Options:
  -p, --param KEY=VALUE   Override or supply a config arg. Repeatable.
  --dry-run               Validate config without executing any steps.
```

### `validate`

Parse and validate a Scarf file without running it.

```bash
scarfolder validate SCARF_FILE
```

### `list-steps`

Print a summary of all steps and their plugin chains. Each step shows its full chain with role labels — `[G]` Generator, `[T]` Transformer, `[L]` Loader.

```bash
scarfolder list-steps SCARF_FILE
```

---

## Built-in Plugins

### Generators

| Path | Description |
|---|---|
| `scarfolder.generators.util.Constant` | Repeat a single value `count` times |
| `scarfolder.generators.util.Range` | Integer sequence (`start`, `stop`, `step`) |
| `scarfolder.generators.util.Combine` | Zip multiple streams into tuples |
| `scarfolder.generators.util.Enumerate` | Pair each item with its index |

### Transformers

All built-in text transformers operate on `list[str]`. When chained to a generator, `values` is auto-injected; when used standalone, declare `values: ${steps.<id>}` in args.

| Path | Description |
|---|---|
| `scarfolder.transformers.text.capitalize_first` | Capitalise first letter of each string |
| `scarfolder.transformers.text.upper` | Upper-case every string |
| `scarfolder.transformers.text.lower` | Lower-case every string |
| `scarfolder.transformers.text.strip` | Strip leading/trailing whitespace |
| `scarfolder.transformers.text.join` | Join each inner sequence into a string |
| `scarfolder.transformers.text.prefix` | Prepend a fixed string |
| `scarfolder.transformers.text.suffix` | Append a fixed string |
| `scarfolder.transformers.text.format_template` | Apply `{value}` format template |

### Loaders

When chained to a step, `values` is auto-injected; when used standalone, declare `values: ${steps.<id>}` in args.

| Path | Description |
|---|---|
| `scarfolder.loaders.file.WriteLines` | Write one value per line to a text file |
| `scarfolder.loaders.file.WriteJson` | Serialise values as a JSON array |
| `scarfolder.loaders.console.Print` | Print values to stdout with optional template/header/footer |
| `scarfolder.loaders.file.print_values` | Print values to stdout (simple function) |
| `scarfolder.loaders.sql.ExecuteStatements` | Execute each value as a raw SQL statement |
| `scarfolder.loaders.sql.ExecuteMany` | Execute a parameterised query for each row |

---

## Writing Custom Plugins

Any Python class or plain callable can be a plugin — reference it by its fully qualified dotted path.

### Class-based (recommended for stateful plugins)

All data arrives through the constructor. Action methods take no positional arguments.

```python
# my_project/generators.py
from scarfolder.core.base import Generator

class Name(Generator):
    def __init__(self, language: str = "en", count: int = 5):
        self.pool = ["Alice", "Bob"] if language == "en" else ["Luca", "Sofia"]
        self.count = count

    def generate(self) -> list[str]:
        import random
        return [random.choice(self.pool) for _ in range(self.count)]
```

```python
# my_project/loaders.py
import csv
from pathlib import Path
from scarfolder.core.base import Loader

class WriteCsv(Loader):
    def __init__(self, values: list, path: str, headers: list[str] | None = None):
        self.values = values   # auto-injected when chained; explicit via ${steps.*} otherwise
        self.path = Path(path)
        self.headers = headers

    def load(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("w", newline="") as f:
            writer = csv.writer(f)
            if self.headers:
                writer.writerow(self.headers)
            writer.writerows([[v] for v in self.values])
```

### Function-based (simpler for stateless transforms)

All resolved args are passed as keyword arguments. The data input is just another named keyword argument.

```python
# my_project/transforms.py

def shout(values: list[str], mark: str = "!") -> list[str]:
    return [v.upper() + mark for v in values]
```

### Referencing in YAML

```yaml
steps:
  - id: names
    generator:
      name: my_project.generators.Name
      args:
        language: it
        count: 20
    transformer:                          # chained — values auto-injected
      name: my_project.transforms.shout
      args:
        mark: "!!!"
    loader:                               # chained — values auto-injected
      name: my_project.loaders.WriteCsv
      args:
        path: output/names.csv
        headers: [name]
```

Make sure your project directory is on `PYTHONPATH`:

```bash
PYTHONPATH=. scarfolder run pipeline.yaml
```

---

## Running with Docker

A pre-built image is available. Mount your project to `/workspace` — that directory is automatically on `PYTHONPATH`, so your custom plugins are importable with no extra setup.

### One-off run

```bash
docker run --rm \
  -v ./my_project:/workspace \
  ghcr.io/freshmag/scarfolder:latest \
  run scarf.yaml -planguage=it
```

### With Docker Compose

```yaml
# docker-compose.yml
services:
  scarfolder:
    image: ghcr.io/freshmag/scarfolder:latest
    volumes:
      - .:/workspace
    command: ["run", "scarf.yaml", "-planguage=it"]
```

```bash
docker compose run --rm scarfolder
```

### Plugins outside the project directory

Use `SCARFOLDER_PLUGINS_PATH` (colon-separated) to inject additional paths:

```bash
docker run --rm \
  -v ./my_project:/workspace \
  -v ./shared_plugins:/plugins \
  -e SCARFOLDER_PLUGINS_PATH=/plugins \
  ghcr.io/freshmag/scarfolder:latest \
  run scarf.yaml
```

---

<div align="center">
  <sub>Made with ❤️ and a warm scarf.</sub>
</div>
