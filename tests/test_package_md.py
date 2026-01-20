"""Tests for PACKAGE.md marker file support."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agr.cli.main import app
from agr.config import AgrConfig
from agr.package import parse_package_md, validate_no_nested_packages


runner = CliRunner()


class TestParsePackageMd:
    """Unit tests for parse_package_md()."""

    def test_valid_package_md_with_name(self, tmp_path: Path):
        """Test parsing a valid PACKAGE.md with name field."""
        package_md = tmp_path / "PACKAGE.md"
        package_md.write_text("---\nname: my-package\n---\n\n# Documentation")

        result = parse_package_md(package_md)

        assert result.valid is True
        assert result.name == "my-package"
        assert result.error is None

    def test_valid_package_md_with_quoted_name(self, tmp_path: Path):
        """Test parsing PACKAGE.md with quoted name."""
        package_md = tmp_path / "PACKAGE.md"
        package_md.write_text('---\nname: "my-package"\n---\n')

        result = parse_package_md(package_md)

        assert result.valid is True
        assert result.name == "my-package"

    def test_valid_package_md_with_single_quoted_name(self, tmp_path: Path):
        """Test parsing PACKAGE.md with single-quoted name."""
        package_md = tmp_path / "PACKAGE.md"
        package_md.write_text("---\nname: 'my-package'\n---\n")

        result = parse_package_md(package_md)

        assert result.valid is True
        assert result.name == "my-package"

    def test_valid_package_md_name_with_underscore(self, tmp_path: Path):
        """Test valid name with underscore."""
        package_md = tmp_path / "PACKAGE.md"
        package_md.write_text("---\nname: my_package\n---\n")

        result = parse_package_md(package_md)

        assert result.valid is True
        assert result.name == "my_package"

    def test_valid_single_char_name(self, tmp_path: Path):
        """Test valid single character name."""
        package_md = tmp_path / "PACKAGE.md"
        package_md.write_text("---\nname: a\n---\n")

        result = parse_package_md(package_md)

        assert result.valid is True
        assert result.name == "a"

    def test_missing_file_error(self, tmp_path: Path):
        """Test error when PACKAGE.md doesn't exist."""
        package_md = tmp_path / "PACKAGE.md"

        result = parse_package_md(package_md)

        assert result.valid is False
        assert result.name is None
        assert "not found" in result.error

    def test_no_frontmatter_error(self, tmp_path: Path):
        """Test error when PACKAGE.md has no frontmatter."""
        package_md = tmp_path / "PACKAGE.md"
        package_md.write_text("# Just documentation\n\nNo frontmatter here.")

        result = parse_package_md(package_md)

        assert result.valid is False
        assert result.name is None
        assert "frontmatter" in result.error.lower()

    def test_missing_name_field_error(self, tmp_path: Path):
        """Test error when frontmatter is missing name field."""
        package_md = tmp_path / "PACKAGE.md"
        package_md.write_text("---\ndescription: Some package\n---\n")

        result = parse_package_md(package_md)

        assert result.valid is False
        assert result.name is None
        assert "name" in result.error

    def test_empty_name_error(self, tmp_path: Path):
        """Test error when name field is empty."""
        package_md = tmp_path / "PACKAGE.md"
        package_md.write_text("---\nname:\n---\n")

        result = parse_package_md(package_md)

        assert result.valid is False
        assert result.name is None
        assert "empty" in result.error.lower()

    def test_empty_quoted_name_error(self, tmp_path: Path):
        """Test error when name is empty quotes."""
        package_md = tmp_path / "PACKAGE.md"
        package_md.write_text('---\nname: ""\n---\n')

        result = parse_package_md(package_md)

        assert result.valid is False
        assert "empty" in result.error.lower()

    def test_invalid_name_starts_with_hyphen_error(self, tmp_path: Path):
        """Test error when name starts with hyphen."""
        package_md = tmp_path / "PACKAGE.md"
        package_md.write_text("---\nname: -invalid\n---\n")

        result = parse_package_md(package_md)

        assert result.valid is False
        assert "Invalid package name" in result.error

    def test_invalid_name_ends_with_hyphen_error(self, tmp_path: Path):
        """Test error when name ends with hyphen."""
        package_md = tmp_path / "PACKAGE.md"
        package_md.write_text("---\nname: invalid-\n---\n")

        result = parse_package_md(package_md)

        assert result.valid is False
        assert "Invalid package name" in result.error

    def test_invalid_name_with_spaces_error(self, tmp_path: Path):
        """Test error when name contains spaces."""
        package_md = tmp_path / "PACKAGE.md"
        package_md.write_text("---\nname: my package\n---\n")

        result = parse_package_md(package_md)

        assert result.valid is False
        assert "Invalid package name" in result.error

    def test_invalid_name_with_special_chars_error(self, tmp_path: Path):
        """Test error when name contains special characters."""
        package_md = tmp_path / "PACKAGE.md"
        package_md.write_text("---\nname: my@package!\n---\n")

        result = parse_package_md(package_md)

        assert result.valid is False
        assert "Invalid package name" in result.error

    def test_malformed_frontmatter_missing_closing_error(self, tmp_path: Path):
        """Test error when frontmatter is missing closing delimiter."""
        package_md = tmp_path / "PACKAGE.md"
        package_md.write_text("---\nname: my-package\n# No closing delimiter")

        result = parse_package_md(package_md)

        assert result.valid is False
        assert "malformed" in result.error.lower()


class TestValidateNoNestedPackages:
    """Unit tests for validate_no_nested_packages()."""

    def test_no_nested_packages_returns_empty(self, tmp_path: Path):
        """Test that empty list is returned when no nested packages."""
        package_dir = tmp_path / "my-package"
        package_dir.mkdir()
        (package_dir / "PACKAGE.md").write_text("---\nname: my-package\n---\n")
        (package_dir / "skills").mkdir()

        result = validate_no_nested_packages(package_dir)

        assert result == []

    def test_single_nested_package_returns_path(self, tmp_path: Path):
        """Test that nested PACKAGE.md is detected."""
        package_dir = tmp_path / "my-package"
        package_dir.mkdir()
        (package_dir / "PACKAGE.md").write_text("---\nname: my-package\n---\n")

        nested_dir = package_dir / "subdir"
        nested_dir.mkdir()
        nested_pkg = nested_dir / "PACKAGE.md"
        nested_pkg.write_text("---\nname: nested\n---\n")

        result = validate_no_nested_packages(package_dir)

        assert len(result) == 1
        assert result[0] == nested_pkg

    def test_multiple_nested_packages_returns_all(self, tmp_path: Path):
        """Test that multiple nested PACKAGE.md files are detected."""
        package_dir = tmp_path / "my-package"
        package_dir.mkdir()
        (package_dir / "PACKAGE.md").write_text("---\nname: my-package\n---\n")

        nested1 = package_dir / "sub1" / "PACKAGE.md"
        nested1.parent.mkdir()
        nested1.write_text("---\nname: nested1\n---\n")

        nested2 = package_dir / "sub2" / "deep" / "PACKAGE.md"
        nested2.parent.mkdir(parents=True)
        nested2.write_text("---\nname: nested2\n---\n")

        result = validate_no_nested_packages(package_dir)

        assert len(result) == 2
        assert nested1 in result
        assert nested2 in result

    def test_ignores_root_package_md(self, tmp_path: Path):
        """Test that root PACKAGE.md is not included in results."""
        package_dir = tmp_path / "my-package"
        package_dir.mkdir()
        root_pkg = package_dir / "PACKAGE.md"
        root_pkg.write_text("---\nname: my-package\n---\n")

        result = validate_no_nested_packages(package_dir)

        assert root_pkg not in result
        assert result == []


class TestPackageMdIntegration:
    """Integration tests for agr add with PACKAGE.md."""

    def test_package_uses_package_md_name(self, tmp_path: Path, monkeypatch):
        """Test that package uses name from PACKAGE.md instead of directory name."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create package with PACKAGE.md
        pkg_dir = tmp_path / "my-dir-name"
        pkg_dir.mkdir()
        (pkg_dir / "PACKAGE.md").write_text("---\nname: custom-pkg-name\n---\n")

        # Add skill to make package non-empty
        skill_dir = pkg_dir / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        result = runner.invoke(app, ["add", "./my-dir-name"])

        assert result.exit_code == 0, result.output

        # Verify installed using name from PACKAGE.md, not directory name
        installed = tmp_path / ".claude" / "skills" / "local:custom-pkg-name:my-skill" / "SKILL.md"
        assert installed.exists(), f"Expected {installed} to exist"

        # Verify NOT installed with directory name
        wrong_path = tmp_path / ".claude" / "skills" / "local:my-dir-name:my-skill"
        assert not wrong_path.exists()

    def test_invalid_package_md_errors(self, tmp_path: Path, monkeypatch):
        """Test that invalid PACKAGE.md produces error."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create package with invalid PACKAGE.md (no frontmatter)
        pkg_dir = tmp_path / "bad-package"
        pkg_dir.mkdir()
        (pkg_dir / "PACKAGE.md").write_text("# No frontmatter here")

        # Add skill to avoid empty package error
        skill_dir = pkg_dir / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Skill")

        result = runner.invoke(app, ["add", "./bad-package"])

        assert result.exit_code == 1
        assert "Invalid PACKAGE.md" in result.output

    def test_nested_package_md_errors(self, tmp_path: Path, monkeypatch):
        """Test that nested PACKAGE.md produces error."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create package with nested PACKAGE.md
        pkg_dir = tmp_path / "parent-package"
        pkg_dir.mkdir()
        (pkg_dir / "PACKAGE.md").write_text("---\nname: parent\n---\n")

        nested = pkg_dir / "nested"
        nested.mkdir()
        (nested / "PACKAGE.md").write_text("---\nname: nested\n---\n")

        # Add skill to avoid empty package error
        skill_dir = pkg_dir / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Skill")

        result = runner.invoke(app, ["add", "./parent-package"])

        assert result.exit_code == 1
        assert "nested PACKAGE.md" in result.output

    def test_package_without_package_md_still_works(self, tmp_path: Path, monkeypatch):
        """Test backward compatibility: packages without PACKAGE.md still work."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create package without PACKAGE.md (old style)
        pkg_dir = tmp_path / "old-style-pkg"
        pkg_dir.mkdir()

        skill_dir = pkg_dir / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")
        (pkg_dir / "commands").mkdir()
        (pkg_dir / "agents").mkdir()

        result = runner.invoke(app, ["add", "./old-style-pkg", "--type", "package"])

        assert result.exit_code == 0, result.output

        # Verify installed using directory name
        installed = tmp_path / ".claude" / "skills" / "local:old-style-pkg:my-skill" / "SKILL.md"
        assert installed.exists()

    def test_package_md_auto_detects_type(self, tmp_path: Path, monkeypatch):
        """Test that PACKAGE.md triggers auto-detection as package type."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        # Create directory with PACKAGE.md but no standard subdirs
        pkg_dir = tmp_path / "unusual-structure"
        pkg_dir.mkdir()
        (pkg_dir / "PACKAGE.md").write_text("---\nname: my-pkg\n---\n")

        # Add skill in a non-standard location
        skill_dir = pkg_dir / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        result = runner.invoke(app, ["add", "./unusual-structure"])

        assert result.exit_code == 0, result.output
        assert "package" in result.output.lower()

    def test_package_md_with_multiple_skills(self, tmp_path: Path, monkeypatch):
        """Test package with PACKAGE.md and multiple skills."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        pkg_dir = tmp_path / "multi-skill-pkg"
        pkg_dir.mkdir()
        (pkg_dir / "PACKAGE.md").write_text("---\nname: toolkit\n---\n")

        for skill_name in ["skill-a", "skill-b", "nested/skill-c"]:
            skill_dir = pkg_dir / "skills" / skill_name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(f"# {skill_name}")

        result = runner.invoke(app, ["add", "./multi-skill-pkg"])

        assert result.exit_code == 0, result.output

        # Verify all skills installed with PACKAGE.md name
        assert (tmp_path / ".claude" / "skills" / "local:toolkit:skill-a" / "SKILL.md").exists()
        assert (tmp_path / ".claude" / "skills" / "local:toolkit:skill-b" / "SKILL.md").exists()
        assert (tmp_path / ".claude" / "skills" / "local:toolkit:nested:skill-c" / "SKILL.md").exists()
