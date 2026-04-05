---
id: plugins
title: Built-in Plugins
sidebar_position: 5
---

# Built-in Plugins

## Generators

### `scarfolder.generators.util.Range`

Generate a sequence of integers, analogous to Python's `range()`.

| Arg | Type | Default | Description |
|---|---|---|---|
| `start` | int | `0` | First value |
| `stop` | int | `10` | Upper bound (exclusive) |
| `step` | int | `1` | Increment |

```yaml
generator:
  name: scarfolder.generators.util.Range
  args:
    start: 1
    stop: 11
    step: 2
# → [1, 3, 5, 7, 9]
```

---

### `scarfolder.generators.util.Constant`

Repeat a single value exactly `count` times.

| Arg | Type | Default | Description |
|---|---|---|---|
| `value` | any | — | The value to repeat |
| `count` | int | `1` | How many copies |

```yaml
generator:
  name: scarfolder.generators.util.Constant
  args:
    value: hello
    count: 3
# → ["hello", "hello", "hello"]
```

---

### `scarfolder.generators.util.From`

Pass a previous step's output through unchanged. Useful when you want to apply a transformer or loader to an existing step without re-generating data.

| Arg | Type | Description |
|---|---|---|
| `stream` | list | A step output, e.g. `${steps.names}` |

```yaml
generator:
  name: scarfolder.generators.util.From
  args:
    stream: ${steps.full_names}
loader: my_pkg.loaders.WriteLines
```

---

### `scarfolder.generators.util.Combine`

Zip multiple streams into tuples (shortest wins, same as `zip()`).

| Arg | Type | Description |
|---|---|---|
| `streams` | list of lists | The streams to zip |

```yaml
generator:
  name: scarfolder.generators.util.Combine
  args:
    streams:
      - ${steps.first_names}
      - ${steps.last_names}
# → [("Alice", "Smith"), ("Bob", "Jones"), ...]
```

---

### `scarfolder.generators.util.Enumerate`

Pair each item with its index, like Python's `enumerate()`.

| Arg | Type | Default | Description |
|---|---|---|---|
| `stream` | list | — | Input list |
| `start` | int | `0` | Starting index |

```yaml
generator:
  name: scarfolder.generators.util.Enumerate
  args:
    stream: ${steps.names}
    start: 1
# → [(1, "Alice"), (2, "Bob"), ...]
```

---

## Transformers

All text transformers operate on `list[str]`.

### `scarfolder.transformers.text.capitalize_first`

Capitalise the first letter of each string.

```yaml
transformer: scarfolder.transformers.text.capitalize_first
```

---

### `scarfolder.transformers.text.upper` / `lower`

Convert each string to upper- or lower-case.

```yaml
transformer: scarfolder.transformers.text.upper
```

---

### `scarfolder.transformers.text.strip`

Strip leading/trailing whitespace (or a custom set of characters).

| Arg | Type | Default | Description |
|---|---|---|---|
| `chars` | str | `None` | Characters to strip; `None` strips whitespace |

---

### `scarfolder.transformers.text.join`

Join each inner sequence into a single string. Used after `Combine` or `Enumerate`.

| Arg | Type | Default | Description |
|---|---|---|---|
| `separator` | str | `" "` | String placed between parts |

```yaml
transformer:
  name: scarfolder.transformers.text.join
  args:
    separator: " "
# [("Alice", "Smith"), ("Bob", "Jones")] → ["Alice Smith", "Bob Jones"]
```

---

### `scarfolder.transformers.text.prefix` / `suffix`

Prepend or append a fixed string to every value.

| Arg | Type | Default | Description |
|---|---|---|---|
| `text` | str | `""` | The string to prepend/append |

```yaml
transformer:
  name: scarfolder.transformers.text.prefix
  args:
    text: "user_"
```

---

### `scarfolder.transformers.text.format_template`

Apply a Python format-string template to each value. The value is exposed as `{value}`.

| Arg | Type | Default | Description |
|---|---|---|---|
| `template` | str | `"{value}"` | Format string |

```yaml
transformer:
  name: scarfolder.transformers.text.format_template
  args:
    template: "Hello, {value}!"
# ["Alice", "Bob"] → ["Hello, Alice!", "Hello, Bob!"]
```
