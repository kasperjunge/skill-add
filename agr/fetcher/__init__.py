"""Generic resource fetcher for skills, commands, and agents."""

from agr.fetcher.bundle import (
    BundleContents,
    BundleInstallResult,
    BundleRemoveResult,
    discover_bundle_contents,
    fetch_bundle,
    fetch_bundle_from_repo_dir,
    remove_bundle,
)
from agr.fetcher.discovery import (
    discover_resource_type_from_dir,
    _is_bundle,
)
from agr.fetcher.download import (
    downloaded_repo,
    _build_resource_path,
    _download_and_extract_tarball,
)
from agr.fetcher.resource import (
    fetch_resource,
    fetch_resource_from_repo_dir,
)
from agr.fetcher.types import (
    DiscoveredResource,
    DiscoveryResult,
    ResourceConfig,
    RESOURCE_CONFIGS,
    ResourceType,
)

__all__ = [
    # Types and configs
    "ResourceType",
    "ResourceConfig",
    "RESOURCE_CONFIGS",
    "DiscoveredResource",
    "DiscoveryResult",
    # Download operations
    "downloaded_repo",
    "_build_resource_path",
    "_download_and_extract_tarball",
    # Discovery
    "discover_resource_type_from_dir",
    "_is_bundle",
    # Resource fetching
    "fetch_resource_from_repo_dir",
    "fetch_resource",
    # Bundle operations
    "BundleContents",
    "BundleInstallResult",
    "BundleRemoveResult",
    "discover_bundle_contents",
    "fetch_bundle_from_repo_dir",
    "fetch_bundle",
    "remove_bundle",
]
