---
id: cli
title: CLI Reference
sidebar_position: 4
---

# CLI Reference

```
scarfolder [OPTIONS] COMMAND [ARGS]
```

## `run`

Execute a pipeline.

```bash
scarfolder run SCARF_FILE [OPTIONS]
```

| Option | Description |
|---|---|
| `-p`, `--param KEY=VALUE` | Override or supply a config arg. Repeatable. |
| `--dry-run` | Validate config without executing any steps. |

### Examples

```bash
# Basic run
scarfolder run pipeline.yaml

# Override multiple args
scarfolder run pipeline.yaml -planguage=it -pcount=50 -poutput=result.txt

# Validate without running
scarfolder run pipeline.yaml --dry-run
```

If a required arg (declared with a `null` default) is not supplied via `-p`, the CLI prompts for it interactively:

```
Required argument 'output': _
```

## `validate`

Parse and validate a Scarf file without running it. Reports config errors, unknown step references, and type errors.

```bash
scarfolder validate SCARF_FILE
```

## `list-steps`

Print a summary of all steps and their plugin chains.

```bash
scarfolder list-steps SCARF_FILE
```

Each step is displayed as a chain of its plugins, labelled by role:

```
Scarf: hello-world

  1. [first_names]  [G] scarfolder.generators.util.Constant
  2. [last_names]   [G] scarfolder.generators.util.Constant
  3. [(unnamed)]    [G] scarfolder.generators.util.Combine → [T] text.join → [T] text.format_template → [L] file.WriteLines
```

Labels: `[G]` = Generator, `[T]` = Transformer, `[L]` = Loader.
