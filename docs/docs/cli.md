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
| `--dry-run` | Validate config and resolve placeholders without executing any steps. |

### Examples

```bash
# Basic run
scarfolder run pipeline.yaml

# Override multiple args
scarfolder run pipeline.yaml -planguage=it -pcount=50 -poutput=result.txt

# Validate without running
scarfolder run pipeline.yaml --dry-run
```

If a required arg (declared with `null` default) is not supplied via `-p`, the CLI will prompt for it interactively:

```
Required argument 'output': _
```

## `validate`

Parse and validate a Scarf file without running it. Reports config errors, unknown step references, and type errors.

```bash
scarfolder validate SCARF_FILE
```

## `list-steps`

Print a summary of all steps and their plugins.

```bash
scarfolder list-steps SCARF_FILE
```
