"""Tests for version consistency across package files."""

from pathlib import Path

import tomlkit


def test_version_matches_pyproject():
    """Verify that agr.__version__ matches the version in pyproject.toml."""
    from agr import __version__

    # Read pyproject.toml
    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    with open(pyproject_path) as f:
        pyproject = tomlkit.load(f)

    expected_version = pyproject["project"]["version"]

    assert __version__ == expected_version, (
        f"Version mismatch: agr.__version__={__version__!r}, "
        f"pyproject.toml version={expected_version!r}"
    )
