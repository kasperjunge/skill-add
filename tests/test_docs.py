"""Tests for documentation integrity."""

import re
from pathlib import Path

import pytest

DOCS_DIR = Path(__file__).parent.parent / "docs" / "docs"


def get_markdown_files() -> list[Path]:
    """Get all markdown files in docs directory."""
    return list(DOCS_DIR.glob("*.md"))


def extract_internal_links(content: str) -> list[str]:
    """Extract internal markdown links from content, excluding code blocks."""
    # First, remove code blocks to avoid parsing example links
    content_no_code = re.sub(r"```.*?```", "", content, flags=re.DOTALL)

    # Match [text](link) where link doesn't start with http
    pattern = r"\[([^\]]+)\]\(([^)]+)\)"
    links = []
    for match in re.finditer(pattern, content_no_code):
        link = match.group(2)
        if not link.startswith(("http://", "https://", "#")):
            links.append(link)
    return links


def extract_code_blocks(content: str) -> list[tuple[str, str]]:
    """Extract code blocks with their language from content."""
    pattern = r"```(\w+)?\n(.*?)```"
    return re.findall(pattern, content, re.DOTALL)


class TestDocsExist:
    """Test that required documentation files exist."""

    def test_index_exists(self):
        """Home page exists."""
        assert (DOCS_DIR / "index.md").exists()

    def test_creating_exists(self):
        """Creating skills page exists."""
        assert (DOCS_DIR / "creating.md").exists()

    def test_reference_exists(self):
        """Reference page exists."""
        assert (DOCS_DIR / "reference.md").exists()

    def test_llms_txt_exists(self):
        """llms.txt exists."""
        assert (DOCS_DIR / "llms.txt").exists()


class TestInternalLinks:
    """Test that internal links resolve to existing files."""

    @pytest.mark.parametrize("md_file", get_markdown_files())
    def test_internal_links_resolve(self, md_file: Path):
        """All internal links point to existing files."""
        content = md_file.read_text()
        links = extract_internal_links(content)

        for link in links:
            # Handle relative links
            if link.startswith("./"):
                target = DOCS_DIR / link[2:]
            else:
                target = DOCS_DIR / link

            # Remove .md extension handling for directory-style links
            if not target.exists() and not target.suffix:
                target = target.with_suffix(".md")

            assert target.exists(), f"Broken link in {md_file.name}: {link}"


class TestCodeExamples:
    """Test that code examples are syntactically valid."""

    @pytest.mark.parametrize("md_file", get_markdown_files())
    def test_bash_commands_have_valid_structure(self, md_file: Path):
        """Bash code blocks contain valid-looking commands."""
        content = md_file.read_text()
        blocks = extract_code_blocks(content)

        for lang, code in blocks:
            if lang == "bash":
                # Skip empty blocks
                if not code.strip():
                    continue

                # Check that bash commands start with a valid command or comment
                lines = [l.strip() for l in code.strip().split("\n") if l.strip()]
                for line in lines:
                    # Skip comments
                    if line.startswith("#"):
                        continue
                    # Check first word is a plausible command
                    first_word = line.split()[0] if line.split() else ""
                    assert first_word, f"Empty bash line in {md_file.name}"

    @pytest.mark.parametrize("md_file", get_markdown_files())
    def test_toml_syntax_valid(self, md_file: Path):
        """TOML code blocks are syntactically valid."""
        content = md_file.read_text()
        blocks = extract_code_blocks(content)

        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        for lang, code in blocks:
            if lang == "toml":
                try:
                    tomllib.loads(code)
                except Exception as e:
                    pytest.fail(f"Invalid TOML in {md_file.name}: {e}")

    @pytest.mark.parametrize("md_file", get_markdown_files())
    def test_markdown_code_blocks_have_frontmatter(self, md_file: Path):
        """Markdown code blocks that show SKILL.md format have frontmatter."""
        content = md_file.read_text()
        blocks = extract_code_blocks(content)

        for lang, code in blocks:
            if lang == "markdown" and "SKILL" in code:
                # Check for frontmatter
                assert code.strip().startswith("---"), (
                    f"SKILL.md example in {md_file.name} should start with frontmatter"
                )


class TestCliCommands:
    """Test that documented CLI commands are real."""

    KNOWN_COMMANDS = {"add", "remove", "sync", "list", "init"}

    def test_documented_agr_commands_exist(self):
        """Commands documented in reference.md are known commands."""
        reference = (DOCS_DIR / "reference.md").read_text()

        # Extract code blocks only
        code_blocks = extract_code_blocks(reference)
        bash_code = "\n".join(code for lang, code in code_blocks if lang == "bash")

        # Extract agr commands from bash code blocks only
        pattern = r"agr (\w+)"
        commands = set(re.findall(pattern, bash_code))

        for cmd in commands:
            assert cmd in self.KNOWN_COMMANDS, (
                f"Unknown command documented: agr {cmd}"
            )

    def test_documented_agrx_exists(self):
        """agrx command is documented."""
        reference = (DOCS_DIR / "reference.md").read_text()
        assert "agrx" in reference


class TestContentQuality:
    """Test documentation content quality."""

    def test_index_has_quick_start(self):
        """Home page has a quick install example."""
        content = (DOCS_DIR / "index.md").read_text()
        assert "uvx agr add" in content or "pip install agr" in content

    def test_creating_has_skill_example(self):
        """Creating page has a complete skill example."""
        content = (DOCS_DIR / "creating.md").read_text()
        assert "SKILL.md" in content
        assert "name:" in content
        assert "description:" in content

    def test_reference_has_all_commands(self):
        """Reference page documents all main commands."""
        content = (DOCS_DIR / "reference.md").read_text()
        for cmd in ["agr add", "agr remove", "agr sync", "agr list", "agr init", "agrx"]:
            assert cmd in content, f"Missing documentation for {cmd}"

    def test_no_broken_next_steps(self):
        """Next steps links in index.md point to valid pages."""
        content = (DOCS_DIR / "index.md").read_text()
        links = extract_internal_links(content)

        for link in links:
            target = DOCS_DIR / link
            if not target.exists() and not target.suffix:
                target = target.with_suffix(".md")
            assert target.exists(), f"Broken next steps link: {link}"
