---
id: custom-plugins
title: Custom Plugins
sidebar_position: 6
---

# Custom Plugins

Any Python class or plain callable can be a plugin — reference it by its fully qualified dotted path.

## Class-based plugins

Subclass the appropriate base class from `scarfolder.core.base`. Constructor arguments come directly from the `args` block in YAML.

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

### Transformer

```python
# my_project/transformers.py
from scarfolder.core.base import Transformer

class AddSuffix(Transformer):
    def __init__(self, suffix: str = ""):
        self.suffix = suffix

    def transform(self, values: list[str]) -> list[str]:
        return [v + self.suffix for v in values]
```

### Loader

```python
# my_project/loaders.py
from pathlib import Path
from scarfolder.core.base import Loader

class WriteLines(Loader):
    def __init__(self, path: str):
        self.path = Path(path)

    def load(self, values: list) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("\n".join(map(str, values)))
```

## Function-based plugins

Plain callables work too — useful for stateless transformations.

- **Generator function:** `fn(**kwargs) -> Iterable`
- **Transformer function:** `fn(values, **kwargs) -> Iterable`
- **Loader function:** `fn(values, **kwargs) -> None`

```python
# my_project/transforms.py

def shout(values: list[str], mark: str = "!") -> list[str]:
    return [v.upper() + mark for v in values]
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
    transformer:
      name: my_project.transforms.shout
      args:
        mark: "!!!"
    loader:
      name: my_project.loaders.WriteLines
      args:
        path: output/names.txt
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
