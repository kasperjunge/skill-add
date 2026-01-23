"""Orchestrator re-export for API compatibility.

This module re-exports from agr.orchestrator for backward compatibility.
The orchestrator was moved out of agr.core to avoid circular imports.

For new code, import directly from agr.orchestrator.
"""

from agr.orchestrator import InstallResult, Orchestrator

__all__ = ["InstallResult", "Orchestrator"]
