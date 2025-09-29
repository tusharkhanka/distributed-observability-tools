"""Utilities for observability components."""
from .client import instrument_httpx_client, CorrelatedClient, patch_httpx

__all__ = [
    "instrument_httpx_client",
    "CorrelatedClient",
    "patch_httpx",
]
