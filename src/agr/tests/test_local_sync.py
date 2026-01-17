"""Unit tests for local resource sync functionality."""

import pytest
from pathlib import Path

from agr.discovery import (
    LocalResource,
    LocalPackage,
    DiscoveryContext,
)
from agr.local_sync import (
    SyncResult,
    sync_local_resources,
    _should_update,
    _get_dest_path,
)
from agr.fetcher import ResourceType


class TestSyncResult:
    """Tests for SyncResult dataclass."""

    def test_creates_sync_result(self):
        """Test creating a SyncResult."""
        result = SyncResult(
            installed=["skill-a", "skill-b"],
            updated=["skill-c"],
            removed=[],
            errors=[],
        )
        assert len(result.installed) == 2
        assert len(result.updated) == 1
        assert result.total_synced == 3

    def test_total_synced_property(self):
        """Test total_synced includes installed and updated."""
        result = SyncResult(
            installed=["a"],
            updated=["b", "c"],
            removed=[],
            errors=[],
        )
        assert result.total_synced == 3

    def test_has_errors_property(self):
        """Test has_errors property."""
        result = SyncResult(
            installed=[],
            updated=[],
            removed=[],
            errors=[("skill-x", "Failed to copy")],
        )
        assert result.has_errors is True

        result2 = SyncResult(
            installed=["a"],
            updated=[],
            removed=[],
            errors=[],
        )
        assert result2.has_errors is False


class TestGetDestPath:
    """Tests for _get_dest_path helper function."""

    def test_skill_path_without_package(self, tmp_path):
        """Test destination path for skill without package."""
        resource = LocalResource(
            name="my-skill",
            resource_type=ResourceType.SKILL,
            source_path=Path("skills/my-skill"),
        )
        dest = _get_dest_path(resource, "kasperjunge", tmp_path)
        assert dest == tmp_path / "skills" / "kasperjunge" / "my-skill"

    def test_skill_path_with_package(self, tmp_path):
        """Test destination path for skill within package."""
        resource = LocalResource(
            name="toolkit-skill",
            resource_type=ResourceType.SKILL,
            source_path=Path("packages/my-toolkit/skills/toolkit-skill"),
            package_name="my-toolkit",
        )
        dest = _get_dest_path(resource, "kasperjunge", tmp_path)
        assert dest == tmp_path / "skills" / "kasperjunge" / "my-toolkit" / "toolkit-skill"

    def test_command_path_without_package(self, tmp_path):
        """Test destination path for command without package."""
        resource = LocalResource(
            name="quick-fix",
            resource_type=ResourceType.COMMAND,
            source_path=Path("commands/quick-fix.md"),
        )
        dest = _get_dest_path(resource, "kasperjunge", tmp_path)
        assert dest == tmp_path / "commands" / "kasperjunge" / "quick-fix.md"

    def test_agent_path_without_package(self, tmp_path):
        """Test destination path for agent without package."""
        resource = LocalResource(
            name="reviewer",
            resource_type=ResourceType.AGENT,
            source_path=Path("agents/reviewer.md"),
        )
        dest = _get_dest_path(resource, "kasperjunge", tmp_path)
        assert dest == tmp_path / "agents" / "kasperjunge" / "reviewer.md"


class TestShouldUpdate:
    """Tests for _should_update helper function."""

    def test_returns_true_when_dest_missing(self, tmp_path):
        """Test returns True when destination doesn't exist."""
        source = tmp_path / "source.md"
        source.write_text("content")
        dest = tmp_path / "dest.md"
        assert _should_update(source, dest) is True

    def test_returns_true_when_source_newer(self, tmp_path):
        """Test returns True when source is newer than dest."""
        import time

        dest = tmp_path / "dest.md"
        dest.write_text("old content")

        time.sleep(0.1)  # Ensure different mtime

        source = tmp_path / "source.md"
        source.write_text("new content")

        assert _should_update(source, dest) is True

    def test_returns_false_when_dest_newer(self, tmp_path):
        """Test returns False when dest is newer than source."""
        import time

        source = tmp_path / "source.md"
        source.write_text("old content")

        time.sleep(0.1)

        dest = tmp_path / "dest.md"
        dest.write_text("newer content")

        assert _should_update(source, dest) is False


class TestSyncLocalResources:
    """Tests for sync_local_resources function."""

    def test_syncs_single_skill(self, tmp_path):
        """Test syncing a single skill."""
        # Create source skill
        source_skill = tmp_path / "skills" / "my-skill"
        source_skill.mkdir(parents=True)
        (source_skill / "SKILL.md").write_text("# My Skill")

        # Create discovery context
        context = DiscoveryContext(
            skills=[
                LocalResource(
                    name="my-skill",
                    resource_type=ResourceType.SKILL,
                    source_path=Path("skills/my-skill"),
                )
            ],
            commands=[],
            agents=[],
            packages=[],
        )

        # Create .claude directory
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        result = sync_local_resources(
            context=context,
            username="testuser",
            base_path=claude_dir,
            root_path=tmp_path,
        )

        assert len(result.installed) == 1
        assert "my-skill" in result.installed
        assert (claude_dir / "skills" / "testuser" / "my-skill" / "SKILL.md").exists()

    def test_syncs_single_command(self, tmp_path):
        """Test syncing a single command."""
        # Create source command
        commands_dir = tmp_path / "commands"
        commands_dir.mkdir()
        (commands_dir / "quick-fix.md").write_text("# Quick Fix")

        context = DiscoveryContext(
            skills=[],
            commands=[
                LocalResource(
                    name="quick-fix",
                    resource_type=ResourceType.COMMAND,
                    source_path=Path("commands/quick-fix.md"),
                )
            ],
            agents=[],
            packages=[],
        )

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        result = sync_local_resources(
            context=context,
            username="testuser",
            base_path=claude_dir,
            root_path=tmp_path,
        )

        assert len(result.installed) == 1
        assert (claude_dir / "commands" / "testuser" / "quick-fix.md").exists()

    def test_syncs_package_resources(self, tmp_path):
        """Test syncing resources from a package."""
        # Create package with skill and command
        pkg_skill = tmp_path / "packages" / "my-toolkit" / "skills" / "toolkit-skill"
        pkg_skill.mkdir(parents=True)
        (pkg_skill / "SKILL.md").write_text("# Toolkit Skill")

        pkg_cmd = tmp_path / "packages" / "my-toolkit" / "commands"
        pkg_cmd.mkdir(parents=True)
        (pkg_cmd / "toolkit-cmd.md").write_text("# Toolkit Command")

        skill_resource = LocalResource(
            name="toolkit-skill",
            resource_type=ResourceType.SKILL,
            source_path=Path("packages/my-toolkit/skills/toolkit-skill"),
            package_name="my-toolkit",
        )
        cmd_resource = LocalResource(
            name="toolkit-cmd",
            resource_type=ResourceType.COMMAND,
            source_path=Path("packages/my-toolkit/commands/toolkit-cmd.md"),
            package_name="my-toolkit",
        )

        context = DiscoveryContext(
            skills=[],
            commands=[],
            agents=[],
            packages=[
                LocalPackage(
                    name="my-toolkit",
                    path=Path("packages/my-toolkit"),
                    resources=[skill_resource, cmd_resource],
                )
            ],
        )

        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        result = sync_local_resources(
            context=context,
            username="testuser",
            base_path=claude_dir,
            root_path=tmp_path,
        )

        assert len(result.installed) == 2
        # Check namespaced package paths
        assert (claude_dir / "skills" / "testuser" / "my-toolkit" / "toolkit-skill" / "SKILL.md").exists()
        assert (claude_dir / "commands" / "testuser" / "my-toolkit" / "toolkit-cmd.md").exists()

    def test_updates_existing_resource(self, tmp_path):
        """Test updating an existing resource when source is newer."""
        import time

        # Create existing dest
        claude_dir = tmp_path / ".claude"
        dest_skill = claude_dir / "skills" / "testuser" / "my-skill"
        dest_skill.mkdir(parents=True)
        (dest_skill / "SKILL.md").write_text("# Old Content")

        time.sleep(0.1)

        # Create source skill with newer content
        source_skill = tmp_path / "skills" / "my-skill"
        source_skill.mkdir(parents=True)
        (source_skill / "SKILL.md").write_text("# New Content")

        context = DiscoveryContext(
            skills=[
                LocalResource(
                    name="my-skill",
                    resource_type=ResourceType.SKILL,
                    source_path=Path("skills/my-skill"),
                )
            ],
            commands=[],
            agents=[],
            packages=[],
        )

        result = sync_local_resources(
            context=context,
            username="testuser",
            base_path=claude_dir,
            root_path=tmp_path,
        )

        assert len(result.updated) == 1
        assert "my-skill" in result.updated
        content = (dest_skill / "SKILL.md").read_text()
        assert "New Content" in content

    def test_skips_unchanged_resource(self, tmp_path):
        """Test that unchanged resources are skipped."""
        import time

        # Create source skill first
        source_skill = tmp_path / "skills" / "my-skill"
        source_skill.mkdir(parents=True)
        (source_skill / "SKILL.md").write_text("# Same Content")

        time.sleep(0.1)

        # Create dest skill after (newer)
        claude_dir = tmp_path / ".claude"
        dest_skill = claude_dir / "skills" / "testuser" / "my-skill"
        dest_skill.mkdir(parents=True)
        (dest_skill / "SKILL.md").write_text("# Same Content")

        context = DiscoveryContext(
            skills=[
                LocalResource(
                    name="my-skill",
                    resource_type=ResourceType.SKILL,
                    source_path=Path("skills/my-skill"),
                )
            ],
            commands=[],
            agents=[],
            packages=[],
        )

        result = sync_local_resources(
            context=context,
            username="testuser",
            base_path=claude_dir,
            root_path=tmp_path,
        )

        assert len(result.installed) == 0
        assert len(result.updated) == 0

    def test_prune_removes_unlisted_resources(self, tmp_path):
        """Test that prune removes resources not in context."""
        # Create orphaned resource in .claude
        claude_dir = tmp_path / ".claude"
        orphan_skill = claude_dir / "skills" / "testuser" / "orphan-skill"
        orphan_skill.mkdir(parents=True)
        (orphan_skill / "SKILL.md").write_text("# Orphan")

        # Empty context - no local resources
        context = DiscoveryContext(
            skills=[],
            commands=[],
            agents=[],
            packages=[],
        )

        result = sync_local_resources(
            context=context,
            username="testuser",
            base_path=claude_dir,
            root_path=tmp_path,
            prune=True,
        )

        assert len(result.removed) == 1
        assert "orphan-skill" in result.removed
        assert not orphan_skill.exists()

    def test_empty_context_no_changes(self, tmp_path):
        """Test that empty context produces no changes."""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()

        context = DiscoveryContext(
            skills=[],
            commands=[],
            agents=[],
            packages=[],
        )

        result = sync_local_resources(
            context=context,
            username="testuser",
            base_path=claude_dir,
            root_path=tmp_path,
        )

        assert len(result.installed) == 0
        assert len(result.updated) == 0
        assert len(result.removed) == 0
        assert len(result.errors) == 0
