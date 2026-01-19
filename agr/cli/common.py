"""Shared CLI utilities for agr commands - re-exports for backward compatibility."""

# Re-export from paths module
from agr.cli.paths import (
    console,
    DEFAULT_REPO_NAME,
    TYPE_TO_SUBDIR,
    find_repo_root,
    is_local_path,
    extract_type_from_args,
    parse_nested_name,
    parse_resource_ref,
    get_base_path,
    get_destination,
    get_namespaced_destination,
    fetch_spinner,
    cleanup_empty_parent,
    remove_path,
    error_exit,
    warn,
)

# Re-export from discovery module
from agr.cli.discovery import (
    discover_local_resource_type,
    discover_runnable_resource,
)

# Re-export from handlers module
from agr.cli.handlers import (
    print_success_message,
    handle_add_resource,
    get_local_resource_path,
    handle_remove_resource,
    print_installed_resources,
    print_bundle_success_message,
    print_bundle_remove_message,
    handle_add_bundle,
    handle_remove_bundle,
    handle_add_unified,
    handle_remove_unified,
)

# Define __all__ for explicit public API
__all__ = [
    # paths
    "console",
    "DEFAULT_REPO_NAME",
    "TYPE_TO_SUBDIR",
    "find_repo_root",
    "is_local_path",
    "extract_type_from_args",
    "parse_nested_name",
    "parse_resource_ref",
    "get_base_path",
    "get_destination",
    "get_namespaced_destination",
    "fetch_spinner",
    "cleanup_empty_parent",
    "remove_path",
    "error_exit",
    "warn",
    # discovery
    "discover_local_resource_type",
    "discover_runnable_resource",
    # handlers
    "print_success_message",
    "handle_add_resource",
    "get_local_resource_path",
    "handle_remove_resource",
    "print_installed_resources",
    "print_bundle_success_message",
    "print_bundle_remove_message",
    "handle_add_bundle",
    "handle_remove_bundle",
    "handle_add_unified",
    "handle_remove_unified",
]
