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


class MultipleResourcesFoundError(AgrError):
    """Raised when a resource name exists in multiple resource types."""


class ConfigNotFoundError(AgrError):
    """Raised when agr.toml is required but not found."""


class ConfigParseError(AgrError):
    """Raised when agr.toml contains invalid TOML syntax."""


class NoGitRemoteError(AgrError):
    """Raised when no git remote is found for namespace resolution."""


class InvalidLocalPathError(AgrError):
    """Raised when a local resource path is invalid or doesn't exist."""


class ResourceTypeDetectionError(AgrError):
    """Raised when resource type cannot be detected from path."""
