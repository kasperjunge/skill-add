"""CLI tests for agr add command."""

from tests.cli.assertions import assert_cli


class TestAgrAdd:
    """Tests for agr add command."""

    def test_add_local_skill_succeeds(self, agr, cli_skill):
        """agr add ./path adds local skill."""
        result = agr("add", "./skills/test-skill")

        assert_cli(result).succeeded().stdout_contains("Added:")

    def test_add_local_skill_creates_installed_dir(self, agr, cli_project, cli_skill):
        """agr add creates skill in .claude/skills."""
        agr("add", "./skills/test-skill")

        installed = cli_project / ".claude" / "skills" / "local--test-skill"
        assert installed.exists()
        assert (installed / "SKILL.md").exists()

    def test_add_local_skill_updates_config(self, agr, cli_project, cli_skill):
        """agr add updates agr.toml."""
        agr("add", "./skills/test-skill")

        config = (cli_project / "agr.toml").read_text()
        assert "skills/test-skill" in config

    def test_add_nonexistent_skill_fails(self, agr):
        """agr add nonexistent path fails."""
        result = agr("add", "./nonexistent")

        assert_cli(result).failed()

    def test_add_invalid_handle_fails(self, agr):
        """agr add with invalid handle fails."""
        result = agr("add", "not-a-valid-handle")

        assert_cli(result).failed()

    def test_add_outside_git_repo_fails(self, tmp_path):
        """agr add outside git repo fails."""
        from tests.cli.runner import run_cli

        result = run_cli(["agr", "add", "./skill"], cwd=tmp_path)

        assert_cli(result).failed().stdout_contains("Not in a git repository")

    def test_add_skill_already_installed_fails(self, agr, cli_skill):
        """agr add on already installed skill fails and suggests --overwrite."""
        agr("add", "./skills/test-skill")
        result = agr("add", "./skills/test-skill")

        assert_cli(result).failed().stdout_contains("--overwrite")
