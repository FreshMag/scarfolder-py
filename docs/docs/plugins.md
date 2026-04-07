---
id: plugins
title: Built-in Plugins
sidebar_position: 5
---

# Built-in Plugins

## Generators

Generators produce a list of values. Their constructor receives all configuration through `args`. Any argument may reference a previous step's output via `${steps.<id>}`, making generators composable without any special syntax.

---

### `scarfolder.generators.util.Range`

Generates a sequence of integers, analogous to Python's `range()`.

| Arg | Type | Default | Description |
|---|---|---|---|
| `start` | int | `0` | First value |
| `stop` | int | `10` | Upper bound (exclusive) |
| `step` | int | `1` | Increment |

```yaml
- id: numbers
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

Repeats a single value exactly `count` times.

| Arg | Type | Default | Description |
|---|---|---|---|
| `value` | any | — | The value to repeat |
| `count` | int | `1` | How many copies |

```yaml
- id: words
  generator:
    name: scarfolder.generators.util.Constant
    args:
      value: hello
      count: 3
# → ["hello", "hello", "hello"]
```

---

### `scarfolder.generators.util.Combine`

Zips multiple streams into tuples (shortest wins, like Python's `zip()`). Each stream is typically a previous step's output passed as an arg.

| Arg | Type | Description |
|---|---|---|
| `streams` | list of lists | The streams to zip together |

```yaml
- id: pairs
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

Pairs each item with its index, like Python's `enumerate()`.

| Arg | Type | Default | Description |
|---|---|---|---|
| `stream` | list | — | Input list, e.g. `${steps.names}` |
| `start` | int | `0` | Starting index |

```yaml
- id: indexed
  generator:
    name: scarfolder.generators.util.Enumerate
    args:
      stream: ${steps.names}
      start: 1
# → [(1, "Alice"), (2, "Bob"), ...]
```

---

## Transformers

Transformers receive a list and return a new list. When used as inline chain steps (attached to a generator), `values` is injected automatically. When used as standalone steps, `values` must be declared explicitly in `args`.

All built-in text transformers operate on `list[str]`.

---

### `scarfolder.transformers.text.capitalize_first`

Capitalises the first letter of each string.

```yaml
# Inline — values auto-injected
- id: names
  generator:
    name: scarfolder.generators.util.Constant
    args: { value: alice, count: 3 }
  transformer: scarfolder.transformers.text.capitalize_first
# → ["Alice", "Alice", "Alice"]

# Standalone — values explicit
- id: names
  transformer:
    name: scarfolder.transformers.text.capitalize_first
    args:
      values: ${steps.raw_names}
```

---

### `scarfolder.transformers.text.upper` / `lower`

Converts each string to upper- or lower-case.

```yaml
transformer: scarfolder.transformers.text.upper
transformer: scarfolder.transformers.text.lower
```

---

### `scarfolder.transformers.text.strip`

Strips leading/trailing whitespace (or a custom set of characters).

| Arg | Type | Default | Description |
|---|---|---|---|
| `chars` | str | `null` | Characters to strip; `null` strips whitespace |

---

### `scarfolder.transformers.text.join`

Joins each inner sequence into a single string. Typically used after `Combine` or `Enumerate`.

| Arg | Type | Default | Description |
|---|---|---|---|
| `separator` | str | `" "` | String placed between parts |

```yaml
- id: full_names
  generator:
    name: scarfolder.generators.util.Combine
    args:
      streams:
        - ${steps.first_names}
        - ${steps.last_names}
  transformer: scarfolder.transformers.text.join
# [("Alice", "Smith"), ("Bob", "Jones")] → ["Alice Smith", "Bob Jones"]
```

---

### `scarfolder.transformers.text.prefix` / `suffix`

Prepends or appends a fixed string to every value.

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

Applies a Python format-string template to each value. The value is exposed as `{value}`.

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

---

## Loaders

Loaders consume a list as a terminal side effect and return nothing. When attached to a step with a generator or transformer chain, `values` is injected automatically. When used standalone, `values` must be declared explicitly in `args`.

---

### `scarfolder.loaders.file.WriteLines`

Writes each value as a line to a text file.

| Arg | Type | Default | Description |
|---|---|---|---|
| `values` | list | — | The sequence to write (auto-injected when chained) |
| `path` | str | — | Destination file path |
| `mode` | str | `"w"` | `"w"` to overwrite, `"a"` to append |
| `encoding` | str | `"utf-8"` | File encoding |

```yaml
- generator:
    name: scarfolder.generators.util.Constant
    args: { value: hello, count: 3 }
  loader:
    name: scarfolder.loaders.file.WriteLines
    args:
      path: output.txt
```

---

### `scarfolder.loaders.file.WriteJson`

Serialises values as a JSON array to a file.

| Arg | Type | Default | Description |
|---|---|---|---|
| `values` | list | — | The sequence to serialise (auto-injected when chained) |
| `path` | str | — | Destination file path |
| `indent` | int or null | `2` | Pretty-print indent; `null` for compact output |
| `encoding` | str | `"utf-8"` | File encoding |

---

### `scarfolder.loaders.console.Print`

Prints each value to stdout. Useful for debugging.

| Arg | Type | Default | Description |
|---|---|---|---|
| `values` | list | — | The sequence to print (auto-injected when chained) |
| `template` | str | `"{value}"` | Format string; `{index}` is also available |
| `separator` | str | `"\n"` | String printed between items |
| `header` | str | `null` | Line printed once before all values |
| `footer` | str | `null` | Line printed once after all values |

```yaml
- generator:
    name: scarfolder.generators.util.Range
    args: { stop: 5 }
  loader:
    name: scarfolder.loaders.console.Print
    args:
      header: "--- items ---"
      template: "  {index}. {value}"
```

---

### `scarfolder.loaders.file.print_values`

Function-based convenience loader that prints each value to stdout. Takes only `values`.

```yaml
loader: scarfolder.loaders.file.print_values
```

---

### SQL loaders

Requires SQLAlchemy: `pip install scarfolder[sql]`

#### `scarfolder.loaders.sql.ExecuteStatements`

Executes each value as a raw SQL statement.

| Arg | Type | Default | Description |
|---|---|---|---|
| `values` | list | — | SQL strings to execute (auto-injected when chained) |
| `url` | str | — | SQLAlchemy connection URL |
| `echo` | bool | `false` | Log every executed statement |
| `stop_on_error` | bool | `true` | Abort on first failure |

#### `scarfolder.loaders.sql.ExecuteMany`

Executes one parameterised SQL statement per row.

| Arg | Type | Default | Description |
|---|---|---|---|
| `values` | list | — | Rows to insert (auto-injected when chained) |
| `url` | str | — | SQLAlchemy connection URL |
| `query` | str | — | Parameterised SQL with `:name` placeholders |
| `mapping` | list of str | `null` | Maps positional tuple/list elements to parameter names |
| `echo` | bool | `false` | Log every executed statement |

```yaml
- loader:
    name: scarfolder.loaders.sql.ExecuteMany
    args:
      values: ${steps.name_rows}
      url: postgresql+psycopg2://user:${env.DB_PASSWORD}@localhost/mydb
      query: "INSERT INTO people (first, last) VALUES (:first, :last)"
      mapping: [first, last]
```
