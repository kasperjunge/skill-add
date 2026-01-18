"""Tests for the refactored fetcher module structure.

Verifies that the fetcher package exports all expected symbols and
maintains backward compatibility after the modular refactoring.
"""

import pytest


class TestFetcherModuleExports:
    """Test that each submodule exports expected symbols."""

    def test_types_module_exports(self):
        """Test types.py exports all type definitions."""
        from agr.fetcher.types import (
            ResourceType,
            ResourceConfig,
            RESOURCE_CONFIGS,
            DiscoveredResource,
            DiscoveryResult,
        )

        # Verify ResourceType enum values
        assert ResourceType.SKILL.value == "skill"
        assert ResourceType.COMMAND.value == "command"
        assert ResourceType.AGENT.value == "agent"

        # Verify RESOURCE_CONFIGS has all types
        assert ResourceType.SKILL in RESOURCE_CONFIGS
        assert ResourceType.COMMAND in RESOURCE_CONFIGS
        assert ResourceType.AGENT in RESOURCE_CONFIGS

        # Verify ResourceConfig structure
        skill_config = RESOURCE_CONFIGS[ResourceType.SKILL]
        assert skill_config.is_directory is True
        assert skill_config.source_subdir == ".claude/skills"

    def test_download_module_exports(self):
        """Test download.py exports download operations."""
        from agr.fetcher.download import (
            downloaded_repo,
            _build_resource_path,
            _download_and_extract_tarball,
        )

        # Verify they are callable
        assert callable(downloaded_repo)
        assert callable(_build_resource_path)
        assert callable(_download_and_extract_tarball)

    def test_bundle_module_exports(self):
        """Test bundle.py exports bundle operations."""
        from agr.fetcher.bundle import (
            BundleContents,
            BundleInstallResult,
            BundleRemoveResult,
            discover_bundle_contents,
            fetch_bundle_from_repo_dir,
            fetch_bundle,
            remove_bundle,
        )

        # Verify dataclass structure
        contents = BundleContents(bundle_name="test")
        assert contents.is_empty is True
        assert contents.total_count == 0

        result = BundleInstallResult()
        assert result.total_installed == 0
        assert result.total_skipped == 0

        remove_result = BundleRemoveResult()
        assert remove_result.is_empty is True
        assert remove_result.total_removed == 0

    def test_discovery_module_exports(self):
        """Test discovery.py exports discovery functions."""
        from agr.fetcher.discovery import (
            discover_resource_type_from_dir,
            _is_bundle,
        )

        assert callable(discover_resource_type_from_dir)
        assert callable(_is_bundle)

    def test_resource_module_exports(self):
        """Test resource.py exports fetch functions."""
        from agr.fetcher.resource import (
            fetch_resource_from_repo_dir,
            fetch_resource,
        )

        assert callable(fetch_resource_from_repo_dir)
        assert callable(fetch_resource)


class TestBackwardCompatibilityImports:
    """Test backward compatibility via agr.fetcher package imports."""

    def test_all_public_symbols_importable_from_package(self):
        """Test all public symbols can be imported from agr.fetcher."""
        from agr.fetcher import (
            # Types
            ResourceType,
            ResourceConfig,
            RESOURCE_CONFIGS,
            DiscoveredResource,
            DiscoveryResult,
            # Download
            downloaded_repo,
            # Discovery
            discover_resource_type_from_dir,
            # Resource fetching
            fetch_resource_from_repo_dir,
            fetch_resource,
            # Bundle operations
            BundleContents,
            BundleInstallResult,
            BundleRemoveResult,
            discover_bundle_contents,
            fetch_bundle_from_repo_dir,
            fetch_bundle,
            remove_bundle,
        )

        # All symbols should be importable without error
        assert ResourceType is not None
        assert ResourceConfig is not None
        assert RESOURCE_CONFIGS is not None
        assert DiscoveredResource is not None
        assert DiscoveryResult is not None
        assert downloaded_repo is not None
        assert discover_resource_type_from_dir is not None
        assert fetch_resource_from_repo_dir is not None
        assert fetch_resource is not None
        assert BundleContents is not None
        assert BundleInstallResult is not None
        assert BundleRemoveResult is not None
        assert discover_bundle_contents is not None
        assert fetch_bundle_from_repo_dir is not None
        assert fetch_bundle is not None
        assert remove_bundle is not None

    def test_all_exports_match_dunder_all(self):
        """Test that __all__ matches actual exports."""
        import agr.fetcher as fetcher_module

        for name in fetcher_module.__all__:
            assert hasattr(fetcher_module, name), f"Missing export: {name}"


class TestDiscoveryResultDataclass:
    """Test DiscoveryResult dataclass properties."""

    def test_is_unique_with_one_resource(self):
        """Test is_unique returns True for exactly one resource."""
        from agr.fetcher import DiscoveredResource, DiscoveryResult, ResourceType

        result = DiscoveryResult(
            resources=[
                DiscoveredResource(
                    name="test",
                    resource_type=ResourceType.SKILL,
                    path_segments=["test"],
                )
            ]
        )
        assert result.is_unique is True
        assert result.is_ambiguous is False
        assert result.is_empty is False

    def test_is_unique_with_bundle_only(self):
        """Test is_unique returns True for bundle only."""
        from agr.fetcher import DiscoveryResult

        result = DiscoveryResult(resources=[], is_bundle=True)
        assert result.is_unique is True
        assert result.is_ambiguous is False
        assert result.is_empty is False

    def test_is_ambiguous_with_multiple(self):
        """Test is_ambiguous returns True for multiple resources."""
        from agr.fetcher import DiscoveredResource, DiscoveryResult, ResourceType

        result = DiscoveryResult(
            resources=[
                DiscoveredResource(
                    name="test",
                    resource_type=ResourceType.SKILL,
                    path_segments=["test"],
                ),
                DiscoveredResource(
                    name="test",
                    resource_type=ResourceType.COMMAND,
                    path_segments=["test"],
                ),
            ]
        )
        assert result.is_unique is False
        assert result.is_ambiguous is True

    def test_is_empty_with_no_resources(self):
        """Test is_empty returns True for no resources."""
        from agr.fetcher import DiscoveryResult

        result = DiscoveryResult()
        assert result.is_empty is True
        assert result.is_unique is False
        assert result.is_ambiguous is False

    def test_found_types_includes_bundle(self):
        """Test found_types includes bundle when is_bundle is True."""
        from agr.fetcher import DiscoveredResource, DiscoveryResult, ResourceType

        result = DiscoveryResult(
            resources=[
                DiscoveredResource(
                    name="test",
                    resource_type=ResourceType.SKILL,
                    path_segments=["test"],
                )
            ],
            is_bundle=True,
        )
        types = result.found_types
        assert "skill" in types
        assert "bundle" in types


class TestResourceConfigStructure:
    """Test ResourceConfig has correct structure for each type."""

    def test_skill_config(self):
        """Test skill configuration."""
        from agr.fetcher import RESOURCE_CONFIGS, ResourceType

        config = RESOURCE_CONFIGS[ResourceType.SKILL]
        assert config.is_directory is True
        assert config.file_extension is None
        assert config.source_subdir == ".claude/skills"
        assert config.dest_subdir == "skills"

    def test_command_config(self):
        """Test command configuration."""
        from agr.fetcher import RESOURCE_CONFIGS, ResourceType

        config = RESOURCE_CONFIGS[ResourceType.COMMAND]
        assert config.is_directory is False
        assert config.file_extension == ".md"
        assert config.source_subdir == ".claude/commands"
        assert config.dest_subdir == "commands"

    def test_agent_config(self):
        """Test agent configuration."""
        from agr.fetcher import RESOURCE_CONFIGS, ResourceType

        config = RESOURCE_CONFIGS[ResourceType.AGENT]
        assert config.is_directory is False
        assert config.file_extension == ".md"
        assert config.source_subdir == ".claude/agents"
        assert config.dest_subdir == "agents"
