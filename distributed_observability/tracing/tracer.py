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
from opentelemetry.sdk.trace.sampling import TraceIdRatioBasedSampler
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
                "telemetry.sdk.version": "0.1.0",
            }

            # Add custom resource attributes
            if self.config.resource_attributes:
                resource_attrs.update(self.config.resource_attributes)

            if self.config.environment:
                resource_attrs["service.environment"] = self.config.environment

            resource = Resource.create(resource_attrs)

            # Create tracer provider
            self._tracer_provider = TracerProvider(resource=resource)

            # Set sampling if configured
            if self.config.sampling_rate is not None:
                sampler = TraceIdRatioBasedSampler(self.config.sampling_rate)
                self._tracer_provider._sampler = sampler

            # Create OTLP exporter
            exporter_kwargs = {
                "endpoint": self.config.collector_url,
                "insecure": self.config.collector_url.startswith("http://"),
            }

            if self.config.collector_protocol.upper() == "HTTP":
                # Use HTTP instead of gRPC
                from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter as HTTPOTLPSpanExporter
                exporter = HTTPOTLPSpanExporter(**exporter_kwargs)
            else:
                exporter = OTLPSpanExporter(**exporter_kwargs)

            # Add span processor
            self._span_processor = BatchSpanProcessor(exporter)
            self._tracer_provider.add_span_processor(self._span_processor)

            # Set global tracer provider
            set_tracer_provider(self._tracer_provider)

            # Create tracer
            self._tracer = trace.get_tracer(
                name=self.config.service_name,
                version=self.config.service_version,
                tracer_provider=self._tracer_provider
            )

            self._is_setup = True
            logger.info("✅ OpenTelemetry tracing setup successful")
            return True

        except Exception as e:
            logger.warning(f"⚠️ OpenTelemetry setup failed: {e}")
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


def setup_tracing(config: TracingConfig) -> TracingManager:
    """Convenience function to initialize tracing from config."""
    manager = TracingManager(config)
    if manager.setup():
        return manager
    else:
        # Return manager even if setup failed for graceful degradation
        return manager


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
