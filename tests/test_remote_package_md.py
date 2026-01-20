"""Tests for PACKAGE.md handling in remote resource resolution."""

from pathlib import Path

import pytest

from agr.fetcher import ResourceType
from agr.resolver import (
    ResolvedResource,
    ResourceSource,
    resolve_remote_resource,
    _find_package_context_in_repo,
)
from agr.fetcher.resource import fetch_resource_from_repo_dir


class TestFindPackageContextInRepo:
    """Tests for _find_package_context_in_repo helper function."""

    def test_finds_package_md_in_parent_directory(self, tmp_path: Path):
        """Test finding PACKAGE.md in parent directory of resource."""
        # Create package structure
        pkg_dir = tmp_path / "my-toolkit"
        pkg_dir.mkdir()
        (pkg_dir / "PACKAGE.md").write_text("---\nname: toolkit\n---\n")

        skill_dir = pkg_dir / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        # Resource path is relative to repo_dir
        resource_path = Path("my-toolkit/skills/my-skill")

        result = _find_package_context_in_repo(tmp_path, resource_path)

        assert result == "toolkit"

    def test_finds_package_md_directly_at_resource_parent(self, tmp_path: Path):
        """Test finding PACKAGE.md directly containing the resource."""
        pkg_dir = tmp_path / "pkg"
        pkg_dir.mkdir()
        (pkg_dir / "PACKAGE.md").write_text("---\nname: direct-pkg\n---\n")
        (pkg_dir / "commands").mkdir()
        (pkg_dir / "commands" / "cmd.md").write_text("# Command")

        resource_path = Path("pkg/commands/cmd.md")

        result = _find_package_context_in_repo(tmp_path, resource_path)

        assert result == "direct-pkg"

    def test_returns_none_when_no_package_md(self, tmp_path: Path):
        """Test returning None when no PACKAGE.md exists."""
        skill_dir = tmp_path / "skills" / "standalone"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Standalone")

        resource_path = Path("skills/standalone")

        result = _find_package_context_in_repo(tmp_path, resource_path)

        assert result is None

    def test_respects_repo_dir_boundary(self, tmp_path: Path):
        """Test that search stops at repo_dir boundary."""
        # Create PACKAGE.md outside repo_dir (should be ignored)
        (tmp_path / "PACKAGE.md").write_text("---\nname: outside\n---\n")

        # Create repo directory without PACKAGE.md
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir()
        skill_dir = repo_dir / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Skill")

        resource_path = Path("skills/my-skill")

        result = _find_package_context_in_repo(repo_dir, resource_path)

        # Should not find the PACKAGE.md outside repo_dir
        assert result is None

    def test_returns_none_for_invalid_package_md(self, tmp_path: Path):
        """Test returning None when PACKAGE.md is invalid."""
        pkg_dir = tmp_path / "invalid-pkg"
        pkg_dir.mkdir()
        # Invalid PACKAGE.md (no name field)
        (pkg_dir / "PACKAGE.md").write_text("---\ndescription: Missing name\n---\n")
        skill_dir = pkg_dir / "skills" / "skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Skill")

        resource_path = Path("invalid-pkg/skills/skill")

        result = _find_package_context_in_repo(tmp_path, resource_path)

        assert result is None

    def test_finds_nearest_package_md(self, tmp_path: Path):
        """Test that nearest PACKAGE.md is used when multiple exist."""
        # Create outer package
        outer_pkg = tmp_path / "outer"
        outer_pkg.mkdir()
        (outer_pkg / "PACKAGE.md").write_text("---\nname: outer-pkg\n---\n")

        # Create inner structure (without nested PACKAGE.md per package rules)
        # but the nearest one should be found
        inner = outer_pkg / "subdir"
        inner.mkdir()
        skill_dir = inner / "skills" / "skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Skill")

        resource_path = Path("outer/subdir/skills/skill")

        result = _find_package_context_in_repo(tmp_path, resource_path)

        assert result == "outer-pkg"


class TestResolveRemoteResourceWithPackageContext:
    """Tests for resolve_remote_resource with PACKAGE.md context."""

    def test_resolves_skill_with_package_context_from_agr_toml(self, tmp_path: Path):
        """Test that skill resolved from agr.toml gets package context."""
        # Create agr.toml - note: path format resources/skills/name is expected
        agr_toml = tmp_path / "agr.toml"
        agr_toml.write_text("""
dependencies = [
    {path = "resources/skills/my-skill", type = "skill"},
]
""")

        # Create package with PACKAGE.md containing the skills
        pkg_dir = tmp_path / "resources"
        pkg_dir.mkdir()
        (pkg_dir / "PACKAGE.md").write_text("---\nname: toolkit\n---\n")

        skill_dir = pkg_dir / "skills" / "my-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# My Skill")

        result = resolve_remote_resource(tmp_path, "my-skill")

        assert result is not None
        assert result.source == ResourceSource.AGR_TOML
        assert result.package_name == "toolkit"

    def test_resolves_skill_without_package_context(self, tmp_path: Path):
        """Test that skill without PACKAGE.md has None package_name."""
        # Create agr.toml
        agr_toml = tmp_path / "agr.toml"
        agr_toml.write_text("""
dependencies = [
    {path = "resources/skills/standalone", type = "skill"},
]
""")

        # Create skill without PACKAGE.md
        skill_dir = tmp_path / "resources" / "skills" / "standalone"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Standalone Skill")

        result = resolve_remote_resource(tmp_path, "standalone")

        assert result is not None
        assert result.source == ResourceSource.AGR_TOML
        assert result.package_name is None

    def test_resolves_command_with_package_context_from_claude_dir(self, tmp_path: Path):
        """Test command in .claude/ with PACKAGE.md gets package context."""
        # Create PACKAGE.md at .claude level
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        (claude_dir / "PACKAGE.md").write_text("---\nname: claude-pkg\n---\n")

        commands_dir = claude_dir / "commands"
        commands_dir.mkdir()
        (commands_dir / "my-cmd.md").write_text("# My Command")

        result = resolve_remote_resource(tmp_path, "my-cmd")

        assert result is not None
        assert result.source == ResourceSource.CLAUDE_DIR
        assert result.resource_type == ResourceType.COMMAND
        assert result.package_name == "claude-pkg"

    def test_resolves_skill_with_package_context_from_repo_root(self, tmp_path: Path):
        """Test auto-discovered skill gets package context."""
        # Create package with PACKAGE.md
        pkg_dir = tmp_path / "my-pkg"
        pkg_dir.mkdir()
        (pkg_dir / "PACKAGE.md").write_text("---\nname: discovered-pkg\n---\n")

        skill_dir = pkg_dir / "my-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# My Skill")

        result = resolve_remote_resource(tmp_path, "my-skill")

        assert result is not None
        assert result.source == ResourceSource.REPO_ROOT
        assert result.package_name == "discovered-pkg"

    def test_bundles_have_no_package_context(self, tmp_path: Path):
        """Test that bundles don't inherit package context."""
        # Create bundle structure in .claude/
        bundle_skill = tmp_path / ".claude" / "skills" / "my-bundle" / "bundle-skill"
        bundle_skill.mkdir(parents=True)
        (bundle_skill / "SKILL.md").write_text("# Bundle Skill")

        # Add PACKAGE.md above (should not affect bundle)
        (tmp_path / ".claude" / "PACKAGE.md").write_text("---\nname: should-ignore\n---\n")

        result = resolve_remote_resource(tmp_path, "my-bundle")

        assert result is not None
        assert result.is_package is True
        assert result.package_name is None  # Bundles explicitly have None


class TestFetchResourceWithPackageContext:
    """Tests for fetch_resource_from_repo_dir with package_name."""

    def test_skill_with_package_name_installed_to_namespaced_path(self, tmp_path: Path):
        """Test skill with package_name installs to user:package:skill path."""
        # Create source skill
        repo_dir = tmp_path / "repo"
        skill_source = repo_dir / "pkg" / "skills" / "my-skill"
        skill_source.mkdir(parents=True)
        (skill_source / "SKILL.md").write_text("---\nname: my-skill\n---\n# Skill")

        # Create destination
        dest = tmp_path / "dest" / "skills"
        dest.mkdir(parents=True)

        result_path = fetch_resource_from_repo_dir(
            repo_dir=repo_dir,
            name="my-skill",
            path_segments=["my-skill"],
            dest=dest,
            resource_type=ResourceType.SKILL,
            username="testuser",
            source_path=Path("pkg/skills/my-skill"),
            package_name="toolkit",
        )

        # Should install to dest/testuser:toolkit:my-skill/
        assert result_path == dest / "testuser:toolkit:my-skill"
        assert result_path.exists()
        assert (result_path / "SKILL.md").exists()

        # Verify SKILL.md name was updated
        skill_md_content = (result_path / "SKILL.md").read_text()
        assert "name: testuser:toolkit:my-skill" in skill_md_content

    def test_skill_without_package_name_installed_normally(self, tmp_path: Path):
        """Test skill without package_name installs to user:skill path."""
        # Create source skill
        repo_dir = tmp_path / "repo"
        skill_source = repo_dir / "resources" / "skills" / "standalone"
        skill_source.mkdir(parents=True)
        (skill_source / "SKILL.md").write_text("---\nname: standalone\n---\n# Skill")

        # Create destination
        dest = tmp_path / "dest" / "skills"
        dest.mkdir(parents=True)

        result_path = fetch_resource_from_repo_dir(
            repo_dir=repo_dir,
            name="standalone",
            path_segments=["standalone"],
            dest=dest,
            resource_type=ResourceType.SKILL,
            username="testuser",
            source_path=Path("resources/skills/standalone"),
            package_name=None,
        )

        # Should install to dest/testuser:standalone/
        assert result_path == dest / "testuser:standalone"
        assert result_path.exists()

    def test_command_with_package_name_installed_to_namespaced_path(self, tmp_path: Path):
        """Test command with package_name installs to user/package/cmd.md path."""
        # Create source command
        repo_dir = tmp_path / "repo"
        cmd_source = repo_dir / "pkg" / "commands"
        cmd_source.mkdir(parents=True)
        (cmd_source / "my-cmd.md").write_text("# My Command")

        # Create destination
        dest = tmp_path / "dest" / "commands"
        dest.mkdir(parents=True)

        result_path = fetch_resource_from_repo_dir(
            repo_dir=repo_dir,
            name="my-cmd",
            path_segments=["my-cmd"],
            dest=dest,
            resource_type=ResourceType.COMMAND,
            username="testuser",
            source_path=Path("pkg/commands/my-cmd.md"),
            package_name="my-toolkit",
        )

        # Should install to dest/testuser/my-toolkit/my-cmd.md
        assert result_path == dest / "testuser" / "my-toolkit" / "my-cmd.md"
        assert result_path.exists()

    def test_command_without_package_name_installed_normally(self, tmp_path: Path):
        """Test command without package_name installs to user/cmd.md path."""
        # Create source command
        repo_dir = tmp_path / "repo"
        cmd_source = repo_dir / "resources" / "commands"
        cmd_source.mkdir(parents=True)
        (cmd_source / "standalone.md").write_text("# Standalone")

        # Create destination
        dest = tmp_path / "dest" / "commands"
        dest.mkdir(parents=True)

        result_path = fetch_resource_from_repo_dir(
            repo_dir=repo_dir,
            name="standalone",
            path_segments=["standalone"],
            dest=dest,
            resource_type=ResourceType.COMMAND,
            username="testuser",
            source_path=Path("resources/commands/standalone.md"),
            package_name=None,
        )

        # Should install to dest/testuser/standalone.md
        assert result_path == dest / "testuser" / "standalone.md"
        assert result_path.exists()

    def test_nested_skill_with_package_name(self, tmp_path: Path):
        """Test nested skill with package_name installs correctly."""
        # Create source nested skill
        repo_dir = tmp_path / "repo"
        skill_source = repo_dir / "pkg" / "skills" / "category" / "my-skill"
        skill_source.mkdir(parents=True)
        (skill_source / "SKILL.md").write_text("# Nested Skill")

        # Create destination
        dest = tmp_path / "dest" / "skills"
        dest.mkdir(parents=True)

        result_path = fetch_resource_from_repo_dir(
            repo_dir=repo_dir,
            name="category:my-skill",
            path_segments=["category", "my-skill"],
            dest=dest,
            resource_type=ResourceType.SKILL,
            username="testuser",
            source_path=Path("pkg/skills/category/my-skill"),
            package_name="toolkit",
        )

        # Should install to dest/testuser:toolkit:category:my-skill/
        assert result_path == dest / "testuser:toolkit:category:my-skill"
        assert result_path.exists()


class TestEndToEndRemotePackageResolution:
    """End-to-end tests for remote package resolution chain."""

    def test_full_resolution_to_fetch_chain_with_package(self, tmp_path: Path):
        """Test full chain: resolve resource with package, then fetch."""
        # Setup mock repo structure
        repo_dir = tmp_path / "mock-repo"

        # Create agr.toml - use standard resources/ path that agr understands
        agr_toml = repo_dir / "agr.toml"
        agr_toml.parent.mkdir(parents=True)
        agr_toml.write_text("""
dependencies = [
    {path = "resources/skills/featured-skill", type = "skill"},
]
""")

        # Create package with PACKAGE.md containing the resources
        pkg_dir = repo_dir / "resources"
        pkg_dir.mkdir()
        (pkg_dir / "PACKAGE.md").write_text("---\nname: my-toolkit\n---\n")

        skill_dir = pkg_dir / "skills" / "featured-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Featured Skill")

        # Resolve
        resolved = resolve_remote_resource(repo_dir, "featured-skill")

        assert resolved is not None
        assert resolved.package_name == "my-toolkit"
        assert resolved.source == ResourceSource.AGR_TOML

        # Fetch using resolved info
        dest = tmp_path / "install" / "skills"
        dest.mkdir(parents=True)

        installed_path = fetch_resource_from_repo_dir(
            repo_dir=repo_dir,
            name="featured-skill",
            path_segments=["featured-skill"],
            dest=dest,
            resource_type=resolved.resource_type,
            username="publisher",
            source_path=resolved.path,
            package_name=resolved.package_name,
        )

        # Verify installed to namespaced path with package
        assert installed_path == dest / "publisher:my-toolkit:featured-skill"
        assert installed_path.exists()
        assert (installed_path / "SKILL.md").exists()

    def test_full_resolution_to_fetch_chain_without_package(self, tmp_path: Path):
        """Test full chain: resolve resource without package, then fetch."""
        # Setup mock repo structure
        repo_dir = tmp_path / "mock-repo"

        # Create agr.toml
        agr_toml = repo_dir / "agr.toml"
        agr_toml.parent.mkdir(parents=True)
        agr_toml.write_text("""
dependencies = [
    {path = "resources/skills/standalone-skill", type = "skill"},
]
""")

        # Create skill without PACKAGE.md
        skill_dir = repo_dir / "resources" / "skills" / "standalone-skill"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Standalone Skill")

        # Resolve
        resolved = resolve_remote_resource(repo_dir, "standalone-skill")

        assert resolved is not None
        assert resolved.package_name is None
        assert resolved.source == ResourceSource.AGR_TOML

        # Fetch using resolved info
        dest = tmp_path / "install" / "skills"
        dest.mkdir(parents=True)

        installed_path = fetch_resource_from_repo_dir(
            repo_dir=repo_dir,
            name="standalone-skill",
            path_segments=["standalone-skill"],
            dest=dest,
            resource_type=resolved.resource_type,
            username="publisher",
            source_path=resolved.path,
            package_name=resolved.package_name,
        )

        # Verify installed to namespaced path without package
        assert installed_path == dest / "publisher:standalone-skill"
        assert installed_path.exists()
