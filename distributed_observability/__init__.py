"""
Distributed Observability Tools

A comprehensive observability suite for distributed systems, providing:
- Distributed tracing with correlation ID propagation
- Structured logging capabilities
- Metrics collection and aggregation

Example:
    >>> from distributed_observability import TracingConfig, setup_tracing
    >>> config = TracingConfig(service_name="my-service")
    >>> tracer, middleware = setup_tracing(config)
"""

__version__ = "0.1.0"
__author__ = "Tushar Khanka"
__email__ = "your-email@gmail.com"

# Core tracing exports
from .tracing import TracingConfig, setup_tracing, TracingManager
from .framework.fastapi import RequestTracingMiddleware
from .utils.client import instrument_httpx_client

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",

    # Core tracing
    "TracingConfig",
    "setup_tracing",
    "TracingManager",

    # Framework integrations
    "RequestTracingMiddleware",

    # Utilities
    "instrument_httpx_client",
]
