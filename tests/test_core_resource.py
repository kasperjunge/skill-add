"""Tests for agr.core.resource module."""

import pytest

from agr.core.resource import Resource, ResourceSpec, ResourceType


class TestResourceType:
    """Tests for ResourceType enum."""

    def test_skill_type(self):
        """SKILL type has correct value."""
        assert ResourceType.SKILL.value == "skill"


class TestResourceSpec:
    """Tests for ResourceSpec class."""

    @pytest.fixture
    def skill_spec(self):
        """Create a skill spec for testing."""
        return ResourceSpec(
            type=ResourceType.SKILL,
            marker_file="SKILL.md",
            is_directory=True,
            search_paths=("resources/skills", "skills", "."),
            required_frontmatter=(),
            optional_frontmatter=("name", "description"),
            name_pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$",
        )

    def test_validate_name_valid(self, skill_spec):
        """Valid names pass validation."""
        assert skill_spec.validate_name("commit")
        assert skill_spec.validate_name("my-skill")
        assert skill_spec.validate_name("my_skill")
        assert skill_spec.validate_name("skill123")
        assert skill_spec.validate_name("1skill")

    def test_validate_name_invalid(self, skill_spec):
        """Invalid names fail validation."""
        assert not skill_spec.validate_name("")
        assert not skill_spec.validate_name("-skill")
        assert not skill_spec.validate_name("_skill")
        assert not skill_spec.validate_name("skill!")
        assert not skill_spec.validate_name("skill@name")

    def test_is_valid_resource_directory(self, skill_spec, tmp_path):
        """Valid skill directory is recognized."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill")

        assert skill_spec.is_valid_resource(skill_dir)

    def test_is_valid_resource_missing_marker(self, skill_spec, tmp_path):
        """Directory without marker is not valid."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()

        assert not skill_spec.is_valid_resource(skill_dir)

    def test_is_valid_resource_file_not_dir(self, skill_spec, tmp_path):
        """File is not valid for directory-based resource."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")

        assert not skill_spec.is_valid_resource(file_path)

    def test_is_valid_resource_nonexistent(self, skill_spec, tmp_path):
        """Nonexistent path is not valid."""
        assert not skill_spec.is_valid_resource(tmp_path / "nonexistent")

    def test_frozen(self, skill_spec):
        """ResourceSpec is frozen (immutable)."""
        with pytest.raises(Exception):  # FrozenInstanceError
            skill_spec.marker_file = "OTHER.md"


class TestResource:
    """Tests for Resource class."""

    @pytest.fixture
    def skill_spec(self):
        """Create a skill spec for testing."""
        return ResourceSpec(
            type=ResourceType.SKILL,
            marker_file="SKILL.md",
            is_directory=True,
            search_paths=("resources/skills", "skills", "."),
            required_frontmatter=(),
            optional_frontmatter=("name",),
            name_pattern=r"^[a-zA-Z0-9][a-zA-Z0-9_-]*$",
        )

    @pytest.fixture
    def skill_resource(self, skill_spec, tmp_path):
        """Create a skill resource for testing."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Skill")
        return Resource(
            spec=skill_spec,
            name="my-skill",
            path=skill_dir,
        )

    def test_type_property(self, skill_resource):
        """type property returns the spec's type."""
        assert skill_resource.type == ResourceType.SKILL

    def test_marker_path(self, skill_resource, tmp_path):
        """marker_path returns correct path."""
        expected = tmp_path / "my-skill" / "SKILL.md"
        assert skill_resource.marker_path == expected

    def test_is_valid(self, skill_resource):
        """is_valid returns True for valid resource."""
        assert skill_resource.is_valid()

    def test_is_valid_after_deletion(self, skill_resource):
        """is_valid returns False after marker deletion."""
        skill_resource.marker_path.unlink()
        assert not skill_resource.is_valid()

    def test_metadata_default(self, skill_spec, tmp_path):
        """metadata defaults to empty dict."""
        resource = Resource(
            spec=skill_spec,
            name="test",
            path=tmp_path,
        )
        assert resource.metadata == {}

    def test_metadata_custom(self, skill_spec, tmp_path):
        """metadata can be set."""
        resource = Resource(
            spec=skill_spec,
            name="test",
            path=tmp_path,
            metadata={"key": "value"},
        )
        assert resource.metadata == {"key": "value"}
