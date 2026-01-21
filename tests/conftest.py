"""Test configuration and fixtures."""

import os
import time
from functools import wraps
from pathlib import Path

import pytest

from agr.config import AgrConfig


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "e2e: end-to-end tests requiring network")
    config.addinivalue_line("markers", "network: tests that make real network requests")
    config.addinivalue_line("markers", "slow: tests taking > 5 seconds")


@pytest.fixture(autouse=True)
def skip_e2e_in_ci(request):
    """Auto-skip E2E tests in CI based on SKIP_E2E env var."""
    if request.node.get_closest_marker("e2e"):
        if os.environ.get("SKIP_E2E", "").lower() in ("1", "true", "yes"):
            pytest.skip("E2E tests skipped in CI (SKIP_E2E=1)")


@pytest.fixture
def network_retry():
    """Provide a retry decorator for flaky network operations."""
    def retry_decorator(max_attempts=3, delay=1.0, backoff=2.0, exceptions=(Exception,)):
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                last_exception = None
                current_delay = delay
                for attempt in range(max_attempts):
                    try:
                        return func(*args, **kwargs)
                    except exceptions as e:
                        last_exception = e
                        if attempt < max_attempts - 1:
                            time.sleep(current_delay)
                            current_delay *= backoff
                raise last_exception
            return wrapper
        return decorator
    return retry_decorator


@pytest.fixture
def check_github_rate_limit():
    """Check GitHub API rate limits before running network tests."""
    def _check():
        try:
            import httpx
            response = httpx.get("https://api.github.com/rate_limit", timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                remaining = data.get("resources", {}).get("core", {}).get("remaining", 0)
                if remaining < 10:
                    pytest.skip(f"GitHub rate limit too low: {remaining} remaining")
        except Exception:
            pass
    return _check


E2E_TEST_REPO = "kasperjunge/agr-test-fixtures"


@pytest.fixture
def e2e_test_repo():
    """Provide the E2E test repository info as (owner, repo, full_name)."""
    return ("kasperjunge", "agr-test-fixtures", E2E_TEST_REPO)


@pytest.fixture
def git_project(tmp_path: Path, monkeypatch):
    """Set up a temporary git project directory."""
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".git").mkdir()
    return tmp_path


# Alias for compatibility with jobs/conftest.py naming convention
@pytest.fixture
def project_with_git(git_project: Path):
    """Alias for git_project fixture."""
    return git_project


@pytest.fixture(autouse=True)
def cleanup_test_entries():
    """Clean up any testuser entries from agr.toml after each test."""
    yield

    agr_toml = Path(__file__).parent.parent / "agr.toml"
    if not agr_toml.exists():
        return

    config = AgrConfig.load(agr_toml)
    original_count = len(config.dependencies)

    config.dependencies = [
        dep for dep in config.dependencies
        if not (
            (dep.handle and dep.handle.startswith("testuser/"))
            or (dep.path and "testuser" in dep.path)
        )
    ]

    if len(config.dependencies) != original_count:
        config.save(agr_toml)
