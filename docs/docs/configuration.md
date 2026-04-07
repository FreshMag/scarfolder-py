---
id: configuration
title: Configuration
sidebar_position: 3
---

# Configuration

A Scarf file is a plain YAML document with a defined structure.

## Full schema

```yaml
name: my-pipeline          # required — human-readable name
description: optional text

# External YAML files. Each key becomes a namespace accessible via ${key.*}.
refs:
  queries: ./sql/queries.yaml

# Default argument values.
# null marks a required arg that must be supplied at runtime.
args:
  language: en
  count: 10
  output: null             # required — CLI will prompt if not given via -p

steps:
  - id: step-name          # optional; required if referenced by other steps
    generator:
      name: dotted.path.ClassName
      args:
        language: ${args.language}
        count: ${args.count}
    transformer:            # chained after generator; values auto-injected
      name: dotted.path.fn
      args:
        extra_arg: value
    loader:                 # runs after transformer; values auto-injected
      name: dotted.path.Loader
      args:
        path: ${args.output}
```

## Step structure

Each step must declare at least one of `generator`, `transformer` / `transformers`, or `loader` / `loaders`.

### Generator only

Produces values and stores them under the step's `id`. No side effects.

```yaml
- id: names
  generator:
    name: scarfolder.generators.util.Constant
    args:
      value: Alice
      count: 5
```

### Generator + transformer(s)

The transformer runs immediately after the generator. The pipeline automatically injects the generator's output as `values` — you do not need an explicit `${steps.*}` reference.

```yaml
- id: names
  generator:
    name: scarfolder.generators.util.Constant
    args:
      value: alice
      count: 5
  transformer: scarfolder.transformers.text.capitalize_first
```

Use `transformers` (or a YAML list under `transformer`) to chain multiple transformers in sequence. Each one receives the output of the previous:

```yaml
- id: greetings
  generator:
    name: scarfolder.generators.util.Constant
    args:
      value: hello world
      count: 3
  transformers:
    - name: scarfolder.transformers.text.capitalize_first
    - name: scarfolder.transformers.text.format_template
      args:
        template: "→ {value}"
```

### Standalone transformer

When there is no generator, the transformer is the primary producer and must supply all its inputs explicitly through `args`:

```yaml
- id: upper_names
  transformer:
    name: scarfolder.transformers.text.upper
    args:
      values: ${steps.names}
```

### Generator + loader

Attach a `loader` (or `loaders` list) to consume the step's output as a side effect. Values are auto-injected — `path` and any other loader-specific args are still declared explicitly:

```yaml
- generator:
    name: scarfolder.generators.util.Range
    args:
      stop: 10
  loader:
    name: scarfolder.loaders.file.WriteLines
    args:
      path: output.txt
```

Fan out to multiple loaders by using a list:

```yaml
- generator:
    name: scarfolder.generators.util.Constant
    args:
      value: hello
      count: 3
  loaders:
    - name: scarfolder.loaders.console.Print
    - name: scarfolder.loaders.file.WriteLines
      args:
        path: out.txt
```

### Standalone loader

A loader-only step receives its data explicitly through `args`:

```yaml
- loader:
    name: scarfolder.loaders.console.Print
    args:
      values: ${steps.greetings}
```

## Plugin short form

When a plugin has no extra args, write it as a plain string:

```yaml
# verbose
transformer:
  name: scarfolder.transformers.text.upper
  args: {}

# short form — identical behaviour
transformer: scarfolder.transformers.text.upper
```

## Args and placeholders

### Declaring args

```yaml
args:
  language: en    # has a default
  count: 10       # has a default
  output: null    # required — must be supplied via -p or interactive prompt
```

### Supplying args at runtime

```bash
scarfolder run pipeline.yaml -planguage=it -pcount=50 -poutput=result.txt
```

### Placeholder syntax

```yaml
args:
  path: ${args.output}          # from config defaults or CLI
  values: ${steps.names}        # output list of a previous step
  query: ${queries.insert_user} # key from an external ref file
  count: ${count}               # shorthand for ${args.count}
  token: ${env.API_TOKEN}       # OS environment variable
```

**Type preservation:** if the entire value is a single placeholder, the resolved Python object is used directly — not its string representation. This is essential for passing lists between steps:

```yaml
args:
  values: ${steps.names}   # receives the actual list, not its string form
```

If the placeholder is embedded inside a string, the result is always a string:

```yaml
args:
  message: "Hello ${args.name}!"   # always a string
```

## External refs

Load external YAML files and reference their contents anywhere in the config:

```yaml
refs:
  queries: ./sql/queries.yaml

steps:
  - generator:
      name: my_pkg.generators.SqlRows
      args:
        query: ${queries.select_users}
```

`queries.yaml`:

```yaml
select_users: "SELECT id, name FROM users"
insert_user:  "INSERT INTO users (name) VALUES (?)"
```

Ref files are loaded relative to the Scarf file's directory.

## Step dependencies

Steps are automatically sorted in topological order. Any `${steps.*}` reference anywhere in a step's args — including inside chained transformers and loaders — is picked up as a dependency. Declaration order in the file does not matter:

```yaml
steps:
  - id: full_names
    generator:
      name: scarfolder.generators.util.Combine
      args:
        streams:
          - ${steps.first_names}   # declared below — still fine
          - ${steps.last_names}
    transformer: scarfolder.transformers.text.join

  - id: first_names
    generator:
      name: scarfolder.generators.util.Constant
      args: { value: Alice, count: 3 }

  - id: last_names
    generator:
      name: scarfolder.generators.util.Constant
      args: { value: Smith, count: 3 }
```
