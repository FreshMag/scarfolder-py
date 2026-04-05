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
      name: dotted.path.ClassName   # or a plain function path
      args:
        key: value
        ref_key: ${args.language}   # placeholder
    transformer:            # optional
      name: dotted.path.fn
      args: {}
    loader:                 # optional
      name: dotted.path.Loader
      args:
        path: ${args.output}
```

## Plugin short form

When a plugin has no args, you can write it as a plain string instead of a mapping:

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
  data: ${steps.names}          # output list of a previous step
  query: ${queries.insert_user} # key from an external ref file
  count: ${count}               # shorthand for ${args.count}
```

**Type preservation rule:** if the *entire* value is a single placeholder expression, the resolved Python object is used directly — not its string representation. This is essential for passing lists between steps:

```yaml
args:
  stream: ${steps.names}   # receives the actual list, not "[\"Alice\", ...]"
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

Steps are automatically sorted in topological order. You can reference any earlier step's output regardless of where it appears in the file:

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
