"""Fixtures for CLI tests."""

import shutil
import subprocess
from pathlib import Path

import pytest

from tests.cli.runner import run_cli


def pytest_configure(config):
    """Register CLI test markers."""
    config.addinivalue_line(
        "markers", "requires_cli(name): skip test if CLI tool is not installed"
    )
    config.addinivalue_line(
        "markers",
        "network: marks tests as requiring network access (deselect with '-m \"not network\"')",
    )


def pytest_runtest_setup(item):
    """Skip tests that require unavailable CLI tools."""
    for marker in item.iter_markers(name="requires_cli"):
        cli_name = marker.args[0]
        if shutil.which(cli_name) is None:
            pytest.skip(f"Test requires '{cli_name}' CLI which is not installed")


@pytest.fixture
def cli_project(tmp_path: Path) -> Path:
    """Create a temporary git project directory."""
    project = tmp_path / "project"
    project.mkdir()

    # Initialize as git repo
    subprocess.run(["git", "init"], cwd=project, capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=project,
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=project,
        capture_output=True,
        check=True,
    )

    return project


@pytest.fixture
def cli_skill(cli_project: Path) -> Path:
    """Create a test skill in the project."""
    skill_dir = cli_project / "skills" / "test-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("""---
name: test-skill
---

# Test Skill

A test skill for CLI testing.
""")
    return skill_dir


@pytest.fixture
def cli_config(cli_project: Path):
    """Factory fixture to create agr.toml with custom content."""

    def _create_config(content: str = "dependencies = []"):
        config_path = cli_project / "agr.toml"
        config_path.write_text(content)
        return config_path

    return _create_config


@pytest.fixture
def agr(cli_project: Path):
    """Helper to run agr commands in the project."""

    def _run(*args: str, **kwargs):
        return run_cli(["agr", *args], cwd=cli_project, **kwargs)

    return _run


@pytest.fixture
def agrx(cli_project: Path):
    """Helper to run agrx commands in the project."""

    def _run(*args: str, **kwargs):
        return run_cli(["agrx", *args], cwd=cli_project, **kwargs)

    return _run
