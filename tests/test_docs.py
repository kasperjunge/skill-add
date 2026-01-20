"""Tests to verify documentation accuracy against implementation."""

import re
from pathlib import Path

import pytest
import tomlkit

from agr.config import VALID_TYPES, AgrConfig
from agr.fetcher.types import ResourceType, RESOURCE_CONFIGS
from agr.adapters import AdapterRegistry


# Path to docs directory
DOCS_DIR = Path(__file__).parent.parent / "docs" / "docs"
ROOT_DIR = Path(__file__).parent.parent


class TestResourceTypeCoverage:
    """Ensure all resource types are documented."""

    def test_all_resource_types_in_valid_types(self):
        """Test that all ResourceType enum values are in VALID_TYPES."""
        for rt in ResourceType:
            assert rt.value in VALID_TYPES, f"ResourceType.{rt.name} not in VALID_TYPES"

    def test_all_resource_types_have_configs(self):
        """Test that all ResourceType enum values have RESOURCE_CONFIGS."""
        for rt in ResourceType:
            assert rt in RESOURCE_CONFIGS, f"ResourceType.{rt.name} not in RESOURCE_CONFIGS"

    def test_resource_types_documented(self):
        """Test that resource-types.md mentions all resource types."""
        resource_types_doc = DOCS_DIR / "concepts" / "resource-types.md"
        if not resource_types_doc.exists():
            pytest.skip("resource-types.md not found")

        content = resource_types_doc.read_text().lower()

        for rt in ResourceType:
            # Check that the type is mentioned as a heading or description
            assert rt.value in content, f"ResourceType '{rt.value}' not documented in resource-types.md"


class TestValidTypesDocumentation:
    """Test that valid types are consistently documented."""

    def test_valid_types_in_managing_dependencies(self):
        """Test that managing-dependencies.md lists all valid types."""
        doc = DOCS_DIR / "guides" / "managing-dependencies.md"
        if not doc.exists():
            pytest.skip("managing-dependencies.md not found")

        content = doc.read_text()

        # Find the "Valid types:" line
        match = re.search(r"Valid types:\s*`([^`]+)`(?:,\s*`([^`]+)`)*", content)
        if match:
            # Extract types from the line
            types_line = content[content.find("Valid types:"):content.find("Valid types:") + 200]
            documented_types = set(re.findall(r"`(\w+)`", types_line))

            for valid_type in VALID_TYPES:
                assert valid_type in documented_types, (
                    f"Type '{valid_type}' not in documented valid types"
                )


class TestConfigExamples:
    """Test that documented config examples are valid."""

    def test_example_toml_parses(self):
        """Test that example agr.toml snippets in docs are valid TOML."""
        doc = DOCS_DIR / "guides" / "managing-dependencies.md"
        if not doc.exists():
            pytest.skip("managing-dependencies.md not found")

        content = doc.read_text()

        # Find TOML code blocks
        toml_blocks = re.findall(r"```toml\n(.*?)```", content, re.DOTALL)

        for i, block in enumerate(toml_blocks):
            # Skip blocks that are just comments or partial examples
            if block.strip().startswith("#") and "=" not in block:
                continue

            try:
                tomlkit.parse(block)
            except Exception as e:
                pytest.fail(f"TOML block {i+1} failed to parse: {e}\nContent:\n{block}")

    def test_dependency_format_valid(self):
        """Test that documented dependency formats are valid."""
        # Create dependencies using the documented format
        valid_examples = [
            {"handle": "kasperjunge/commit", "type": "skill"},
            {"path": "./commands/docs.md", "type": "command"},
            {"handle": "acme/tools/review", "type": "command"},
        ]

        for example in valid_examples:
            # This should not raise an exception
            from agr.config import Dependency
            if "handle" in example:
                dep = Dependency(handle=example["handle"], type=example["type"])
                assert dep.is_remote
            else:
                dep = Dependency(path=example["path"], type=example["type"])
                assert dep.is_local


class TestToolsConfigDocumentation:
    """Test that tools configuration is properly documented."""

    def test_tools_config_example_valid(self):
        """Test that the documented [tools] config format is valid."""
        example = """
[tools]
targets = ["claude", "cursor"]
"""
        doc = tomlkit.parse(example)
        assert "tools" in doc
        assert doc["tools"]["targets"] == ["claude", "cursor"]

    def test_documented_tools_are_registered(self):
        """Test that documented tool names are actually registered."""
        doc = DOCS_DIR / "guides" / "managing-dependencies.md"
        if not doc.exists():
            pytest.skip("managing-dependencies.md not found")

        content = doc.read_text()

        # Find tool names in examples (claude, cursor)
        tool_mentions = re.findall(r'--tool\s+(\w+)', content)

        registered_tools = AdapterRegistry.all_names()

        for tool in set(tool_mentions):
            assert tool in registered_tools, (
                f"Documented tool '{tool}' is not registered in AdapterRegistry"
            )


class TestCLIDocumentation:
    """Test that CLI documentation matches implementation."""

    def test_documented_commands_exist(self):
        """Test that documented CLI commands actually exist."""
        from agr.cli.main import app

        # Get registered commands and groups from the app
        registered_names = set()

        # Add command names
        for command in app.registered_commands:
            name = command.name or (command.callback.__name__ if command.callback else None)
            if name:
                registered_names.add(name)

        # Add group names
        for group_info in app.registered_groups:
            if hasattr(group_info, 'name') and group_info.name:
                registered_names.add(group_info.name)
            elif hasattr(group_info, 'typer_instance'):
                # Try to get the name from the typer instance
                pass

        # Check that basic commands are documented
        expected_commands = {"add", "remove", "sync", "list", "init"}

        for cmd in expected_commands:
            found = cmd in registered_names or any(cmd in name for name in registered_names)
            assert found, f"Command '{cmd}' not found in CLI. Found: {registered_names}"

    def test_documented_flags_in_sync(self):
        """Test that documented flags for agr sync exist."""
        from agr.cli.sync import sync

        import inspect
        sig = inspect.signature(sync)
        params = set(sig.parameters.keys())

        # Documented flags (converted to parameter names)
        expected_params = {"global_install", "prune", "local_only", "remote_only", "overwrite", "yes", "tool"}

        for param in expected_params:
            assert param in params, f"Documented flag '--{param}' not in sync command"


class TestReadmeAccuracy:
    """Test that README.md is accurate."""

    def test_readme_commands_table(self):
        """Test that README command table has valid commands."""
        readme = ROOT_DIR / "README.md"
        if not readme.exists():
            pytest.skip("README.md not found")

        content = readme.read_text()

        # Check that key commands are mentioned
        expected_commands = [
            "agr add",
            "agr remove",
            "agr sync",
            "agr list",
            "agr init",
            "agrx",
        ]

        for cmd in expected_commands:
            assert cmd in content, f"Command '{cmd}' not mentioned in README"


class TestChangelogFormat:
    """Test that CHANGELOG.md follows conventions."""

    def test_changelog_exists(self):
        """Test that CHANGELOG.md exists."""
        changelog = ROOT_DIR / "CHANGELOG.md"
        assert changelog.exists(), "CHANGELOG.md not found"

    def test_changelog_has_current_version(self):
        """Test that CHANGELOG.md includes the current version."""
        changelog = ROOT_DIR / "CHANGELOG.md"
        if not changelog.exists():
            pytest.skip("CHANGELOG.md not found")

        # Read current version from pyproject.toml
        pyproject = ROOT_DIR / "pyproject.toml"
        pyproject_content = tomlkit.parse(pyproject.read_text())
        current_version = pyproject_content["project"]["version"]

        changelog_content = changelog.read_text()
        assert current_version in changelog_content, (
            f"Current version {current_version} not in CHANGELOG.md"
        )

    def test_changelog_format(self):
        """Test that CHANGELOG.md follows Keep a Changelog format."""
        changelog = ROOT_DIR / "CHANGELOG.md"
        if not changelog.exists():
            pytest.skip("CHANGELOG.md not found")

        content = changelog.read_text()

        # Check for standard sections
        assert "## [" in content, "CHANGELOG missing version headers"
        assert any(
            section in content for section in ["### Added", "### Changed", "### Fixed", "### Removed"]
        ), "CHANGELOG missing standard sections"
