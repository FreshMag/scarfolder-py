"""YAML loading, normalisation, and ref resolution."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from scarfolder.config.schema import ScarConfig
from scarfolder.exceptions import ConfigError


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data or {}
    except yaml.YAMLError as exc:
        raise ConfigError(f"YAML parse error in '{path}': {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Cannot read '{path}': {exc}") from exc


def _load_refs(config_dir: Path, refs_spec: dict[str, str]) -> dict[str, Any]:
    """Load each file listed in the ``refs`` section and return their contents."""
    result: dict[str, Any] = {}
    for name, rel_path in refs_spec.items():
        abs_path = config_dir / rel_path
        result[name] = _load_yaml(abs_path)
    return result


def load_scarf(
    scarf_path: Path,
    cli_args: dict[str, Any],
) -> tuple[ScarConfig, dict[str, Any], dict[str, Any]]:
    """Parse a scarf YAML file and merge CLI arguments.

    Parameters
    ----------
    scarf_path:
        Path to the ``.yaml`` scarf file.
    cli_args:
        Arguments supplied via ``-p KEY=VALUE`` on the command line.

    Returns
    -------
    config:
        Validated :class:`~scarfolder.config.schema.ScarConfig` model.
    merged_args:
        Config defaults overridden by *cli_args*.  Required args (those
        with ``null`` defaults) that are still missing must be prompted for
        by the caller.
    refs:
        Dict mapping each ref name to its loaded YAML content.
    """
    raw = _load_yaml(scarf_path)

    try:
        config = ScarConfig(**raw)
    except Exception as exc:
        raise ConfigError(
            f"Invalid scarf configuration in '{scarf_path}': {exc}"
        ) from exc

    merged_args: dict[str, Any] = {**config.args, **cli_args}
    refs = _load_refs(scarf_path.parent, config.refs)

    return config, merged_args, refs
