"""Tests for agr-support skill structure and content."""

import pytest
from pathlib import Path
import yaml


# Get the path to the agr-support skill
# Path: tests -> agr -> src -> agent-resources (4 levels up)
SKILL_PATH = Path(__file__).parent.parent.parent.parent / "skills" / "agr-support"


class TestSkillStructure:
    """Tests for agr-support skill directory structure."""

    def test_skill_directory_exists(self):
        """Test that the skill directory exists."""
        assert SKILL_PATH.exists(), f"Skill directory not found at {SKILL_PATH}"
        assert SKILL_PATH.is_dir()

    def test_skill_md_exists(self):
        """Test that SKILL.md exists."""
        skill_md = SKILL_PATH / "SKILL.md"
        assert skill_md.exists(), "SKILL.md not found"

    def test_references_directory_exists(self):
        """Test that references directory exists."""
        refs_dir = SKILL_PATH / "references"
        assert refs_dir.exists(), "references/ directory not found"
        assert refs_dir.is_dir()

    def test_commands_reference_exists(self):
        """Test that commands.md reference exists."""
        commands_md = SKILL_PATH / "references" / "commands.md"
        assert commands_md.exists(), "references/commands.md not found"

    def test_workflows_reference_exists(self):
        """Test that workflows.md reference exists."""
        workflows_md = SKILL_PATH / "references" / "workflows.md"
        assert workflows_md.exists(), "references/workflows.md not found"

    def test_troubleshooting_reference_exists(self):
        """Test that troubleshooting.md reference exists."""
        troubleshooting_md = SKILL_PATH / "references" / "troubleshooting.md"
        assert troubleshooting_md.exists(), "references/troubleshooting.md not found"


class TestSkillFrontmatter:
    """Tests for SKILL.md frontmatter."""

    @pytest.fixture
    def skill_content(self):
        """Read SKILL.md content."""
        skill_md = SKILL_PATH / "SKILL.md"
        return skill_md.read_text()

    @pytest.fixture
    def frontmatter(self, skill_content):
        """Parse frontmatter from SKILL.md."""
        # Extract frontmatter between --- markers
        lines = skill_content.split("\n")
        if lines[0] != "---":
            pytest.fail("SKILL.md must start with ---")

        end_idx = None
        for i, line in enumerate(lines[1:], 1):
            if line == "---":
                end_idx = i
                break

        if end_idx is None:
            pytest.fail("SKILL.md frontmatter not closed with ---")

        frontmatter_text = "\n".join(lines[1:end_idx])
        return yaml.safe_load(frontmatter_text)

    def test_has_name_field(self, frontmatter):
        """Test that frontmatter has name field."""
        assert "name" in frontmatter, "Frontmatter must have 'name' field"
        assert frontmatter["name"] == "agr-support"

    def test_has_description_field(self, frontmatter):
        """Test that frontmatter has description field."""
        assert "description" in frontmatter, "Frontmatter must have 'description' field"
        assert len(frontmatter["description"]) > 50, "Description should be comprehensive"

    def test_description_mentions_agr(self, frontmatter):
        """Test that description mentions agr/agrx."""
        desc = frontmatter["description"].lower()
        assert "agr" in desc, "Description should mention agr"

    def test_description_includes_use_cases(self, frontmatter):
        """Test that description includes when to use the skill."""
        desc = frontmatter["description"].lower()
        # Should mention at least some of these use cases
        use_cases = ["install", "sync", "authoring", "troubleshoot", "dependency"]
        matches = sum(1 for uc in use_cases if uc in desc)
        assert matches >= 2, "Description should mention use cases (install, sync, etc.)"


class TestSkillContent:
    """Tests for SKILL.md body content."""

    @pytest.fixture
    def skill_content(self):
        """Read SKILL.md content."""
        skill_md = SKILL_PATH / "SKILL.md"
        return skill_md.read_text()

    def test_has_response_format_section(self, skill_content):
        """Test that skill includes response format guidance."""
        assert "response format" in skill_content.lower() or "format" in skill_content.lower()

    def test_has_scope_section(self, skill_content):
        """Test that skill defines scope."""
        assert "scope" in skill_content.lower()
        assert "in scope" in skill_content.lower() or "out of scope" in skill_content.lower()

    def test_has_example_qa(self, skill_content):
        """Test that skill includes example Q&A."""
        # Should have at least a few example questions
        assert "example" in skill_content.lower()
        # Check for example patterns
        assert "how do i" in skill_content.lower() or "what" in skill_content.lower()

    def test_references_reference_files(self, skill_content):
        """Test that SKILL.md references the reference files."""
        assert "references/commands.md" in skill_content or "commands.md" in skill_content
        assert "references/workflows.md" in skill_content or "workflows.md" in skill_content
        assert "references/troubleshooting.md" in skill_content or "troubleshooting.md" in skill_content


class TestReferenceContent:
    """Tests for reference file content."""

    def test_commands_md_has_agr_add(self):
        """Test that commands.md documents agr add."""
        content = (SKILL_PATH / "references" / "commands.md").read_text()
        assert "agr add" in content
        assert "--type" in content or "-t" in content
        assert "--global" in content or "-g" in content

    def test_commands_md_has_agr_sync(self):
        """Test that commands.md documents agr sync."""
        content = (SKILL_PATH / "references" / "commands.md").read_text()
        assert "agr sync" in content
        assert "--prune" in content
        assert "--local" in content
        assert "--remote" in content

    def test_commands_md_has_agrx(self):
        """Test that commands.md documents agrx."""
        content = (SKILL_PATH / "references" / "commands.md").read_text()
        assert "agrx" in content

    def test_commands_md_has_agr_init(self):
        """Test that commands.md documents agr init."""
        content = (SKILL_PATH / "references" / "commands.md").read_text()
        assert "agr init" in content
        assert "init repo" in content or "agr init repo" in content
        assert "init skill" in content or "agr init skill" in content

    def test_workflows_md_has_installation(self):
        """Test that workflows.md has installation workflow."""
        content = (SKILL_PATH / "references" / "workflows.md").read_text()
        assert "install" in content.lower()

    def test_workflows_md_has_local_authoring(self):
        """Test that workflows.md has local authoring workflow."""
        content = (SKILL_PATH / "references" / "workflows.md").read_text()
        assert "local authoring" in content.lower() or "authoring" in content.lower()
        assert "agr sync" in content

    def test_workflows_md_has_dependency_management(self):
        """Test that workflows.md has dependency management workflow."""
        content = (SKILL_PATH / "references" / "workflows.md").read_text()
        assert "agr.toml" in content
        assert "dependencies" in content.lower() or "dependency" in content.lower()

    def test_troubleshooting_md_has_common_errors(self):
        """Test that troubleshooting.md covers common errors."""
        content = (SKILL_PATH / "references" / "troubleshooting.md").read_text()
        # Should cover these common issues
        assert "not found" in content.lower()
        assert "already exists" in content.lower()
        assert "--type" in content  # Disambiguation solution
        assert "agr.toml" in content

    def test_troubleshooting_md_has_solutions(self):
        """Test that troubleshooting.md provides solutions."""
        content = (SKILL_PATH / "references" / "troubleshooting.md").read_text()
        assert "solution" in content.lower()
