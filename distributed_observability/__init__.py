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
__email__ = "tusharkhanka@gmail.com"

# Core tracing exports (always available)
from .tracing import TracingConfig, setup_tracing, TracingManager

# Optional framework integrations
try:
    from .framework.fastapi import RequestTracingMiddleware
    _FASTAPI_AVAILABLE = True
except ImportError:
    RequestTracingMiddleware = None
    _FASTAPI_AVAILABLE = False

# Optional utilities
try:
    from .utils.client import instrument_httpx_client
    _HTTPX_AVAILABLE = True
except ImportError:
    instrument_httpx_client = None
    _HTTPX_AVAILABLE = False

__all__ = [
    # Version info
    "__version__",
    "__author__",
    "__email__",

    # Core tracing (always available)
    "TracingConfig",
    "setup_tracing",
    "TracingManager",
]

# Add optional exports if available
if _FASTAPI_AVAILABLE:
    __all__.append("RequestTracingMiddleware")

if _HTTPX_AVAILABLE:
    __all__.append("instrument_httpx_client")
