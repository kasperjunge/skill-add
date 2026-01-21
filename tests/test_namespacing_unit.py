"""Unit tests for path namespacing and flattening functions."""

from pathlib import Path

import pytest

from agr.utils import (
    TYPE_DIRECTORIES,
    compute_flattened_resource_name,
    compute_flattened_skill_name,
    compute_path_segments,
    compute_path_segments_from_skill_path,
    find_package_context,
    update_skill_md_name,
)


class TestComputePathSegments:
    """Tests for compute_path_segments() with various type directories."""

    # Skills directory tests
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

    # Commands directory tests
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

    # Agents directory tests
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

    # Rules directory tests
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

    # Edge cases
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


# ============================================================================
# compute_path_segments_from_skill_path Tests (deprecated alias)
# ============================================================================


class TestComputePathSegmentsFromSkillPath:
    """Tests for compute_path_segments_from_skill_path helper (deprecated)."""

    def test_flat_skill_path(self):
        """Test flat skill path segment extraction."""
        path = Path("./resources/skills/commit")
        result = compute_path_segments_from_skill_path(path)
        assert result == ["commit"]

    def test_nested_skill_path(self):
        """Test nested skill path segment extraction."""
        path = Path("./resources/skills/product-strategy/growth-hacker")
        result = compute_path_segments_from_skill_path(path)
        assert result == ["product-strategy", "growth-hacker"]

    def test_skill_path_without_skills_dir(self):
        """Test skill path without 'skills' in the path."""
        path = Path("./my-custom-dir/my-skill")
        result = compute_path_segments_from_skill_path(path)
        # Falls back to just the name
        assert result == ["my-skill"]


# ============================================================================
# compute_flattened_resource_name Tests
# ============================================================================


class TestComputeFlattenedResourceName:
    """Tests for compute_flattened_resource_name() function."""

    def test_standalone_resource(self):
        """("local", ["skill"]) -> "local:skill" """
        result = compute_flattened_resource_name("local", ["skill"])
        assert result == "local:skill"

    def test_nested_resource(self):
        """("local", ["git", "status"]) -> "local:git:status" """
        result = compute_flattened_resource_name("local", ["git", "status"])
        assert result == "local:git:status"

    def test_packaged_resource(self):
        """("local", ["skill"], "pkg") -> "local:pkg:skill" """
        result = compute_flattened_resource_name("local", ["skill"], "pkg")
        assert result == "local:pkg:skill"

    def test_nested_packaged_resource(self):
        """("local", ["a", "b"], "pkg") -> "local:pkg:a:b" """
        result = compute_flattened_resource_name("local", ["a", "b"], "pkg")
        assert result == "local:pkg:a:b"

    def test_deeply_nested_standalone(self):
        """("user", ["a", "b", "c", "d"]) -> "user:a:b:c:d"."""
        result = compute_flattened_resource_name("user", ["a", "b", "c", "d"])
        assert result == "user:a:b:c:d"

    def test_empty_segments_raises(self):
        """Empty path segments should raise ValueError."""
        with pytest.raises(ValueError):
            compute_flattened_resource_name("user", [])

    def test_none_package_is_ignored(self):
        """None package name is equivalent to not passing it."""
        result = compute_flattened_resource_name("user", ["commit"], None)
        assert result == "user:commit"


# ============================================================================
# compute_flattened_skill_name Tests (deprecated alias)
# ============================================================================


class TestComputeFlattenedSkillName:
    """Tests for compute_flattened_skill_name helper (deprecated)."""

    def test_flat_skill(self):
        """Test flat skill name computation."""
        result = compute_flattened_skill_name("kasperjunge", ["commit"])
        assert result == "kasperjunge:commit"

    def test_nested_skill(self):
        """Test nested skill name computation."""
        result = compute_flattened_skill_name(
            "kasperjunge", ["product-strategy", "growth-hacker"]
        )
        assert result == "kasperjunge:product-strategy:growth-hacker"

    def test_empty_segments_raises(self):
        """Test that empty path segments raises an error."""
        with pytest.raises(ValueError):
            compute_flattened_skill_name("kasperjunge", [])

    def test_delegates_to_new_function(self):
        """Test that deprecated function delegates to new one."""
        result = compute_flattened_skill_name("kasperjunge", ["commit"])
        expected = compute_flattened_resource_name("kasperjunge", ["commit"])
        assert result == expected


# ============================================================================
# find_package_context Tests
# ============================================================================


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


# ============================================================================
# update_skill_md_name Tests
# ============================================================================


class TestUpdateSkillMdName:
    """Tests for update_skill_md_name helper."""

    def test_updates_existing_name(self, tmp_path: Path):
        """Test updating existing name field in SKILL.md."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            """---
name: my-skill
description: A test skill
---

# My Skill
"""
        )

        update_skill_md_name(skill_dir, "kasperjunge:my-skill")

        content = skill_md.read_text()
        assert "name: kasperjunge:my-skill" in content
        assert "description: A test skill" in content
        assert "# My Skill" in content

    def test_adds_name_to_existing_frontmatter(self, tmp_path: Path):
        """Test adding name to frontmatter without name field."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text(
            """---
description: A test skill
---

# My Skill
"""
        )

        update_skill_md_name(skill_dir, "kasperjunge:my-skill")

        content = skill_md.read_text()
        assert "name: kasperjunge:my-skill" in content
        assert "description: A test skill" in content

    def test_adds_frontmatter_when_missing(self, tmp_path: Path):
        """Test adding frontmatter when completely missing."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("# My Skill\n\nSome content.")

        update_skill_md_name(skill_dir, "kasperjunge:my-skill")

        content = skill_md.read_text()
        assert content.startswith("---\n")
        assert "name: kasperjunge:my-skill" in content
        assert "# My Skill" in content

    def test_raises_when_skill_md_missing(self, tmp_path: Path):
        """Test that FileNotFoundError is raised when SKILL.md doesn't exist."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()

        with pytest.raises(FileNotFoundError):
            update_skill_md_name(skill_dir, "kasperjunge:my-skill")


# ============================================================================
# TYPE_DIRECTORIES Constant Tests
# ============================================================================


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
