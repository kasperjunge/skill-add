"""Shared exception classes for agr."""


class AgrError(Exception):
    """Base exception for agr errors."""


class RepoNotFoundError(AgrError):
    """Raised when the GitHub repo doesn't exist."""


class ResourceNotFoundError(AgrError):
    """Raised when the skill/command/agent doesn't exist in the repo."""


class ResourceExistsError(AgrError):
    """Raised when the resource already exists locally."""


class BundleNotFoundError(AgrError):
    """Raised when no bundle directory exists in any resource type."""


class ConfigNotFoundError(AgrError):
    """Raised when agr.toml is not found."""


class ConfigParseError(AgrError):
    """Raised when agr.toml cannot be parsed."""


class ConfigValidationError(AgrError):
    """Raised when agr.toml contains invalid configuration."""


class TypeDetectionError(AgrError):
    """Raised when resource type cannot be detected from path."""
