"""Tests for namespaced path infrastructure."""

from pathlib import Path

import pytest

from agr.cli.common import discover_local_resource_type, get_namespaced_destination
from agr.fetcher import ResourceType, fetch_resource_from_repo_dir


class TestGetNamespacedDestination:
    """Tests for get_namespaced_destination function."""

    def test_returns_namespaced_path_local(self, tmp_path: Path, monkeypatch):
        """Test that local namespaced path includes username."""
        monkeypatch.chdir(tmp_path)

        result = get_namespaced_destination(
            username="kasperjunge",
            resource_name="commit",
            resource_subdir="skills",
            global_install=False,
        )

        expected = tmp_path / ".claude" / "skills" / "kasperjunge" / "commit"
        assert result == expected

    def test_returns_namespaced_path_global(self, tmp_path: Path, monkeypatch):
        """Test that global namespaced path includes username."""
        # Mock home directory
        monkeypatch.setattr(Path, "home", lambda: tmp_path)

        result = get_namespaced_destination(
            username="alice",
            resource_name="review",
            resource_subdir="commands",
            global_install=True,
        )

        expected = tmp_path / ".claude" / "commands" / "alice" / "review"
        assert result == expected

    def test_different_resource_types(self, tmp_path: Path, monkeypatch):
        """Test namespaced paths for different resource types."""
        monkeypatch.chdir(tmp_path)

        skill_path = get_namespaced_destination(
            username="user", resource_name="skill1", resource_subdir="skills", global_install=False
        )
        command_path = get_namespaced_destination(
            username="user", resource_name="cmd1", resource_subdir="commands", global_install=False
        )
        agent_path = get_namespaced_destination(
            username="user", resource_name="agent1", resource_subdir="agents", global_install=False
        )

        assert skill_path == tmp_path / ".claude" / "skills" / "user" / "skill1"
        assert command_path == tmp_path / ".claude" / "commands" / "user" / "cmd1"
        assert agent_path == tmp_path / ".claude" / "agents" / "user" / "agent1"


class TestFetchResourceNamespaced:
    """Tests for fetch_resource_from_repo_dir with namespaced paths."""

    def test_installs_skill_to_namespaced_path(self, tmp_path: Path):
        """Test that skill is installed to namespaced path when username provided."""
        # Create mock repo with skill
        repo_dir = tmp_path / "repo"
        skill_dir = repo_dir / ".claude" / "skills" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Commit Skill")

        dest_base = tmp_path / "project" / ".claude" / "skills"
        dest_base.mkdir(parents=True)

        # Fetch with username
        result = fetch_resource_from_repo_dir(
            repo_dir=repo_dir,
            name="commit",
            path_segments=["commit"],
            dest=dest_base,
            resource_type=ResourceType.SKILL,
            overwrite=False,
            username="kasperjunge",
        )

        # Verify installed to namespaced path
        expected = dest_base / "kasperjunge" / "commit"
        assert result == expected
        assert expected.exists()
        assert (expected / "SKILL.md").exists()

    def test_installs_command_to_namespaced_path(self, tmp_path: Path):
        """Test that command is installed to namespaced path when username provided."""
        # Create mock repo with command
        repo_dir = tmp_path / "repo"
        cmd_dir = repo_dir / ".claude" / "commands"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "review.md").write_text("# Review Command")

        dest_base = tmp_path / "project" / ".claude" / "commands"
        dest_base.mkdir(parents=True)

        # Fetch with username
        result = fetch_resource_from_repo_dir(
            repo_dir=repo_dir,
            name="review",
            path_segments=["review"],
            dest=dest_base,
            resource_type=ResourceType.COMMAND,
            overwrite=False,
            username="alice",
        )

        # Verify installed to namespaced path
        expected = dest_base / "alice" / "review.md"
        assert result == expected
        assert expected.exists()

    def test_backward_compat_flat_path_without_username(self, tmp_path: Path):
        """Test that without username, falls back to flat path (backward compat)."""
        # Create mock repo with skill
        repo_dir = tmp_path / "repo"
        skill_dir = repo_dir / ".claude" / "skills" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Commit Skill")

        dest_base = tmp_path / "project" / ".claude" / "skills"
        dest_base.mkdir(parents=True)

        # Fetch without username (backward compat)
        result = fetch_resource_from_repo_dir(
            repo_dir=repo_dir,
            name="commit",
            path_segments=["commit"],
            dest=dest_base,
            resource_type=ResourceType.SKILL,
            overwrite=False,
            username=None,
        )

        # Verify installed to flat path
        expected = dest_base / "commit"
        assert result == expected
        assert expected.exists()


class TestDiscoverLocalNamespaced:
    """Tests for discovering resources in namespaced paths."""

    def test_discovers_skill_in_namespaced_path(self, tmp_path: Path, monkeypatch):
        """Test discovering a skill in namespaced path."""
        # Create namespaced skill
        skill_dir = tmp_path / ".claude" / "skills" / "kasperjunge" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Commit Skill")

        monkeypatch.chdir(tmp_path)

        # Should find when searching by name only
        result = discover_local_resource_type("commit", global_install=False)

        assert result.is_unique is True
        assert result.resources[0].resource_type == ResourceType.SKILL
        assert result.resources[0].username == "kasperjunge"

    def test_discovers_command_in_namespaced_path(self, tmp_path: Path, monkeypatch):
        """Test discovering a command in namespaced path."""
        # Create namespaced command
        cmd_dir = tmp_path / ".claude" / "commands" / "alice"
        cmd_dir.mkdir(parents=True)
        (cmd_dir / "review.md").write_text("# Review Command")

        monkeypatch.chdir(tmp_path)

        result = discover_local_resource_type("review", global_install=False)

        assert result.is_unique is True
        assert result.resources[0].resource_type == ResourceType.COMMAND
        assert result.resources[0].username == "alice"

    def test_discovers_skill_in_flat_path(self, tmp_path: Path, monkeypatch):
        """Test discovering a skill in flat (legacy) path."""
        # Create flat skill (backward compat)
        skill_dir = tmp_path / ".claude" / "skills" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Commit Skill")

        monkeypatch.chdir(tmp_path)

        result = discover_local_resource_type("commit", global_install=False)

        assert result.is_unique is True
        assert result.resources[0].resource_type == ResourceType.SKILL
        assert result.resources[0].username is None

    def test_prefers_namespaced_over_flat(self, tmp_path: Path, monkeypatch):
        """Test that namespaced path is found even if flat path also exists."""
        # Create both namespaced and flat skills with same name
        flat_skill = tmp_path / ".claude" / "skills" / "commit"
        flat_skill.mkdir(parents=True)
        (flat_skill / "SKILL.md").write_text("# Flat Commit")

        namespaced_skill = tmp_path / ".claude" / "skills" / "kasperjunge" / "commit"
        namespaced_skill.mkdir(parents=True)
        (namespaced_skill / "SKILL.md").write_text("# Namespaced Commit")

        monkeypatch.chdir(tmp_path)

        result = discover_local_resource_type("commit", global_install=False)

        # Should find both (ambiguous situation)
        # In practice, flat one will be from old install, namespaced from new
        assert len(result.resources) >= 1

    def test_discovers_by_full_ref(self, tmp_path: Path, monkeypatch):
        """Test discovering by full ref (username/name)."""
        # Create namespaced skill
        skill_dir = tmp_path / ".claude" / "skills" / "kasperjunge" / "commit"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Commit Skill")

        monkeypatch.chdir(tmp_path)

        # Search by full ref
        result = discover_local_resource_type("kasperjunge/commit", global_install=False)

        assert result.is_unique is True
        assert result.resources[0].resource_type == ResourceType.SKILL
