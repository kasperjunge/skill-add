"""CLI tests for agr version and help."""

from tests.cli.assertions import assert_cli
from tests.cli.runner import run_cli


class TestAgrVersion:
    """Tests for agr --version and --help."""

    def test_version_flag(self):
        """agr --version shows version."""
        result = run_cli(["agr", "--version"])

        assert_cli(result).succeeded().stdout_matches(r"agr \d+\.\d+\.\d+")

    def test_help_flag(self):
        """agr --help shows help."""
        result = run_cli(["agr", "--help"])

        (
            assert_cli(result)
            .succeeded()
            .stdout_contains("Agent Resources")
            .stdout_contains("add")
            .stdout_contains("remove")
            .stdout_contains("sync")
        )
