"""CLI tests for agr init command."""

from tests.cli.assertions import assert_cli


class TestAgrInit:
    """Tests for agr init command."""

    def test_init_creates_agr_toml(self, agr, cli_project):
        """agr init creates agr.toml file."""
        result = agr("init")

        assert_cli(result).succeeded()
        assert (cli_project / "agr.toml").exists()

    def test_init_existing_returns_existing(self, agr, cli_project, cli_config):
        """agr init with existing config returns it."""
        cli_config("dependencies = []")

        result = agr("init")

        assert_cli(result).succeeded().stdout_contains("Already exists")

    def test_init_skill_creates_scaffold(self, agr, cli_project):
        """agr init <name> creates skill scaffold."""
        result = agr("init", "my-new-skill")

        assert_cli(result).succeeded()
        skill_dir = cli_project / "my-new-skill"
        assert skill_dir.exists()
        assert (skill_dir / "SKILL.md").exists()

    def test_init_skill_invalid_name_fails(self, agr):
        """agr init with invalid skill name fails."""
        result = agr("init", "invalid name with spaces")

        assert_cli(result).failed().stdout_contains("Invalid skill name")

    def test_init_skill_existing_directory_fails(self, agr, cli_project):
        """agr init with existing directory fails."""
        (cli_project / "existing-skill").mkdir()
        result = agr("init", "existing-skill")

        assert_cli(result).failed()
