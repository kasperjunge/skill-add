"""CLI test runner using real subprocess execution."""

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

ANSI_PATTERN = re.compile(r"\x1b\[[0-9;]*m")
DEFAULT_TIMEOUT = 30


def strip_ansi(text: str) -> str:
    """Remove ANSI escape codes from text."""
    return ANSI_PATTERN.sub("", text)


@dataclass
class CLIResult:
    """Result of a CLI command execution."""

    args: list[str]
    returncode: int
    stdout_raw: str
    stderr_raw: str

    @property
    def stdout(self) -> str:
        """Stdout with ANSI codes stripped."""
        return strip_ansi(self.stdout_raw)

    @property
    def stderr(self) -> str:
        """Stderr with ANSI codes stripped."""
        return strip_ansi(self.stderr_raw)


def run_cli(
    args: list[str],
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    input: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> CLIResult:
    """Run a CLI command and return the result."""
    # Merge env with NO_COLOR=1 to disable Rich colors
    full_env = os.environ.copy()
    full_env["NO_COLOR"] = "1"
    if env:
        full_env.update(env)

    result = subprocess.run(
        args,
        cwd=cwd,
        env=full_env,
        input=input,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    return CLIResult(
        args=args,
        returncode=result.returncode,
        stdout_raw=result.stdout,
        stderr_raw=result.stderr,
    )
