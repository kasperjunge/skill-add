"""Tests for agr.skill module."""

import pytest

from agr.skill import (
    SKILL_MARKER,
    create_skill_scaffold,
    is_valid_skill_dir,
    update_skill_md_name,
    validate_skill_name,
)


class TestIsValidSkillDir:
    """Tests for is_valid_skill_dir function."""

    def test_valid_skill(self, tmp_path):
        """Directory with SKILL.md is valid."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        (skill_dir / SKILL_MARKER).write_text("# Skill")
        assert is_valid_skill_dir(skill_dir)

    def test_missing_marker(self, tmp_path):
        """Directory without SKILL.md is not valid."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        assert not is_valid_skill_dir(skill_dir)

    def test_file_not_dir(self, tmp_path):
        """File is not valid."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")
        assert not is_valid_skill_dir(file_path)

    def test_nonexistent(self, tmp_path):
        """Nonexistent path is not valid."""
        assert not is_valid_skill_dir(tmp_path / "nonexistent")


class TestValidateSkillName:
    """Tests for validate_skill_name function."""

    def test_valid_simple(self):
        """Simple alphanumeric name is valid."""
        assert validate_skill_name("commit")

    def test_valid_with_hyphen(self):
        """Name with hyphens is valid."""
        assert validate_skill_name("my-skill")

    def test_valid_with_underscore(self):
        """Name with underscores is valid."""
        assert validate_skill_name("my_skill")

    def test_valid_with_numbers(self):
        """Name with numbers is valid."""
        assert validate_skill_name("skill123")

    def test_invalid_empty(self):
        """Empty name is invalid."""
        assert not validate_skill_name("")

    def test_invalid_starts_with_hyphen(self):
        """Name starting with hyphen is invalid."""
        assert not validate_skill_name("-skill")

    def test_invalid_starts_with_number(self):
        """Name starting with number is valid (alphanumeric)."""
        # Actually this should be valid per the regex
        assert validate_skill_name("1skill")

    def test_invalid_special_chars(self):
        """Name with special characters is invalid."""
        assert not validate_skill_name("skill!")
        assert not validate_skill_name("skill@name")


class TestUpdateSkillMdName:
    """Tests for update_skill_md_name function."""

    def test_update_existing_name(self, tmp_path):
        """Update existing name field."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_md = skill_dir / SKILL_MARKER
        skill_md.write_text("""---
name: old-name
---

# Content
""")
        update_skill_md_name(skill_dir, "new-name")
        content = skill_md.read_text()
        assert "name: new-name" in content
        assert "old-name" not in content

    def test_add_name_to_frontmatter(self, tmp_path):
        """Add name to existing frontmatter."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_md = skill_dir / SKILL_MARKER
        skill_md.write_text("""---
description: A skill
---

# Content
""")
        update_skill_md_name(skill_dir, "new-name")
        content = skill_md.read_text()
        assert "name: new-name" in content
        assert "description: A skill" in content

    def test_add_frontmatter_if_missing(self, tmp_path):
        """Add frontmatter if missing."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        skill_md = skill_dir / SKILL_MARKER
        skill_md.write_text("# Content only")

        update_skill_md_name(skill_dir, "new-name")
        content = skill_md.read_text()
        assert content.startswith("---")
        assert "name: new-name" in content
        assert "# Content only" in content

    def test_missing_skill_md_does_nothing(self, tmp_path):
        """Missing SKILL.md doesn't raise."""
        skill_dir = tmp_path / "my-skill"
        skill_dir.mkdir()
        # Should not raise
        update_skill_md_name(skill_dir, "new-name")


class TestCreateSkillScaffold:
    """Tests for create_skill_scaffold function."""

    def test_creates_directory(self, tmp_path):
        """Creates skill directory."""
        skill_path = create_skill_scaffold("my-skill", tmp_path)
        assert skill_path.exists()
        assert skill_path.is_dir()
        assert skill_path.name == "my-skill"

    def test_creates_skill_md(self, tmp_path):
        """Creates SKILL.md with scaffold."""
        skill_path = create_skill_scaffold("my-skill", tmp_path)
        skill_md = skill_path / SKILL_MARKER
        assert skill_md.exists()
        content = skill_md.read_text()
        assert "name: my-skill" in content
        assert "# my-skill" in content

    def test_invalid_name_raises(self, tmp_path):
        """Invalid name raises ValueError."""
        with pytest.raises(ValueError, match="Invalid skill name"):
            create_skill_scaffold("-invalid", tmp_path)

    def test_existing_dir_raises(self, tmp_path):
        """Existing directory raises FileExistsError."""
        (tmp_path / "existing").mkdir()
        with pytest.raises(FileExistsError):
            create_skill_scaffold("existing", tmp_path)
