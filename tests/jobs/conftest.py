"""Shared fixtures for Jobs-to-Be-Done test suite."""

from pathlib import Path

import pytest
from typer.testing import CliRunner

from agr.config import AgrConfig, Dependency
from agr.handle import ParsedHandle


runner = CliRunner()


# Note: project_with_git fixture is provided by tests/conftest.py


@pytest.fixture
def project_with_agr_toml(project_with_git: Path):
    """Project with initialized empty agr.toml."""
    config = AgrConfig()
    config.save(project_with_git / "agr.toml")
    return project_with_git


@pytest.fixture
def config_with_remote_deps(project_with_agr_toml: Path):
    """Project with remote dependencies in agr.toml.

    Returns tuple of (project_path, config).
    """
    config = AgrConfig.load(project_with_agr_toml / "agr.toml")
    config.add_remote("kasperjunge/commit", "skill")
    config.add_remote("kasperjunge/review", "command")
    config.add_remote("dsjacobsen/golang-pro", "skill")
    config.save(project_with_agr_toml / "agr.toml")
    return project_with_agr_toml, config


@pytest.fixture
def config_with_local_deps(project_with_agr_toml: Path):
    """Project with local dependencies in agr.toml.

    Creates the local resources and adds them to config.
    Returns tuple of (project_path, config).
    """
    # Create local skill
    skill_dir = project_with_agr_toml / "resources" / "skills" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# My Local Skill")

    # Create local command
    cmd_dir = project_with_agr_toml / "resources" / "commands"
    cmd_dir.mkdir(parents=True)
    (cmd_dir / "deploy.md").write_text("# Deploy Command")

    config = AgrConfig.load(project_with_agr_toml / "agr.toml")
    config.add_local("./resources/skills/my-skill", "skill")
    config.add_local("./resources/commands/deploy.md", "command")
    config.save(project_with_agr_toml / "agr.toml")

    return project_with_agr_toml, config


@pytest.fixture
def config_with_mixed_deps(project_with_agr_toml: Path):
    """Project with both remote and local dependencies.

    Returns tuple of (project_path, config).
    """
    # Create local skill
    skill_dir = project_with_agr_toml / "resources" / "skills" / "local-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# Local Skill")

    config = AgrConfig.load(project_with_agr_toml / "agr.toml")
    config.add_remote("kasperjunge/commit", "skill")
    config.add_local("./resources/skills/local-skill", "skill")
    config.save(project_with_agr_toml / "agr.toml")

    return project_with_agr_toml, config


# ============================================================================
# Installed Resource Fixtures (using ParsedHandle)
# ============================================================================


@pytest.fixture
def installed_skill(project_with_git: Path):
    """Project with a skill installed in .claude/skills/ using ParsedHandle.

    Returns tuple of (project_path, skill_path).
    """
    handle = ParsedHandle.from_components("testuser", "test-skill")
    skill_path = handle.to_skill_path(project_with_git / ".claude")
    skill_path.mkdir(parents=True)
    (skill_path / "SKILL.md").write_text("# Test Skill\n\nA test skill.")
    return project_with_git, skill_path


@pytest.fixture
def installed_command(project_with_git: Path):
    """Project with a command installed in .claude/commands/ using ParsedHandle.

    Returns tuple of (project_path, command_path).
    """
    handle = ParsedHandle.from_components("testuser", "test-command")
    command_path = handle.to_command_path(project_with_git / ".claude")
    command_path.parent.mkdir(parents=True, exist_ok=True)
    command_path.write_text("# Test Command\n\nA test command.")
    return project_with_git, command_path


@pytest.fixture
def installed_agent(project_with_git: Path):
    """Project with an agent installed in .claude/agents/ using ParsedHandle.

    Returns tuple of (project_path, agent_path).
    """
    handle = ParsedHandle.from_components("testuser", "test-agent")
    agent_path = handle.to_agent_path(project_with_git / ".claude")
    agent_path.parent.mkdir(parents=True, exist_ok=True)
    agent_path.write_text("# Test Agent\n\nA test agent.")
    return project_with_git, agent_path


@pytest.fixture
def installed_nested_skill(project_with_git: Path):
    """Project with a nested skill (e.g., product-strategy/flywheel).

    Returns tuple of (project_path, skill_path).
    """
    handle = ParsedHandle.from_components(
        "kasperjunge",
        "flywheel",
        path_segments=["product-strategy", "flywheel"]
    )
    skill_path = handle.to_skill_path(project_with_git / ".claude")
    skill_path.mkdir(parents=True)
    (skill_path / "SKILL.md").write_text("# Flywheel Skill\n\nNested skill.")
    return project_with_git, skill_path


# ============================================================================
# Full Setup Fixtures (config + installed)
# ============================================================================


@pytest.fixture
def project_with_installed_deps(project_with_agr_toml: Path):
    """Project with dependencies in agr.toml AND installed in .claude/.

    Returns tuple of (project_path, config).
    """
    config = AgrConfig.load(project_with_agr_toml / "agr.toml")
    config.add_remote("kasperjunge/commit", "skill")
    config.add_remote("alice/helper", "command")
    config.save(project_with_agr_toml / "agr.toml")

    # Install the skill
    handle = ParsedHandle.from_components("kasperjunge", "commit")
    skill_path = handle.to_skill_path(project_with_agr_toml / ".claude")
    skill_path.mkdir(parents=True)
    (skill_path / "SKILL.md").write_text("# Commit Skill")

    # Install the command
    handle = ParsedHandle.from_components("alice", "helper")
    cmd_path = handle.to_command_path(project_with_agr_toml / ".claude")
    cmd_path.parent.mkdir(parents=True, exist_ok=True)
    cmd_path.write_text("# Helper Command")

    return project_with_agr_toml, config


@pytest.fixture
def project_with_partial_install(project_with_agr_toml: Path):
    """Project with dependencies where some are installed, some are not.

    Returns tuple of (project_path, config, installed_handles, missing_handles).
    """
    config = AgrConfig.load(project_with_agr_toml / "agr.toml")
    config.add_remote("kasperjunge/commit", "skill")
    config.add_remote("kasperjunge/missing", "skill")
    config.add_remote("alice/installed", "command")
    config.save(project_with_agr_toml / "agr.toml")

    # Install only some resources
    handle = ParsedHandle.from_components("kasperjunge", "commit")
    skill_path = handle.to_skill_path(project_with_agr_toml / ".claude")
    skill_path.mkdir(parents=True)
    (skill_path / "SKILL.md").write_text("# Commit Skill")

    handle = ParsedHandle.from_components("alice", "installed")
    cmd_path = handle.to_command_path(project_with_agr_toml / ".claude")
    cmd_path.parent.mkdir(parents=True, exist_ok=True)
    cmd_path.write_text("# Installed Command")

    installed = ["kasperjunge/commit", "alice/installed"]
    missing = ["kasperjunge/missing"]

    return project_with_agr_toml, config, installed, missing


# ============================================================================
# Local Resource Fixtures (for authoring workflow)
# ============================================================================


@pytest.fixture
def local_skill(project_with_git: Path):
    """Project with a local skill in resources/skills/.

    Returns tuple of (project_path, skill_dir).
    """
    skill_dir = project_with_git / "resources" / "skills" / "my-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("# My Local Skill\n\nA locally authored skill.")
    return project_with_git, skill_dir


@pytest.fixture
def local_command(project_with_git: Path):
    """Project with a local command in resources/commands/.

    Returns tuple of (project_path, command_file).
    """
    cmd_dir = project_with_git / "resources" / "commands"
    cmd_dir.mkdir(parents=True)
    cmd_file = cmd_dir / "deploy.md"
    cmd_file.write_text("# Deploy Command\n\nDeploy to production.")
    return project_with_git, cmd_file


@pytest.fixture
def local_agent(project_with_git: Path):
    """Project with a local agent in resources/agents/.

    Returns tuple of (project_path, agent_file).
    """
    agent_dir = project_with_git / "resources" / "agents"
    agent_dir.mkdir(parents=True)
    agent_file = agent_dir / "reviewer.md"
    agent_file.write_text("# Reviewer Agent\n\nReviews code.")
    return project_with_git, agent_file


@pytest.fixture
def local_package(project_with_git: Path):
    """Project with a local package in resources/packages/.

    Returns tuple of (project_path, package_dir).
    """
    pkg_dir = project_with_git / "resources" / "packages" / "my-toolkit"
    (pkg_dir / "skills" / "tool-a").mkdir(parents=True)
    (pkg_dir / "skills" / "tool-a" / "SKILL.md").write_text("# Tool A Skill")
    (pkg_dir / "commands").mkdir(parents=True)
    (pkg_dir / "commands" / "build.md").write_text("# Build Command")
    return project_with_git, pkg_dir


# ============================================================================
# Workspace Fixtures
# ============================================================================


@pytest.fixture
def config_with_workspace(project_with_agr_toml: Path):
    """Project with workspace package containing dependencies.

    Returns tuple of (project_path, config).
    """
    config = AgrConfig.load(project_with_agr_toml / "agr.toml")

    # Add to main dependencies
    config.add_remote("kasperjunge/commit", "skill")

    # Add to workspace
    dep = Dependency(path="./resources/skills/workspace-skill", type="skill")
    config.add_to_workspace("my-workspace", dep)

    config.save(project_with_agr_toml / "agr.toml")
    return project_with_agr_toml, config


# ============================================================================
# Global Install Fixtures
# ============================================================================


@pytest.fixture
def mock_global_claude_dir(tmp_path: Path, monkeypatch):
    """Mock ~/.claude/ directory for global installation tests.

    Returns the mock global .claude path.
    """
    global_claude = tmp_path / ".claude"
    global_claude.mkdir()

    # Mock Path.home() to return our tmp_path
    monkeypatch.setattr(Path, "home", lambda: tmp_path)

    return global_claude
