"""Custom exceptions for Scarfolder."""


class ScarfolderError(Exception):
    """Base exception for all Scarfolder errors."""


class ConfigError(ScarfolderError):
    """Raised when a configuration file is invalid or cannot be loaded."""


class PluginError(ScarfolderError):
    """Raised when a plugin (generator / transformer / loader) cannot be
    imported, instantiated, or called."""


class ResolutionError(ScarfolderError):
    """Raised when a placeholder cannot be resolved (missing key, wrong type,
    unknown namespace, etc.)."""


class StepExecutionError(ScarfolderError):
    """Raised when a step fails during pipeline execution."""


class CircularDependencyError(ScarfolderError):
    """Raised when circular dependencies are detected between steps."""
