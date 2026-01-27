"""CLI tests for agr remove command."""

from tests.cli.assertions import assert_cli


class TestAgrRemove:
    """Tests for agr remove command."""

    def test_remove_installed_skill_succeeds(self, agr, cli_project, cli_skill):
        """agr remove removes installed skill."""
        # First add the skill
        agr("add", "./skills/test-skill")

        # Then remove it
        result = agr("remove", "./skills/test-skill")

        assert_cli(result).succeeded().stdout_contains("Removed:")

    def test_remove_cleans_up_directory(self, agr, cli_project, cli_skill):
        """agr remove deletes installed directory."""
        agr("add", "./skills/test-skill")

        installed = cli_project / ".claude" / "skills" / "local--test-skill"
        assert installed.exists()

        agr("remove", "./skills/test-skill")

        assert not installed.exists()

    def test_remove_updates_config(self, agr, cli_project, cli_skill):
        """agr remove updates agr.toml."""
        agr("add", "./skills/test-skill")
        agr("remove", "./skills/test-skill")

        config = (cli_project / "agr.toml").read_text()
        assert "skills/test-skill" not in config

    def test_remove_not_installed_fails(self, agr, cli_skill):
        """agr remove on non-installed skill fails."""
        result = agr("remove", "./skills/test-skill")

        assert_cli(result).failed()
