---
id: custom-plugins
title: Custom Plugins
sidebar_position: 6
---

# Custom Plugins

Any Python class or plain callable can be a plugin — reference it by its fully qualified dotted path.

## Plugin contract

All data flows through the constructor via the resolved `args` block. The action methods (`generate`, `transform`, `load`) take no positional arguments.

When a transformer or loader is **chained** to a step (i.e. declared on the same step as a generator or as a subsequent transformer), the pipeline automatically injects the previous output as `values`. When used as a **standalone** step, you declare `values` explicitly in `args` using a `${steps.<id>}` placeholder.

## Class-based plugins

Subclass the appropriate base class from `scarfolder.core.base`.

### Generator

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

A generator can also accept another step's output as an arg. Here `seed_names` comes from a previous step:

```python
class FilteredName(Generator):
    def __init__(self, seed_names: list[str], prefix: str = ""):
        self.seed_names = seed_names   # e.g. from ${steps.name_pool}
        self.prefix = prefix

    def generate(self) -> list[str]:
        return [self.prefix + n for n in self.seed_names if len(n) > 3]
```

```yaml
- id: filtered
  generator:
    name: my_project.generators.FilteredName
    args:
      seed_names: ${steps.name_pool}
      prefix: "Dr. "
```

### Transformer

```python
# my_project/transformers.py
from scarfolder.core.base import Transformer

class AddSuffix(Transformer):
    def __init__(self, values: list[str], suffix: str = ""):
        self.values = values   # auto-injected when chained; explicit otherwise
        self.suffix = suffix

    def transform(self) -> list[str]:
        return [v + self.suffix for v in self.values]
```

### Loader

```python
# my_project/loaders.py
import csv
from pathlib import Path
from scarfolder.core.base import Loader

class WriteCsv(Loader):
    def __init__(self, values: list, path: str, headers: list[str] | None = None):
        self.values = values   # auto-injected when chained; explicit otherwise
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

## Function-based plugins

Plain callables work too — useful for stateless transformations.

All resolved args are passed as keyword arguments. The input data is just another named keyword argument.

```python
# my_project/transforms.py

def shout(values: list[str], mark: str = "!") -> list[str]:
    return [v.upper() + mark for v in values]
```

```python
# my_project/loaders.py

def write_report(values: list, path: str) -> None:
    with open(path, "w") as f:
        for item in values:
            f.write(str(item) + "\n")
```

## Referencing plugins in YAML

```yaml
steps:
  - id: names
    generator:
      name: my_project.generators.Name
      args:
        language: it
        count: 20
    transformer:                        # chained — values auto-injected
      name: my_project.transforms.shout
      args:
        mark: "!!!"

  - loader:                             # standalone — values explicit
      name: my_project.loaders.WriteCsv
      args:
        values: ${steps.names}
        path: output/names.csv
        headers: [name]
```

## Making your plugins importable

Your project directory must be on `PYTHONPATH`:

```bash
PYTHONPATH=. scarfolder run pipeline.yaml
```

Or install your package in editable mode alongside Scarfolder:

```bash
pip install -e .
scarfolder run pipeline.yaml
```

When using Docker, mount your project to `/workspace` — that path is automatically added to `PYTHONPATH` by the container entrypoint:

```bash
docker run --rm -v ./my_project:/workspace scarfolder:latest run scarf.yaml
```

## Error handling

Scarfolder wraps plugin errors in typed exceptions:

| Exception | When raised |
|---|---|
| `PluginError` | Import fails, instantiation fails, or the dotted path is invalid |
| `StepExecutionError` | An unexpected error occurs during `generate()`, `transform()`, or `load()` |
| `ResolutionError` | A placeholder cannot be resolved (missing key, wrong type, unknown namespace) |
| `CircularDependencyError` | A cycle is detected in `${steps.*}` references |
| `ConfigError` | The YAML file is invalid or cannot be parsed |
