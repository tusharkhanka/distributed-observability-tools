"""
Core tracing functionality for distributed observability tools.

This module provides clean, configurable OpenTelemetry tracing with correlation ID
support and SigNoz-compatible span attributes.
"""
import logging
import uuid
from typing import Optional, Dict, Any, TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
# Try to import sampler classes - use default if not available
try:
    from opentelemetry.sdk.trace.sampling import TraceIdRatioBasedSampler
    SAMPLER_AVAILABLE = True
except ImportError:
    SAMPLER_AVAILABLE = False
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import Status, StatusCode, set_tracer_provider

from ..core.config import TracingConfig, CorrelationConfig

if TYPE_CHECKING:
    from opentelemetry.trace import Tracer

logger = logging.getLogger(__name__)


class TracingManager:
    """Manages OpenTelemetry tracing setup and lifecycle."""

    def __init__(self, config: TracingConfig):
        """Initialize tracing manager with configuration."""
        self.config = config
        self._tracer_provider: Optional[TracerProvider] = None
        self._tracer: Optional["Tracer"] = None
        self._span_processor: Optional[BatchSpanProcessor] = None
        self._is_setup = False

    def setup(self) -> bool:
        """Set up OpenTelemetry tracing with the configured collector."""
        try:
            logger.info(f"Setting up tracing for {self.config.service_name}")
            logger.info(f"Collector URL: {self.config.collector_url}")

            # Create resource with service info
            resource_attrs = {
                "service.name": self.config.service_name,
                "service.version": self.config.service_version,
                "service.instance.id": str(uuid.uuid4()),
                "telemetry.sdk.name": "distributed-observability-tools",
                "telemetry.sdk.version": "0.1.1",
            }

            # Add custom resource attributes
            if self.config.resource_attributes:
                resource_attrs.update(self.config.resource_attributes)

            if self.config.environment:
                resource_attrs["service.environment"] = self.config.environment

            resource = Resource.create(resource_attrs)

            # Create tracer provider
            self._tracer_provider = TracerProvider(resource=resource)

            # Set sampling if configured and available
            if self.config.sampling_rate is not None and SAMPLER_AVAILABLE:
                sampler = TraceIdRatioBasedSampler(self.config.sampling_rate)
                self._tracer_provider._sampler = sampler

            # Create OTLP exporter
            exporter_kwargs = {
                "endpoint": self.config.collector_url,
                "insecure": self.config.collector_url.startswith("http://"),
            }

            logger.debug(f"Creating OTLP exporter with endpoint: {self.config.collector_url}")
            logger.debug(f"Exporter kwargs: {exporter_kwargs}")

            try:
                if self.config.collector_protocol.upper() == "HTTP":
                    # Use HTTP instead of gRPC
                    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPOTLPSpanExporter
                    exporter = HTTPOTLPSpanExporter(**exporter_kwargs)
                    logger.debug("Created HTTP OTLP exporter")
                else:
                    exporter = OTLPSpanExporter(**exporter_kwargs)
                    logger.debug("Created gRPC OTLP exporter")

                # Add span processor - use SimpleSpanProcessor for immediate export during testing
                from opentelemetry.sdk.trace.export import SimpleSpanProcessor

                # Create a custom span processor that logs exports
                class LoggingSpanProcessor(SimpleSpanProcessor):
                    def on_end(self, span):
                        logger.debug(f"Span ending: {span.name} (trace_id: {span.get_span_context().trace_id:032x})")
                        try:
                            result = super().on_end(span)
                            logger.debug(f"Span exported successfully: {span.name}")
                            return result
                        except Exception as e:
                            logger.error(f"Failed to export span {span.name}: {e}")
                            raise

                self._span_processor = LoggingSpanProcessor(exporter)
                self._tracer_provider.add_span_processor(self._span_processor)
                logger.debug("Using LoggingSpanProcessor for immediate span export with debug logging")

            except Exception as e:
                logger.error(f"Failed to create OTLP exporter: {e}")
                raise

            # Set global tracer provider
            set_tracer_provider(self._tracer_provider)

            # Create tracer
            self._tracer = trace.get_tracer(
                self.config.service_name,
                self.config.service_version,
                tracer_provider=self._tracer_provider
            )

            self._is_setup = True
            logger.info("OpenTelemetry tracing setup successful")
            return True

        except Exception as e:
            logger.warning(f"OpenTelemetry setup failed: {e}")
            logger.warning("Tracing will be disabled")
            return False

    def get_tracer(self) -> "Tracer":
        """Get the configured tracer instance."""
        if not self._is_setup or not self._tracer:
            raise RuntimeError("Tracing not initialized. Call setup() first.")
        return self._tracer

    def shutdown(self) -> None:
        """Clean shutdown of tracing resources."""
        if self._span_processor:
            self._span_processor.shutdown()
            logger.info("Tracing span processor shut down")

        if self._tracer_provider:
            self._tracer_provider.shutdown()
            logger.info("Tracer provider shut down")

    def is_ready(self) -> bool:
        """Check if tracing is properly initialized."""
        return self._is_setup and self._tracer is not None


def setup_tracing(config: TracingConfig):
    """Convenience function to initialize tracing from config.

    Returns:
        Tuple of (TracingManager, (RequestTracingMiddleware, kwargs_dict))
    """
    from ..framework.fastapi import RequestTracingMiddleware

    manager = TracingManager(config)
    success = manager.setup()  # Setup regardless of success for graceful degradation

    logger.info(f"Tracing setup {'successful' if success else 'failed with graceful degradation'}")

    # Return manager and middleware configuration - pass TracingConfig object directly
    # FastAPI's add_middleware will call: RequestTracingMiddleware(app, tracing_config=config)
    middleware_config = (RequestTracingMiddleware, {'tracing_config': config})

    return manager, middleware_config


def instrument_fastapi_app(app, config: TracingConfig = None, fastapi_config=None):
    """Instrument a FastAPI app with OpenTelemetry auto-instrumentation.

    This should be called after the FastAPI app is created and after setup_tracing().

    Args:
        app: FastAPI application instance
        config: TracingConfig instance (optional, for backward compatibility)
        fastapi_config: FastAPIConfig instance with header capture configuration
    """
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from ..core.config import FastAPIConfig

        # Make sure we have a proper tracer provider set before instrumenting
        from opentelemetry import trace
        provider = trace.get_tracer_provider()
        if hasattr(provider, '__class__') and 'Proxy' in provider.__class__.__name__:
            logger.warning("ProxyTracerProvider detected - traces may not be exported properly")

        # Use provided fastapi_config or create default
        if fastapi_config is None:
            fastapi_config = FastAPIConfig()

        logger.debug(f"Configuring header capture with {len(fastapi_config.capture_request_headers)} explicit headers "
                    f"and {len(fastapi_config.header_patterns)} patterns")

        # Configure FastAPI instrumentation to capture HTTP headers
        def request_hook(span, scope):
            """Hook to add custom attributes to FastAPI spans."""
            if span and span.is_recording():
                # Extract headers from ASGI scope
                headers = {}
                for name, value in scope.get("headers", []):
                    header_name = name.decode("latin-1").lower()
                    header_value = value.decode("latin-1")
                    headers[header_name] = header_value

                # Track if we found a correlation ID
                correlation_id = None

                # Iterate through all headers and capture based on configuration
                for header_name, header_value in headers.items():
                    # Check if this header should be captured
                    if fastapi_config.should_capture_header(header_name):
                        # Check if this header should be redacted
                        if fastapi_config.should_redact_header(header_name):
                            value_to_set = "[REDACTED]"
                            logger.debug(f"Capturing header {header_name} with redacted value")
                        else:
                            value_to_set = header_value
                            logger.debug(f"Capturing header {header_name}: {header_value}")

                        # Set the header as a span attribute
                        span.set_attribute(f"http.request.header.{header_name}", value_to_set)

                        # Check if this is a correlation ID header
                        if "correlation" in header_name or "request-id" in header_name:
                            if not correlation_id:  # Use first correlation header found
                                correlation_id = header_value
                                span.set_attribute("correlation_id", correlation_id)
                                logger.debug(f"Set correlation_id from {header_name}: {correlation_id}")

        # Instrument the app with the request hook
        FastAPIInstrumentor.instrument_app(app, server_request_hook=request_hook)
        logger.info(f"FastAPI auto-instrumentation enabled with configurable header capture "
                   f"({len(fastapi_config.capture_request_headers)} headers, "
                   f"{len(fastapi_config.header_patterns)} patterns)")
        return True
    except Exception as e:
        logger.warning(f"FastAPI auto-instrumentation setup failed: {e}")
        return False


class CorrelationManager:
    """Manages correlation ID extraction and propagation."""

    def __init__(self, config: CorrelationConfig):
        self.config = config

    def extract_correlation_id(self, headers: Dict[str, str]) -> Optional[str]:
        """Extract correlation ID from request headers."""
        for header_name in self.config.headers:
            correlation_id = headers.get(header_name.lower())
            if correlation_id:
                return correlation_id

        return None

    def generate_correlation_id(self) -> str:
        """Generate a new correlation ID."""
        return str(uuid.uuid4())

    def get_correlation_id(self, headers: Dict[str, str]) -> Optional[str]:
        """Get correlation ID from headers, generate if needed."""
        correlation_id = self.extract_correlation_id(headers)

        if not correlation_id and self.config.generate_id:
            correlation_id = self.generate_correlation_id()

        return correlation_id

    def get_propagation_headers(self, correlation_id: Optional[str]) -> Dict[str, str]:
        """Get headers for correlation ID propagation."""
        if not correlation_id or not self.config.propagation:
            return {}

        # For now, use the first configured header
        header_name = self.config.headers[0] if self.config.headers else "x-correlation-id"
        return {header_name: correlation_id}


class SpanManager:
    """Manages span instrumentation for requests."""

    def __init__(self, config: TracingConfig):
        self.config = config
        self.correlation_manager = CorrelationManager(config.correlation)

    def instrument_request_span(self, span: trace.Span, request) -> None:
        """Add SigNoz-compatible attributes to request span."""
        try:
            # Extract correlation ID from request headers
            headers = getattr(request, 'headers', {})
            if hasattr(headers, 'get'):  # If headers is dict-like
                correlation_id = self.correlation_manager.get_correlation_id(dict(headers))
            else:
                correlation_id = None

            # Primary correlation ID attribute (SigNoz compatibility)
            if correlation_id:
                span.set_attribute("correlation_id", correlation_id)

            # Standard span attributes
            if hasattr(request, 'method'):
                span.set_attribute("request.method", request.method)
            if hasattr(request, 'url'):
                span.set_attribute("request.path", str(request.url.path) if hasattr(request.url, 'path') else str(request.url))
            if hasattr(request, 'client') and request.client:
                if hasattr(request.client, 'host'):
                    span.set_attribute("client.ip", request.client.host)

            # SigNoz-compatible nested attributes
            if correlation_id:
                span.set_attribute("correlation.id", correlation_id)
                span.set_attribute("x-correlation-id", correlation_id)
                span.set_attribute("http.request.header.x-correlation-id", correlation_id)

        except Exception as e:
            logger.warning(f"Failed to instrument request span: {e}")

    def record_exception(self, span: trace.Span, exception: Exception) -> None:
        """Record exception in span."""
        span.record_exception(exception)
        span.set_status(Status(StatusCode.ERROR, str(exception)))

    def get_current_correlation_id(self) -> Optional[str]:
        """Get correlation ID from current span attributes."""
        try:
            current_span = trace.get_current_span()
            if current_span and current_span.is_recording():
                # Try to extract from span attributes
                attributes = current_span.attributes or {}
                for key in ["correlation_id", "correlation.id", "x-correlation-id"]:
                    if key in attributes:
                        return attributes[key]
        except Exception:
            pass
        return None
