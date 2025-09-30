"""
HTTP client utilities for correlation ID propagation.

Provides instrumentation for automatically adding correlation IDs to outgoing
HTTP requests, ensuring trace continuity across service boundaries.
"""
import logging
from typing import Optional, Dict, Any

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None

from ..core.config import HTTPClientConfig
from ..tracing.tracer import CorrelationManager
from ..core.config import CorrelationConfig

logger = logging.getLogger(__name__)


class CorrelatedClient:
    """
    HTTP client wrapper that automatically adds correlation ID headers to requests.

    This client extracts correlation ID from the current span context and adds
    it to outgoing HTTP requests, ensuring distributed trace continuity.
    """

    def __init__(
        self,
        correlation_manager: CorrelationManager,
        client_config: Optional[HTTPClientConfig] = None,
        httpx_client: Optional["httpx.AsyncClient"] = None
    ):
        """
        Initialize correlated HTTP client.

        Args:
            correlation_manager: Manager for correlation ID handling
            client_config: Configuration for HTTP client behavior
            httpx_client: Optional pre-configured httpx client
        """
        self.correlation_manager = correlation_manager
        self.client_config = client_config or HTTPClientConfig()

        if not HTTPX_AVAILABLE:
            raise ImportError("httpx is required for HTTP client correlation. Install with: pip install httpx")

        self.client = httpx_client or httpx.AsyncClient()

    async def get(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> "httpx.Response":
        """Send GET request with correlation headers."""
        return await self.request("GET", url, headers=headers, **kwargs)

    async def post(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> "httpx.Response":
        """Send POST request with correlation headers."""
        return await self.request("POST", url, headers=headers, **kwargs)

    async def put(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> "httpx.Response":
        """Send PUT request with correlation headers."""
        return await self.request("PUT", url, headers=headers, **kwargs)

    async def delete(self, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> "httpx.Response":
        """Send DELETE request with correlation headers."""
        return await self.request("DELETE", url, headers=headers, **kwargs)

    async def request(self, method: str, url: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> "httpx.Response":
        """Send HTTP request with correlation headers added."""
        # Start with any provided headers
        request_headers = dict(headers) if headers else {}

        # Add correlation ID headers if not already present
        if self.client_config.enable_httpx:
            correlation_headers = self._get_correlation_headers()
            # Only add if not already in headers (don't override user-provided)
            for key, value in correlation_headers.items():
                if key.lower() not in [h.lower() for h in request_headers.keys()]:
                    request_headers[key] = value

        logger.debug(f"Outgoing {method} request to {url} with correlation headers: {correlation_headers}")

        return await self.client.request(method, url, headers=request_headers, **kwargs)

    def _get_correlation_headers(self) -> Dict[str, str]:
        """Get correlation headers from current context."""
        correlation_id = self._extract_current_correlation_id()
        if correlation_id:
            propagation_headers = self.correlation_manager.get_propagation_headers(correlation_id)
            logger.debug(f"Propagating correlation ID: {correlation_id}")
            return propagation_headers
        else:
            logger.debug("No correlation ID found in current context")
            return {}

    def _extract_current_correlation_id(self) -> Optional[str]:
        """Extract correlation ID from current tracing context."""
        try:
            from opentelemetry import trace

            current_span = trace.get_current_span()
            if current_span and current_span.is_recording():
                # Look for correlation ID in span attributes
                attributes = current_span.attributes or {}
                for key in ["correlation_id", "correlation.id", "x-correlation-id"]:
                    if key in attributes:
                        return str(attributes[key])
        except Exception as e:
            logger.debug(f"Could not extract correlation ID from span: {e}")

        return None

    async def close(self):
        """Close the underlying HTTP client."""
        await self.client.aclose()


# Convenience function for instrumenting existing httpx clients
def instrument_httpx_client(
    client: Optional["httpx.AsyncClient"] = None,
    correlation_config: Optional[CorrelationConfig] = None
) -> CorrelatedClient:
    """
    Instrument an httpx client with correlation ID propagation.

    Args:
        client: Optional existing httpx client to wrap
        correlation_config: Optional correlation configuration

    Returns:
        CorrelatedClient instance for making requests with correlation headers
    """
    if not HTTPX_AVAILABLE:
        raise ImportError("httpx is required for HTTP client correlation. Install with: pip install distributed-observability-tools[httpx]")

    correlation_manager = CorrelationManager(correlation_config or CorrelationConfig())
    http_config = HTTPClientConfig()

    return CorrelatedClient(correlation_manager, http_config, client)


# Hook for automatic httpx instrumentation
def patch_httpx():
    """Patch httpx to automatically add correlation headers to all requests."""
    if not HTTPX_AVAILABLE:
        logger.warning("httpx not available, skipping auto-instrumentation")
        return

    logger.debug("Patching httpx for automatic correlation header injection")

    original_request = httpx.AsyncClient.request

    async def patched_request(client_self, method, url, *args, **kwargs):
        # Only add correlation headers if not already present
        headers = kwargs.get('headers', {})

        # Extract correlation ID from current context
        correlation_id = None
        try:
            from opentelemetry import trace

            current_span = trace.get_current_span()
            if current_span and current_span.is_recording():
                attributes = current_span.attributes or {}
                for key in ["correlation_id", "correlation.id", "x-correlation-id"]:
                    if key in attributes:
                        correlation_id = str(attributes[key])
                        break
        except Exception:
            pass

        if correlation_id:
            correlation_config = CorrelationConfig()
            correlation_manager = CorrelationManager(correlation_config)
            propagation_headers = correlation_manager.get_propagation_headers(correlation_id)

            # Add headers if not already present
            headers = dict(headers)  # Copy existing headers
            for key, value in propagation_headers.items():
                if key.lower() not in [h.lower() for h in headers.keys()]:
                    headers[key] = value
                    logger.debug(f"Added correlation header {key}: {value}")

            kwargs['headers'] = headers

        return await original_request(client_self, method, url, *args, **kwargs)

    # Apply the patch
    httpx.AsyncClient.request = patched_request
    logger.info("httpx patched successfully")
