"""Command-line interface for Scarfolder."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Plugin path injection — runs at import time, before any user module is loaded.
#
# SCARFOLDER_PLUGINS_PATH mirrors the PYTHONPATH convention: a colon-separated
# (semicolon on Windows) list of directories to prepend to sys.path.
# When running in Docker, /workspace is already on PYTHONPATH via the image ENV;
# this env var is the escape hatch for extra directories.
# ---------------------------------------------------------------------------
_extra = os.environ.get("SCARFOLDER_PLUGINS_PATH", "")
_sep = ";" if sys.platform == "win32" else ":"
for _dir in reversed([p.strip() for p in _extra.split(_sep) if p.strip()]):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

import click

from scarfolder.config.loader import load_scarf
from scarfolder.core.pipeline import Pipeline
from scarfolder.exceptions import ScarfolderError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_param(raw: str) -> tuple[str, str]:
    """Parse ``KEY=VALUE`` into ``(key, value)``."""
    if "=" not in raw:
        raise click.BadParameter(
            f"Expected KEY=VALUE format, got: {raw!r}",
            param_hint="'-p'",
        )
    key, _, value = raw.partition("=")
    return key.strip(), value.strip()


def _prompt_missing(config_args: dict[str, Any], provided: dict[str, Any]) -> dict[str, Any]:
    """Interactively prompt for required args (those with a ``null`` default)
    that were not supplied via CLI.
    """
    missing = sorted(
        k for k, v in config_args.items() if v is None and k not in provided
    )
    extra: dict[str, Any] = {}
    for key in missing:
        extra[key] = click.prompt(f"  Required argument '{key}'")
    return {**provided, **extra}


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(package_name="scarfolder")
def main() -> None:
    """Scarfolder — data and file scaffolding via YAML pipelines."""


# ---------------------------------------------------------------------------
# `run` command
# ---------------------------------------------------------------------------

@main.command("run")
@click.argument("scarf_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-p",
    "--param",
    "params",
    multiple=True,
    metavar="KEY=VALUE",
    help="Inject a runtime parameter.  May be repeated: -pLANG=it -pCOUNT=50",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Validate the scarf config without executing any steps.",
)
def run_command(scarf_file: Path, params: tuple[str, ...], dry_run: bool) -> None:
    """Run the pipeline defined in SCARF_FILE.

    Runtime parameters override config defaults:

    \b
        scarfolder run people.yaml -pLANGUAGE=it -pCOUNT=100
    """
    cli_args: dict[str, Any] = {}
    for p in params:
        k, v = _parse_param(p)
        cli_args[k] = v

    try:
        config, merged_args, refs = load_scarf(scarf_file, cli_args)
        final_args = _prompt_missing(config.args, merged_args)

        if dry_run:
            click.echo(
                f"[dry-run] '{config.name}' — {len(config.steps)} step(s), config valid."
            )
            return

        click.echo(f"Running '{config.name}'…")
        Pipeline(config, final_args, refs).run()
        click.echo("Done.")

    except ScarfolderError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# `validate` command
# ---------------------------------------------------------------------------

@main.command("validate")
@click.argument("scarf_file", type=click.Path(exists=True, path_type=Path))
def validate_command(scarf_file: Path) -> None:
    """Validate a Scarf YAML file without running it."""
    try:
        config, _, _ = load_scarf(scarf_file, {})
        click.echo(f"OK  '{config.name}' — {len(config.steps)} step(s).")
    except ScarfolderError as exc:
        click.echo(f"Invalid: {exc}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# `list-steps` command
# ---------------------------------------------------------------------------

@main.command("list-steps")
@click.argument("scarf_file", type=click.Path(exists=True, path_type=Path))
def list_steps_command(scarf_file: Path) -> None:
    """Print a summary of all steps in a Scarf file."""
    try:
        config, _, _ = load_scarf(scarf_file, {})
        click.echo(f"Scarf: {config.name}")
        if config.description:
            click.echo(f"       {config.description}")
        click.echo()
        for i, step in enumerate(config.steps, 1):
            label = step.id or "(unnamed)"
            gen = step.generator.name
            tr = f"  → {step.transformer.name}" if step.transformer else ""
            ld = f"  ⇒ {step.loader.name}" if step.loader else ""
            click.echo(f"  {i}. [{label}]  {gen}{tr}{ld}")
    except ScarfolderError as exc:
        click.echo(f"Error: {exc}", err=True)
        sys.exit(1)
