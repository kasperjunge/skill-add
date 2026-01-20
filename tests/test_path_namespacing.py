"""Tests for path namespacing functionality (Issue #34).

Tests the path namespacing logic where path segments under type directories
(skills/, commands/, agents/, rules/) become namespace segments.

Naming formula: username : package : path : resource

Examples:
- Standalone: skills/git/status/SKILL.md -> user:git:status
- Packaged: pkg/skills/git/status/SKILL.md -> user:my-toolkit:git:status
- Outside type dir: pkg/standalone/SKILL.md -> user:my-toolkit:standalone
"""

import pytest
from pathlib import Path

from typer.testing import CliRunner

from agr.cli.main import app
from agr.utils import (
    TYPE_DIRECTORIES,
    compute_flattened_resource_name,
    compute_path_segments,
    find_package_context,
)


runner = CliRunner()


class TestComputePathSegments:
    """Tests for compute_path_segments() with various type directories."""

    def test_skills_dir_single_level(self):
        """skills/commit -> ["commit"]"""
        path = Path("skills/commit")
        result = compute_path_segments(path)
        assert result == ["commit"]

    def test_skills_dir_nested(self):
        """skills/git/status -> ["git", "status"]"""
        path = Path("skills/git/status")
        result = compute_path_segments(path)
        assert result == ["git", "status"]

    def test_skills_dir_deeply_nested(self):
        """skills/category/subcategory/skill -> ["category", "subcategory", "skill"]"""
        path = Path("skills/category/subcategory/skill")
        result = compute_path_segments(path)
        assert result == ["category", "subcategory", "skill"]

    def test_commands_dir_single(self):
        """commands/deploy.md -> ["deploy"]"""
        path = Path("commands/deploy.md")
        result = compute_path_segments(path)
        assert result == ["deploy"]

    def test_commands_dir_nested(self):
        """commands/git/clone.md -> ["git", "clone"]"""
        path = Path("commands/git/clone.md")
        result = compute_path_segments(path)
        assert result == ["git", "clone"]

    def test_agents_dir_single(self):
        """agents/reviewer.md -> ["reviewer"]"""
        path = Path("agents/reviewer.md")
        result = compute_path_segments(path)
        assert result == ["reviewer"]

    def test_agents_dir_nested(self):
        """agents/code/reviewer.md -> ["code", "reviewer"]"""
        path = Path("agents/code/reviewer.md")
        result = compute_path_segments(path)
        assert result == ["code", "reviewer"]

    def test_rules_dir_single(self):
        """rules/no-console.md -> ["no-console"]"""
        path = Path("rules/no-console.md")
        result = compute_path_segments(path)
        assert result == ["no-console"]

    def test_rules_dir_nested(self):
        """rules/security/no-eval.md -> ["security", "no-eval"]"""
        path = Path("rules/security/no-eval.md")
        result = compute_path_segments(path)
        assert result == ["security", "no-eval"]

    def test_outside_type_dir_file(self):
        """standalone/SKILL.md -> ["SKILL"] (file without type dir)"""
        path = Path("standalone/SKILL.md")
        result = compute_path_segments(path)
        assert result == ["SKILL"]

    def test_outside_type_dir_directory(self):
        """custom/my-skill -> ["my-skill"]"""
        path = Path("custom/my-skill")
        result = compute_path_segments(path)
        assert result == ["my-skill"]

    def test_with_resources_prefix(self):
        """./resources/skills/commit -> ["commit"]"""
        path = Path("./resources/skills/commit")
        result = compute_path_segments(path)
        assert result == ["commit"]

    def test_with_dot_prefix(self):
        """./skills/commit -> ["commit"]"""
        path = Path("./skills/commit")
        result = compute_path_segments(path)
        assert result == ["commit"]

    def test_file_extension_stripped(self):
        """commands/test.md -> ["test"] (extension removed)"""
        path = Path("commands/test.md")
        result = compute_path_segments(path)
        assert result == ["test"]

    def test_with_explicit_root(self):
        """Test with explicit resource root parameter."""
        root = Path("./my-repo/skills")
        path = Path("./my-repo/skills/git/status")
        result = compute_path_segments(path, resource_root=root)
        assert result == ["git", "status"]

    def test_explicit_root_not_in_path(self):
        """Test with explicit root that doesn't match path."""
        root = Path("./other-repo/skills")
        path = Path("./my-repo/skills/commit")
        result = compute_path_segments(path, resource_root=root)
        # Falls back to just the name since path isn't relative to root
        assert result == ["commit"]

    def test_custom_type_dirs(self):
        """Test with custom type directories tuple."""
        path = Path("prompts/git/commit")
        # Default TYPE_DIRECTORIES doesn't include "prompts"
        result = compute_path_segments(path)
        assert result == ["commit"]  # Falls back to name

        # With custom type dirs
        result = compute_path_segments(path, type_dirs=("prompts",))
        assert result == ["git", "commit"]


class TestFindPackageContext:
    """Tests for find_package_context() function."""

    def test_finds_package_from_nested_skill(self, tmp_path: Path):
        """pkg/skills/git/SKILL.md -> ("pkg-name", pkg_path)"""
        pkg_dir = tmp_path / "my-toolkit"
        skill_dir = pkg_dir / "skills" / "git"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Git Skill")
        (pkg_dir / "PACKAGE.md").write_text(
            """---
name: my-toolkit
---

# My Toolkit Package
"""
        )

        package_name, package_root = find_package_context(skill_dir)
        assert package_name == "my-toolkit"
        assert package_root == pkg_dir

    def test_finds_package_from_deeply_nested(self, tmp_path: Path):
        """pkg/skills/category/subcategory/skill/SKILL.md finds package."""
        pkg_dir = tmp_path / "deep-pkg"
        skill_dir = pkg_dir / "skills" / "cat" / "subcat" / "skill"
        skill_dir.mkdir(parents=True)
        (pkg_dir / "PACKAGE.md").write_text(
            """---
name: deep-pkg
---
"""
        )

        package_name, package_root = find_package_context(skill_dir)
        assert package_name == "deep-pkg"
        assert package_root == pkg_dir

    def test_returns_none_outside_package(self, tmp_path: Path):
        """skills/git/SKILL.md -> (None, None)"""
        skill_dir = tmp_path / "skills" / "git"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Git Skill")

        package_name, package_root = find_package_context(skill_dir)
        assert package_name is None
        assert package_root is None

    def test_handles_invalid_package_md(self, tmp_path: Path):
        """Invalid PACKAGE.md returns None name but sets root."""
        pkg_dir = tmp_path / "broken-pkg"
        skill_dir = pkg_dir / "skills" / "git"
        skill_dir.mkdir(parents=True)
        (pkg_dir / "PACKAGE.md").write_text("No frontmatter here")

        package_name, package_root = find_package_context(skill_dir)
        assert package_name is None
        assert package_root == pkg_dir  # Still identifies package boundary

    def test_handles_file_path(self, tmp_path: Path):
        """Works with file paths, not just directories."""
        pkg_dir = tmp_path / "file-pkg"
        cmd_file = pkg_dir / "commands" / "deploy.md"
        cmd_file.parent.mkdir(parents=True)
        cmd_file.write_text("# Deploy Command")
        (pkg_dir / "PACKAGE.md").write_text(
            """---
name: file-pkg
---
"""
        )

        package_name, package_root = find_package_context(cmd_file)
        assert package_name == "file-pkg"
        assert package_root == pkg_dir


class TestComputeFlattenedResourceName:
    """Tests for compute_flattened_resource_name() with package context."""

    def test_standalone_skill(self):
        """("user", ["git", "status"]) -> "user:git:status"."""
        result = compute_flattened_resource_name("user", ["git", "status"])
        assert result == "user:git:status"

    def test_packaged_skill(self):
        """("user", ["git", "status"], "my-toolkit") -> "user:my-toolkit:git:status"."""
        result = compute_flattened_resource_name(
            "user", ["git", "status"], "my-toolkit"
        )
        assert result == "user:my-toolkit:git:status"

    def test_resource_outside_type_dir(self):
        """("user", ["standalone"], "my-toolkit") -> "user:my-toolkit:standalone"."""
        result = compute_flattened_resource_name(
            "user", ["standalone"], "my-toolkit"
        )
        assert result == "user:my-toolkit:standalone"

    def test_single_segment_standalone(self):
        """("user", ["commit"]) -> "user:commit"."""
        result = compute_flattened_resource_name("user", ["commit"])
        assert result == "user:commit"

    def test_single_segment_packaged(self):
        """("user", ["commit"], "pkg") -> "user:pkg:commit"."""
        result = compute_flattened_resource_name("user", ["commit"], "pkg")
        assert result == "user:pkg:commit"

    def test_deeply_nested_standalone(self):
        """("user", ["a", "b", "c", "d"]) -> "user:a:b:c:d"."""
        result = compute_flattened_resource_name("user", ["a", "b", "c", "d"])
        assert result == "user:a:b:c:d"

    def test_deeply_nested_packaged(self):
        """("user", ["a", "b", "c"], "pkg") -> "user:pkg:a:b:c"."""
        result = compute_flattened_resource_name("user", ["a", "b", "c"], "pkg")
        assert result == "user:pkg:a:b:c"

    def test_empty_segments_raises(self):
        """Empty path segments should raise ValueError."""
        with pytest.raises(ValueError):
            compute_flattened_resource_name("user", [])

    def test_none_package_is_ignored(self):
        """None package name is equivalent to not passing it."""
        result = compute_flattened_resource_name("user", ["commit"], None)
        assert result == "user:commit"


class TestIntegrationAddSkillWithPath:
    """Integration tests for adding skills with path namespacing."""

    def test_add_nested_skill_path_segments(self, tmp_path: Path, monkeypatch):
        """Test that skills/git/status installs as user:git:status."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create nested skill structure
        skill_dir = tmp_path / "skills" / "git" / "status"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(
            """---
name: status
---

# Git Status Skill
"""
        )

        result = runner.invoke(app, ["add", "./skills/git/status"])
        assert result.exit_code == 0

        # Should be installed with flattened path
        installed = tmp_path / ".claude" / "skills" / "local:git:status" / "SKILL.md"
        assert installed.exists()
        content = installed.read_text()
        assert "name: local:git:status" in content

    def test_add_skill_in_package_context(self, tmp_path: Path, monkeypatch):
        """Test that skills in a package get package name prepended."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create package with skill
        pkg_dir = tmp_path / "my-toolkit"
        skill_dir = pkg_dir / "skills" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Commit Skill")
        (pkg_dir / "PACKAGE.md").write_text(
            """---
name: my-toolkit
---

# My Toolkit
"""
        )

        # Add the package (explodes contents)
        result = runner.invoke(app, ["add", "./my-toolkit", "--type", "package"])
        assert result.exit_code == 0

        # Skill should be installed with package name
        installed = (
            tmp_path / ".claude" / "skills" / "local:my-toolkit:commit" / "SKILL.md"
        )
        assert installed.exists()
        content = installed.read_text()
        assert "name: local:my-toolkit:commit" in content


class TestIntegrationSyncWithPath:
    """Integration tests for syncing with path namespacing."""

    def test_sync_nested_skill(self, tmp_path: Path, monkeypatch):
        """Test that sync correctly handles nested skill paths."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create nested skill
        skill_dir = tmp_path / "skills" / "product" / "flywheel"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Flywheel Skill")

        # Create agr.toml
        (tmp_path / "agr.toml").write_text(
            """
[[dependencies]]
path = "./skills/product/flywheel"
type = "skill"
"""
        )

        result = runner.invoke(app, ["sync"])
        assert result.exit_code == 0

        # Should be installed with nested path
        installed = (
            tmp_path / ".claude" / "skills" / "local:product:flywheel" / "SKILL.md"
        )
        assert installed.exists()


class TestTypeDirectoriesConstant:
    """Tests for TYPE_DIRECTORIES constant."""

    def test_contains_expected_types(self):
        """TYPE_DIRECTORIES should contain all expected type directories."""
        assert "skills" in TYPE_DIRECTORIES
        assert "commands" in TYPE_DIRECTORIES
        assert "agents" in TYPE_DIRECTORIES
        assert "rules" in TYPE_DIRECTORIES

    def test_is_tuple(self):
        """TYPE_DIRECTORIES should be a tuple (immutable)."""
        assert isinstance(TYPE_DIRECTORIES, tuple)
