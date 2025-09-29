"""
FastAPI framework integration for distributed tracing.

Provides middleware for automatic request tracing and correlation ID injection,
with SigNoz-compatible span attribute instrumentation.
"""
import logging
import time
from typing import Optional, Dict, Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.requests import Request
from starlette.responses import Response

from opentelemetry import trace

from ..core.config import TracingConfig, FastAPIConfig
from ..tracing.tracer import SpanManager

logger = logging.getLogger(__name__)


class RequestTracingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic request tracing and correlation ID management.

    This middleware:
    - Creates spans for incoming HTTP requests
    - Extracts and propagates correlation IDs
    - Adds SigNoz-compatible span attributes
    - Handles exception recording in spans
    - Adds custom headers to responses for debugging
    """

    def __init__(
        self,
        app: ASGIApp,
        tracing_config: TracingConfig,
        fastapi_config: Optional[FastAPIConfig] = None,
        custom_span_attributes: Optional[Dict[str, Any]] = None
    ):
        super().__init__(app)
        self.tracing_config = tracing_config
        self.fastapi_config = fastapi_config or FastAPIConfig()
        self.span_manager = SpanManager(tracing_config)
        self.custom_span_attributes = custom_span_attributes or {}

        logger.info("🚀 FastAPI Request Tracing Middleware initialized")
        logger.info(f"📊 Otel endpoint: {tracing_config.collector_url}")
        logger.info("🎯 SigNoz-compatible correlation ID tracking enabled")

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with tracing instrumentation."""

        # Skip tracing if not configured
        if not self.fastapi_config.enable_middleware:
            return await call_next(request)

        # Start timing
        start_time = time.time()

        # Extract client information
        client_host = getattr(request.client, 'host', 'unknown') if request.client else 'unknown'
        client_port = getattr(request.client, 'port', 'unknown') if request.client else 'unknown'

        # Extract all headers for correlation ID detection
        headers_dict = dict(request.headers)

        try:
            # Get current span (may be root span or child)
            current_span = trace.get_current_span()

            # Instrument the span with request details and correlation ID
            if current_span and current_span.is_recording():
                # Add correlation ID as span attributes (SigNoz compatibility)
                correlation_id = self.span_manager.correlation_manager.get_correlation_id(headers_dict)

                if correlation_id:
                    # Primary root-level span attributes (same hierarchical level as service.name)
                    current_span.set_attribute("correlation_id", correlation_id)

                    # Standard span attributes
                    current_span.set_attribute("service.name", self.tracing_config.service_name)
                    current_span.set_attribute("service.port", getattr(self.tracing_config, 'service_port', 8000))
                    current_span.set_attribute("request.method", request.method)
                    current_span.set_attribute("request.path", request.url.path)
                    current_span.set_attribute("client.ip", client_host)

                    # CloudFront/Lambda@Edge specific attributes
                    edge_location = headers_dict.get('x-edge-location')
                    if edge_location and edge_location != 'not-found':
                        current_span.set_attribute("cloudfront.edge_location", edge_location)

                    cf_id = headers_dict.get('x-amz-cf-id')
                    if cf_id and cf_id != 'not-found':
                        current_span.set_attribute("cloudfront.distribution_id", cf_id)

                    request_id = headers_dict.get('x-request-id')
                    if request_id and request_id != 'not-found':
                        current_span.set_attribute("cloudfront.request_id", request_id)

                    # SigNoz-compatible nested attributes (backward compatibility)
                    current_span.set_attribute("correlation.id", correlation_id)
                    current_span.set_attribute("x-correlation-id", correlation_id)
                    current_span.set_attribute("http.request.header.x-correlation-id", correlation_id)

                    if edge_location and edge_location != 'not-found':
                        current_span.set_attribute("x-edge-location", edge_location)
                    if request_id and request_id != 'not-found':
                        current_span.set_attribute("x-request-id", request_id)
                    if cf_id and cf_id != 'not-found':
                        current_span.set_attribute("x-amz-cf-id", cf_id)

                # Add custom span attributes
                for key, value in self.custom_span_attributes.items():
                    current_span.set_attribute(key, value)

                # Log correlation ID detection
                if correlation_id:
                    logger.info(f"🎯 CORRELATION ID DETECTED: {correlation_id}")
                    logger.info(f"📊 SPAN ATTRIBUTES SET: correlation_id={correlation_id}")
                else:
                    logger.warning("⚠️ NO CORRELATION ID FOUND in request headers")

            # Process the request
            try:
                response = await call_next(request)

                # Calculate processing time
                process_time = time.time() - start_time

                # Add custom headers to response for debugging
                response.headers["X-Service-Name"] = self.tracing_config.service_name

                if correlation_id:
                    response.headers["X-Correlation-ID"] = correlation_id

                response.headers["X-Processing-Time"] = str(process_time)

                # Log response details
                logger.info(f"📤 RESPONSE: status={response.status_code}, time={process_time:.3f}s")

                return response

            except Exception as e:
                # Record exception in current span
                if current_span and current_span.is_recording():
                    self.span_manager.record_exception(current_span, e)

                # Log error details
                logger.error(f"❌ REQUEST ERROR: {type(e).__name__}: {e}")

                # Re-raise to maintain normal error handling
                raise

        except Exception as middleware_error:
            logger.warning(f"⚠️ Middleware error: {middleware_error}")
            # Don't let middleware errors break the app
            try:
                return await call_next(request)
            except Exception:
                # Last resort - create minimal response
                return Response("Internal Server Error", status_code=500)


# Convenience function for easy integration
def setup_fastapi_tracing(
    app: ASGIApp,
    tracing_config: TracingConfig,
    fastapi_config: Optional[FastAPIConfig] = None,
    custom_span_attributes: Optional[Dict[str, Any]] = None
) -> ASGIApp:
    """
    Convenience function to add tracing middleware to FastAPI app.

    Args:
        app: FastAPI application instance
        tracing_config: Tracing configuration
        fastapi_config: Optional FastAPI-specific config
        custom_span_attributes: Optional custom span attributes

    Returns:
        Modified FastAPI app with tracing middleware added
    """
    middleware = RequestTracingMiddleware(
        app,
        tracing_config,
        fastapi_config,
        custom_span_attributes
    )

    # Return app wrapped with middleware
    return middleware


# Utility to get correlation ID from current request context
def get_current_correlation_id() -> Optional[str]:
    """
    Get correlation ID from current span context.

    This can be used within request handlers to access the correlation ID
    that was extracted from the incoming request headers.

    Returns:
        Correlation ID string if available, None otherwise
    """
    try:
        current_span = trace.get_current_span()
        if current_span and current_span.is_recording():
            # Look for correlation ID in span attributes
            for key in ["correlation_id", "x-correlation-id"]:
                if key in current_span.attributes:
                    return current_span.attributes[key]
    except Exception:
        pass
    return None
