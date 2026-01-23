"""Tests for agr.core.discovery module."""

import pytest

from agr.core.discovery import (
    discover_resources_in_repo,
    find_resource_in_repo,
    is_valid_resource_path,
)
from agr.core.resource import ResourceSpec, ResourceType


class TestFindResourceInRepo:
    """Tests for find_resource_in_repo function."""

    @pytest.fixture
    def skill_spec(self):
        """Create a skill spec for testing."""
        return ResourceSpec(
            type=ResourceType.SKILL,
            marker_file="SKILL.md",
            is_directory=True,
            search_paths=("resources/skills", "skills", "."),
            required_frontmatter=(),
            optional_frontmatter=(),
            name_pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$",
        )

    def test_find_in_resources_skills(self, skill_spec, tmp_path):
        """Finds skill in resources/skills directory."""
        # Create resources/skills/commit structure
        skill_dir = tmp_path / "resources" / "skills" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Commit skill")

        resource = find_resource_in_repo(tmp_path, "commit", skill_spec)
        assert resource is not None
        assert resource.name == "commit"
        assert resource.path == skill_dir

    def test_find_in_skills(self, skill_spec, tmp_path):
        """Finds skill in skills directory."""
        skill_dir = tmp_path / "skills" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Commit skill")

        resource = find_resource_in_repo(tmp_path, "commit", skill_spec)
        assert resource is not None
        assert resource.name == "commit"
        assert resource.path == skill_dir

    def test_find_at_root(self, skill_spec, tmp_path):
        """Finds skill at root level."""
        skill_dir = tmp_path / "commit"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Commit skill")

        resource = find_resource_in_repo(tmp_path, "commit", skill_spec)
        assert resource is not None
        assert resource.name == "commit"
        assert resource.path == skill_dir

    def test_priority_order(self, skill_spec, tmp_path):
        """resources/skills takes priority over skills directory."""
        # Create skill in both locations
        primary = tmp_path / "resources" / "skills" / "commit"
        primary.mkdir(parents=True)
        (primary / "SKILL.md").write_text("# Primary")

        secondary = tmp_path / "skills" / "commit"
        secondary.mkdir(parents=True)
        (secondary / "SKILL.md").write_text("# Secondary")

        resource = find_resource_in_repo(tmp_path, "commit", skill_spec)
        assert resource is not None
        assert resource.path == primary

    def test_not_found(self, skill_spec, tmp_path):
        """Returns None when skill not found."""
        resource = find_resource_in_repo(tmp_path, "nonexistent", skill_spec)
        assert resource is None

    def test_missing_marker(self, skill_spec, tmp_path):
        """Returns None when directory exists but marker missing."""
        skill_dir = tmp_path / "skills" / "commit"
        skill_dir.mkdir(parents=True)
        # No SKILL.md created

        resource = find_resource_in_repo(tmp_path, "commit", skill_spec)
        assert resource is None


class TestDiscoverResourcesInRepo:
    """Tests for discover_resources_in_repo function."""

    @pytest.fixture
    def skill_spec(self):
        """Create a skill spec for testing."""
        return ResourceSpec(
            type=ResourceType.SKILL,
            marker_file="SKILL.md",
            is_directory=True,
            search_paths=("resources/skills", "skills", "."),
            required_frontmatter=(),
            optional_frontmatter=(),
            name_pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$",
        )

    def test_discover_multiple_skills(self, skill_spec, tmp_path):
        """Discovers multiple skills in a repo."""
        # Create skills in resources/skills
        for name in ["commit", "review", "test"]:
            skill_dir = tmp_path / "resources" / "skills" / name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(f"# {name}")

        resources = discover_resources_in_repo(tmp_path, skill_spec)
        names = {r.name for r in resources}
        assert names == {"commit", "review", "test"}

    def test_discover_across_locations(self, skill_spec, tmp_path):
        """Discovers skills from different search paths."""
        # Create in resources/skills
        (tmp_path / "resources" / "skills" / "commit").mkdir(parents=True)
        (tmp_path / "resources" / "skills" / "commit" / "SKILL.md").write_text("# Commit")

        # Create in skills
        (tmp_path / "skills" / "review").mkdir(parents=True)
        (tmp_path / "skills" / "review" / "SKILL.md").write_text("# Review")

        # Create at root
        (tmp_path / "test").mkdir()
        (tmp_path / "test" / "SKILL.md").write_text("# Test")

        resources = discover_resources_in_repo(tmp_path, skill_spec)
        names = {r.name for r in resources}
        assert names == {"commit", "review", "test"}

    def test_no_duplicates(self, skill_spec, tmp_path):
        """Doesn't return duplicates for same-named skills in different locations."""
        # Create same skill name in multiple locations
        (tmp_path / "resources" / "skills" / "commit").mkdir(parents=True)
        (tmp_path / "resources" / "skills" / "commit" / "SKILL.md").write_text("# Primary")

        (tmp_path / "skills" / "commit").mkdir(parents=True)
        (tmp_path / "skills" / "commit" / "SKILL.md").write_text("# Secondary")

        resources = discover_resources_in_repo(tmp_path, skill_spec)
        names = [r.name for r in resources]
        assert names.count("commit") == 1

    def test_empty_repo(self, skill_spec, tmp_path):
        """Returns empty list for repo with no skills."""
        resources = discover_resources_in_repo(tmp_path, skill_spec)
        assert resources == []

    def test_ignores_invalid_dirs(self, skill_spec, tmp_path):
        """Ignores directories without marker file."""
        # Create valid skill
        (tmp_path / "skills" / "valid").mkdir(parents=True)
        (tmp_path / "skills" / "valid" / "SKILL.md").write_text("# Valid")

        # Create invalid directory (no marker)
        (tmp_path / "skills" / "invalid").mkdir(parents=True)

        resources = discover_resources_in_repo(tmp_path, skill_spec)
        names = {r.name for r in resources}
        assert names == {"valid"}


class TestIsValidResourcePath:
    """Tests for is_valid_resource_path function."""

    @pytest.fixture
    def skill_spec(self):
        """Create a skill spec for testing."""
        return ResourceSpec(
            type=ResourceType.SKILL,
            marker_file="SKILL.md",
            is_directory=True,
            search_paths=(".",),
            required_frontmatter=(),
            optional_frontmatter=(),
            name_pattern=r"^[a-zA-Z0-9_-]+$",
        )

    def test_valid_path(self, skill_spec, tmp_path):
        """Returns True for valid resource path."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill")

        assert is_valid_resource_path(skill_dir, skill_spec)

    def test_invalid_path(self, skill_spec, tmp_path):
        """Returns False for invalid resource path."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        # No marker file

        assert not is_valid_resource_path(skill_dir, skill_spec)
