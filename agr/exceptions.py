"""Custom exceptions for agr."""


class AgrError(Exception):
    """Base exception for agr errors."""


class RepoNotFoundError(AgrError):
    """Raised when the GitHub repo doesn't exist."""


class AuthenticationError(AgrError):
    """Raised when GitHub authentication fails (401/403)."""


class SkillNotFoundError(AgrError):
    """Raised when the skill doesn't exist in the repo."""


class ConfigError(AgrError):
    """Raised when agr.toml has issues (not found or invalid)."""


class InvalidHandleError(AgrError):
    """Raised when a handle cannot be parsed."""


class InvalidLocalPathError(AgrError):
    """Raised when a local skill path is invalid."""
