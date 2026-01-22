"""Tests for agr.commands module (integration tests)."""

import pytest

from agr.commands.init import init_config, init_skill
from agr.commands.list import run_list
from agr.config import AgrConfig, Dependency
from agr.skill import SKILL_MARKER


class TestInitCommand:
    """Tests for init command."""

    def test_init_config_creates_file(self, tmp_path, monkeypatch):
        """init_config creates agr.toml."""
        monkeypatch.chdir(tmp_path)

        config_path, created = init_config()

        assert created
        assert config_path.exists()
        assert config_path.name == "agr.toml"

    def test_init_config_existing(self, tmp_path, monkeypatch):
        """init_config with existing file returns it."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / ".git").mkdir()
        existing = tmp_path / "agr.toml"
        existing.write_text("dependencies = []")

        config_path, created = init_config()

        assert not created
        assert config_path == existing

    def test_init_skill_creates_scaffold(self, tmp_path, monkeypatch):
        """init_skill creates skill scaffold."""
        monkeypatch.chdir(tmp_path)

        skill_path = init_skill("my-skill")

        assert skill_path.exists()
        assert (skill_path / SKILL_MARKER).exists()

    def test_init_skill_invalid_name(self, tmp_path, monkeypatch):
        """init_skill with invalid name raises."""
        monkeypatch.chdir(tmp_path)

        with pytest.raises(ValueError):
            init_skill("-invalid")

    def test_init_skill_existing_dir(self, tmp_path, monkeypatch):
        """init_skill with existing directory raises."""
        monkeypatch.chdir(tmp_path)
        (tmp_path / "existing").mkdir()

        with pytest.raises(FileExistsError):
            init_skill("existing")


class TestListCommand:
    """Tests for list command."""

    def test_list_no_config(self, git_project, capsys):
        """list with no config prints message."""
        run_list()

        captured = capsys.readouterr()
        assert "No agr.toml found" in captured.out

    def test_list_empty_deps(self, git_project, capsys):
        """list with empty deps prints message."""
        config = AgrConfig()
        config.save(git_project / "agr.toml")

        run_list()

        captured = capsys.readouterr()
        assert "No dependencies" in captured.out

    def test_list_with_deps(self, git_project, capsys):
        """list with deps prints table."""
        config = AgrConfig()
        config.add_dependency(Dependency(type="skill", handle="user/skill"))
        config.save(git_project / "agr.toml")

        run_list()

        captured = capsys.readouterr()
        assert "user/skill" in captured.out


class TestAddRemoveCommands:
    """Tests for add and remove commands.

    These require network access for remote skills.
    """

    def test_add_local_skill(self, git_project, skill_fixture):
        """Add a local skill."""
        from agr.commands.add import run_add

        # Move skill fixture into the project
        import shutil
        local_skill = git_project / "my-skill"
        shutil.copytree(skill_fixture, local_skill)

        run_add(["./my-skill"])

        # Check config
        config = AgrConfig.load(git_project / "agr.toml")
        assert len(config.dependencies) == 1
        assert config.dependencies[0].path == "./my-skill"

        # Check installed
        installed_dir = git_project / ".claude" / "skills" / "local:my-skill"
        assert installed_dir.exists()

    def test_remove_local_skill(self, git_project, skill_fixture):
        """Remove a local skill."""
        from agr.commands.add import run_add
        from agr.commands.remove import run_remove

        # First add the skill
        import shutil
        local_skill = git_project / "my-skill"
        shutil.copytree(skill_fixture, local_skill)
        run_add(["./my-skill"])

        # Now remove it
        run_remove(["./my-skill"])

        # Check config
        config = AgrConfig.load(git_project / "agr.toml")
        assert len(config.dependencies) == 0

        # Check uninstalled
        installed_dir = git_project / ".claude" / "skills" / "local:my-skill"
        assert not installed_dir.exists()

    @pytest.mark.e2e
    def test_add_remote_skill(self, git_project):
        """Add a remote skill from GitHub."""
        from agr.commands.add import run_add

        run_add(["kasperjunge/commit"])

        # Check config
        config = AgrConfig.load(git_project / "agr.toml")
        assert len(config.dependencies) == 1
        assert config.dependencies[0].handle == "kasperjunge/commit"

        # Check installed
        installed_dir = git_project / ".claude" / "skills" / "kasperjunge:commit"
        assert installed_dir.exists()


class TestSyncCommand:
    """Tests for sync command."""

    def test_sync_empty(self, git_project, capsys):
        """sync with no config prints message."""
        from agr.commands.sync import run_sync

        run_sync()

        captured = capsys.readouterr()
        assert "No agr.toml found" in captured.out or "Nothing to sync" in captured.out

    def test_sync_up_to_date(self, git_project, skill_fixture, capsys):
        """sync when already installed shows up to date."""
        from agr.commands.add import run_add
        from agr.commands.sync import run_sync

        # Add skill
        import shutil
        local_skill = git_project / "my-skill"
        shutil.copytree(skill_fixture, local_skill)
        run_add(["./my-skill"])

        # Sync again
        run_sync()

        captured = capsys.readouterr()
        assert "up to date" in captured.out.lower()
