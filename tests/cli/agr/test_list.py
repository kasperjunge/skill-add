"""CLI tests for agr list command."""

from tests.cli.assertions import assert_cli


class TestAgrList:
    """Tests for agr list command."""

    def test_list_no_config_message(self, agr):
        """agr list without config shows message."""
        result = agr("list")

        assert_cli(result).succeeded().stdout_contains("No agr.toml")

    def test_list_empty_deps_message(self, agr, cli_config):
        """agr list with empty deps shows message."""
        cli_config("dependencies = []")

        result = agr("list")

        assert_cli(result).succeeded().stdout_contains("No dependencies")

    def test_list_shows_installed_skills(self, agr, cli_skill):
        """agr list shows installed skills."""
        agr("add", "./skills/test-skill")

        result = agr("list")

        assert_cli(result).succeeded().stdout_contains("test-skill")
