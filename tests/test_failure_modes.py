"""Tests for failure modes and error handling."""

import os
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agr.cli.main import app


runner = CliRunner()


class TestNetworkFailures:
    """Tests for network-related failure handling."""

    def test_add_nonexistent_user_produces_error(self, git_project: Path):
        """Test that adding from nonexistent user produces error."""
        result = runner.invoke(app, ["add", "zzznonexistentuser12345xyz/resource"])

        # Should fail - either network error or resolution error
        assert result.exit_code != 0

    def test_add_invalid_handle_format_produces_error(self, git_project: Path):
        """Test that invalid handle format produces error."""
        result = runner.invoke(app, ["add", "///invalid///handle///"])

        assert result.exit_code != 0

    def test_add_empty_handle_produces_error(self, git_project: Path):
        """Test that empty handle produces error."""
        result = runner.invoke(app, ["add", ""])

        assert result.exit_code != 0

    def test_add_whitespace_handle_produces_error(self, git_project: Path):
        """Test that whitespace-only handle produces error."""
        result = runner.invoke(app, ["add", "   "])

        assert result.exit_code != 0

    def test_add_special_chars_in_handle_produces_error(self, git_project: Path):
        """Test that special characters in handle produce error."""
        result = runner.invoke(app, ["add", "user/name!@#$%"])

        assert result.exit_code != 0

    def test_add_very_long_handle_produces_error(self, git_project: Path):
        """Test that very long handle produces error."""
        long_name = "a" * 500
        result = runner.invoke(app, ["add", f"user/{long_name}"])

        assert result.exit_code != 0


# ============================================================================
# Filesystem Failure Tests
# ============================================================================


class TestFilesystemFailures:
    """Tests for filesystem-related failure handling."""

    def test_permission_denied_installing_skill(self, git_project: Path):
        """Test handling permission denied when installing."""
        # Create a read-only directory
        claude_dir = git_project / ".claude"
        claude_dir.mkdir()
        os.chmod(claude_dir, 0o444)

        try:
            result = runner.invoke(app, ["add", "./test-skill", "--type", "skill"])
            # Should handle permission error gracefully
            # Note: This may pass on some systems with elevated privileges
        finally:
            os.chmod(claude_dir, 0o755)

    def test_missing_source_file(self, git_project: Path):
        """Test handling missing source file."""
        result = runner.invoke(app, ["add", "./nonexistent/path"])

        assert result.exit_code != 0
        assert "not found" in result.output.lower() or "does not exist" in result.output.lower() or "no such" in result.output.lower()

    def test_add_file_instead_of_directory(self, git_project: Path):
        """Test handling when file given instead of expected directory."""
        (git_project / "test.txt").write_text("not a skill")

        result = runner.invoke(app, ["add", "./test.txt", "--type", "skill"])

        # Should fail or produce warning about file not being a skill directory
        # Skills require a directory with SKILL.md

    def test_empty_skill_directory(self, git_project: Path):
        """Test handling empty skill directory (no SKILL.md)."""
        empty_skill = git_project / "empty-skill"
        empty_skill.mkdir()

        result = runner.invoke(app, ["add", "./empty-skill", "--type", "skill"])

        # Should fail with message about missing SKILL.md

    def test_symlink_loop_handled(self, git_project: Path):
        """Test that symlink loops don't cause infinite recursion."""
        # Create a symlink loop
        link_a = git_project / "link_a"
        link_b = git_project / "link_b"

        try:
            link_a.symlink_to(link_b)
            link_b.symlink_to(link_a)

            # Add should handle this gracefully
            result = runner.invoke(app, ["add", "./link_a", "--type", "skill"])
            # Should not hang or crash
        except OSError:
            # Some systems don't allow this
            pass
        finally:
            if link_a.exists():
                link_a.unlink()
            if link_b.exists():
                link_b.unlink()

    def test_binary_file_as_command(self, git_project: Path):
        """Test handling binary file as command."""
        binary_file = git_project / "commands" / "binary.md"
        binary_file.parent.mkdir(parents=True)
        binary_file.write_bytes(b"\x00\x01\x02\x03\x04\x05")

        result = runner.invoke(app, ["add", "./commands/binary.md"])

        # Should handle gracefully (may succeed or fail, but shouldn't crash)


# ============================================================================
# Configuration Failure Tests
# ============================================================================


class TestConfigurationFailures:
    """Tests for configuration-related failure handling."""

    def test_invalid_toml_syntax(self, git_project: Path):
        """Test handling invalid TOML syntax."""
        (git_project / "agr.toml").write_text("""
[[dependencies]
handle = "missing-bracket"
type = "skill"
""")

        result = runner.invoke(app, ["sync"])

        assert result.exit_code != 0

    def test_malformed_handle_format(self, git_project: Path):
        """Test handling malformed handle format."""
        (git_project / "agr.toml").write_text("""
[[dependencies]]
handle = "///invalid//handle///"
type = "skill"
""")

        result = runner.invoke(app, ["sync"])

        # Should handle gracefully with error message

    def test_unknown_resource_type(self, git_project: Path):
        """Test handling unknown resource type in config."""
        (git_project / "agr.toml").write_text("""
[[dependencies]]
handle = "user/resource"
type = "unknown-type"
""")

        result = runner.invoke(app, ["sync"])

        assert result.exit_code != 0

    def test_missing_required_field(self, git_project: Path):
        """Test handling missing required field in config."""
        (git_project / "agr.toml").write_text("""
[[dependencies]]
type = "skill"
""")

        result = runner.invoke(app, ["sync"])

        # Should fail with message about missing handle or path

    def test_duplicate_dependencies(self, git_project: Path):
        """Test handling duplicate dependencies in config."""
        (git_project / "agr.toml").write_text("""
[[dependencies]]
handle = "user/skill"
type = "skill"

[[dependencies]]
handle = "user/skill"
type = "skill"
""")

        result = runner.invoke(app, ["sync"])

        # Should handle duplicates (either warn or dedupe)

    def test_conflicting_path_and_handle(self, git_project: Path):
        """Test handling both path and handle in same dependency."""
        (git_project / "agr.toml").write_text("""
[[dependencies]]
path = "./local/skill"
handle = "user/skill"
type = "skill"
""")

        result = runner.invoke(app, ["sync"])

        # Should prefer one or error about conflict

    def test_invalid_workspace_name(self, git_project: Path):
        """Test handling invalid workspace name."""
        (git_project / "agr.toml").write_text("""
[workspaces."invalid/name"]
dependencies = []
""")

        result = runner.invoke(app, ["sync", "--workspace", "invalid/name"])

        # Should handle gracefully

    def test_circular_workspace_reference(self, git_project: Path):
        """Test handling circular workspace references."""
        # This tests if workspaces can reference each other
        (git_project / "agr.toml").write_text("""
[workspaces.a]
dependencies = []

[workspaces.b]
dependencies = []
""")

        result = runner.invoke(app, ["sync", "--workspace", "a"])
        # Should work fine, no circular reference in this case


# ============================================================================
# Git/Project Failure Tests
# ============================================================================


class TestGitProjectFailures:
    """Tests for Git/project-related failure handling."""

    def test_add_without_git_remote_succeeds_for_local(self, tmp_path: Path, monkeypatch):
        """Test adding local resource works even without git remote."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()

        skill_dir = tmp_path / "skills" / "test"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Test")

        result = runner.invoke(app, ["add", "./skills/test"])
        # Should succeed for local resources
        assert result.exit_code == 0

    def test_corrupted_agr_toml(self, git_project: Path):
        """Test handling corrupted agr.toml file."""
        (git_project / "agr.toml").write_bytes(b"\x00\x01\x02invalid binary")

        result = runner.invoke(app, ["sync"])

        assert result.exit_code != 0

    def test_agr_toml_is_directory(self, git_project: Path):
        """Test handling when agr.toml is actually a directory."""
        (git_project / "agr.toml").mkdir()

        result = runner.invoke(app, ["sync"])

        assert result.exit_code != 0

    def test_read_only_agr_toml(self, git_project: Path):
        """Test handling read-only agr.toml."""
        toml_file = git_project / "agr.toml"
        toml_file.write_text("")
        os.chmod(toml_file, 0o444)

        try:
            skill_dir = git_project / "skills" / "test"
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text("# Test")

            result = runner.invoke(app, ["add", "./skills/test"])
            # May fail if trying to write to agr.toml
        finally:
            os.chmod(toml_file, 0o644)


# ============================================================================
# Archive Failure Tests
# ============================================================================


class TestArchiveFailures:
    """Tests for archive-related failure handling.

    Note: Testing actual archive extraction failures requires network access
    and specific failure scenarios. These tests focus on observable behaviors.
    """

    def test_add_nonexistent_remote_skill_fails(self, git_project: Path):
        """Test that adding a truly nonexistent remote skill fails."""
        # Use a definitely nonexistent handle
        result = runner.invoke(app, ["add", "zzz-no-such-user-xyz/no-such-skill-abc"])

        # Should fail because the resource doesn't exist
        assert result.exit_code != 0

    def test_add_nonexistent_type_in_repo_fails(self, git_project: Path):
        """Test that adding a resource with wrong type produces error."""
        # Try to add a skill that doesn't exist with explicit type
        result = runner.invoke(
            app, ["add", "zzz-no-such-user-xyz/resource", "--type", "skill"]
        )

        assert result.exit_code != 0

    def test_add_local_empty_directory_fails(self, git_project: Path):
        """Test that adding an empty directory fails."""
        empty_dir = git_project / "empty-skill"
        empty_dir.mkdir()

        result = runner.invoke(app, ["add", "./empty-skill", "--type", "skill"])

        # Should fail because no SKILL.md in directory
        assert result.exit_code != 0


# ============================================================================
# Input Validation Tests
# ============================================================================


class TestInputValidation:
    """Tests for input validation and edge cases."""

    def test_unicode_in_handle(self, git_project: Path):
        """Test handling unicode characters in handle."""
        result = runner.invoke(app, ["add", "user/skill-\u00e9\u00e8\u00ea"])

        # Should fail gracefully (GitHub doesn't allow unicode in repo names)
        assert result.exit_code != 0

    def test_null_bytes_in_path(self, git_project: Path):
        """Test handling null bytes in path."""
        result = runner.invoke(app, ["add", "./path/with\x00null"])

        # Should handle gracefully
        assert result.exit_code != 0

    def test_newlines_in_handle(self, git_project: Path):
        """Test handling newlines in handle."""
        result = runner.invoke(app, ["add", "user/skill\nwith\nnewlines"])

        assert result.exit_code != 0

    def test_path_traversal_attempt(self, git_project: Path):
        """Test handling path traversal in local path."""
        result = runner.invoke(app, ["add", "../../../etc/passwd"])

        # Should not allow path traversal
        assert result.exit_code != 0
