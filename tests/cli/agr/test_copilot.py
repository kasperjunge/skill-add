"""CLI tests for GitHub Copilot tool support."""

import pytest

from tests.cli.assertions import assert_cli


class TestCopilotAdd:
    """Tests for agr add with Copilot tool."""

    def test_add_local_skill_to_copilot_flat_structure(
        self, agr, cli_project, cli_skill, cli_config
    ):
        """agr add local skill installs to .github/skills/local--<name>/."""
        cli_config('tools = ["copilot"]\ndependencies = []')

        result = agr("add", "./skills/test-skill")

        assert_cli(result).succeeded()
        # Copilot uses flat structure: local--<name>
        installed = cli_project / ".github" / "skills" / "local--test-skill"
        assert installed.exists()
        assert (installed / "SKILL.md").exists()

    @pytest.mark.network
    def test_add_remote_skill_to_copilot_flat_structure(
        self, agr, cli_project, cli_config
    ):
        """agr add remote skill installs to .github/skills/<user>--<repo>--<name>/."""
        cli_config('tools = ["copilot"]\ndependencies = []')

        result = agr("add", "kasperjunge/agent-resources-public-test-repo/test-skill")

        assert_cli(result).succeeded()
        # Copilot uses flat structure: user--repo--skill
        installed = (
            cli_project
            / ".github"
            / "skills"
            / "kasperjunge--agent-resources-public-test-repo--test-skill"
        )
        assert installed.exists()
        assert (installed / "SKILL.md").exists()


class TestCopilotSync:
    """Tests for agr sync with Copilot tool."""

    def test_sync_installs_to_copilot_when_configured(
        self, agr, cli_project, cli_skill, cli_config
    ):
        """agr sync with tools = ["copilot"] installs to correct path."""
        cli_config(
            """
tools = ["copilot"]
dependencies = [
    { path = "./skills/test-skill", type = "skill" },
]
"""
        )

        result = agr("sync")

        assert_cli(result).succeeded()
        installed = cli_project / ".github" / "skills" / "local--test-skill"
        assert installed.exists()

    def test_sync_creates_github_skills_directory(
        self, agr, cli_project, cli_skill, cli_config
    ):
        """agr sync creates .github/skills/ if it doesn't exist."""
        cli_config(
            """
tools = ["copilot"]
dependencies = [
    { path = "./skills/test-skill", type = "skill" },
]
"""
        )
        # Ensure no .github directory exists
        github_dir = cli_project / ".github"
        assert not github_dir.exists()

        result = agr("sync")

        assert_cli(result).succeeded()
        assert github_dir.exists()
        assert (github_dir / "skills" / "local--test-skill").exists()


class TestCopilotRemove:
    """Tests for agr remove with Copilot tool."""

    def test_remove_cleans_up_copilot_flat_structure(
        self, agr, cli_project, cli_skill, cli_config
    ):
        """agr remove removes skill from .github/skills/."""
        cli_config('tools = ["copilot"]\ndependencies = []')
        agr("add", "./skills/test-skill")

        installed = cli_project / ".github" / "skills" / "local--test-skill"
        assert installed.exists()

        result = agr("remove", "./skills/test-skill")

        assert_cli(result).succeeded()
        assert not installed.exists()


class TestMultiToolCopilotClaude:
    """Tests for multi-tool scenarios with Copilot and Claude."""

    def test_add_installs_to_both_claude_and_copilot(
        self, agr, cli_project, cli_skill, cli_config
    ):
        """agr add with tools = ["claude", "copilot"] installs to both."""
        cli_config('tools = ["claude", "copilot"]\ndependencies = []')

        result = agr("add", "./skills/test-skill")

        assert_cli(result).succeeded()

        # Claude uses .claude/skills/
        claude_installed = cli_project / ".claude" / "skills" / "local--test-skill"
        assert claude_installed.exists()
        assert (claude_installed / "SKILL.md").exists()

        # Copilot uses .github/skills/
        copilot_installed = cli_project / ".github" / "skills" / "local--test-skill"
        assert copilot_installed.exists()
        assert (copilot_installed / "SKILL.md").exists()

    def test_sync_installs_to_both_claude_and_copilot(
        self, agr, cli_project, cli_skill, cli_config
    ):
        """agr sync with multiple tools installs to all configured tools."""
        cli_config(
            """
tools = ["claude", "copilot"]
dependencies = [
    { path = "./skills/test-skill", type = "skill" },
]
"""
        )

        result = agr("sync")

        assert_cli(result).succeeded()
        assert (cli_project / ".claude" / "skills" / "local--test-skill").exists()
        assert (cli_project / ".github" / "skills" / "local--test-skill").exists()

    def test_remove_removes_from_both_claude_and_copilot(
        self, agr, cli_project, cli_skill, cli_config
    ):
        """agr remove removes skill from all configured tools."""
        cli_config('tools = ["claude", "copilot"]\ndependencies = []')
        agr("add", "./skills/test-skill")

        result = agr("remove", "./skills/test-skill")

        assert_cli(result).succeeded()
        assert not (cli_project / ".claude" / "skills" / "local--test-skill").exists()
        assert not (cli_project / ".github" / "skills" / "local--test-skill").exists()
