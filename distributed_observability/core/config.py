"""Base configuration classes for observability components."""
import os
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod

from pydantic import BaseModel, Field, validator


class BaseConfig(BaseModel, ABC):
    """Abstract base configuration class."""

    @abstractmethod
    def get_env_vars(self) -> Dict[str, str]:
        """Get environment variable mappings for this config."""
        pass


class CorrelationConfig(BaseModel):
    """Configuration for correlation ID handling."""

    headers: List[str] = Field(
        default=["x-correlation-id", "x-request-id"],
        description="Headers to extract for correlation ID",
    )
    propagation: bool = Field(
        default=True,
        description="Whether to propagate correlation headers in outgoing requests",
    )
    generate_id: bool = Field(
        default=True,
        description="Generate correlation ID if not present",
    )


class TracingConfig(BaseConfig):
    """Configuration for distributed tracing."""

    service_name: str = Field(
        ...,
        description="Name of the service being traced",
    )
    service_version: Optional[str] = Field(
        default="1.0.0",
        description="Version of the service",
    )
    collector_url: str = Field(
        default="http://host.docker.internal:4317",
        description="OpenTelemetry collector endpoint URL",
    )
    collector_protocol: str = Field(
        default="grpc",
        description="Protocol for OTLP export (grpc|http)",
    )
    sampling_rate: Optional[float] = Field(
        default=None,
        description="Sampling rate (0.0-1.0), None for default",
        ge=0.0,
        le=1.0,
    )
    correlation: CorrelationConfig = Field(
        default_factory=CorrelationConfig,
        description="Correlation ID configuration",
    )
    environment: Optional[str] = Field(
        default_factory=lambda: os.getenv("ENVIRONMENT", "development"),
        description="Deployment environment",
    )
    resource_attributes: Dict[str, str] = Field(
        default_factory=dict,
        description="Additional resource attributes",
    )

    def get_env_vars(self) -> Dict[str, str]:
        """Get environment variable mappings."""
        return {
            "OTEL_EXPORTER_OTLP_ENDPOINT": self.collector_url,
            "OTEL_EXPORTER_OTLP_PROTOCOL": self.collector_protocol,
            "OTEL_SERVICE_NAME": self.service_name,
            "OTEL_SERVICE_VERSION": self.service_version or "1.0.0",
            "OTEL_TRACES_SAMPLER": f"traceidratio={self.sampling_rate}" if self.sampling_rate else "parentbased_always_on",
            "ENVIRONMENT": self.environment or "development",
        }


class FastAPIConfig(BaseModel):
    """Configuration for FastAPI framework integration."""

    enable_middleware: bool = Field(
        default=True,
        description="Enable automatic FastAPI middleware",
    )
    log_level: str = Field(
        default="INFO",
        description="Log level for framework logging",
    )
    record_exceptions: bool = Field(
        default=True,
        description="Whether to record exceptions in spans",
    )


class HTTPClientConfig(BaseModel):
    """Configuration for HTTP client instrumentation."""

    enable_httpx: bool = Field(
        default=True,
        description="Enable httpx client instrumentation",
    )
    instrument_requests: bool = Field(
        default=True,
        description="Enable requests library instrumentation",
    )
    capture_headers: List[str] = Field(
        default=["x-*"],
        description="HTTP headers to capture in spans",
    )


class ObservabilityConfig(BaseModel):
    """Master configuration for all observability components."""

    tracing: TracingConfig = Field(
        ...,
        description="Distributed tracing configuration",
    )
    fastapi: FastAPIConfig = Field(
        default_factory=FastAPIConfig,
        description="FastAPI framework integration config",
    )
    http_client: HTTPClientConfig = Field(
        default_factory=HTTPClientConfig,
        description="HTTP client instrumentation config",
    )

    @classmethod
    def from_env(cls) -> "ObservabilityConfig":
        """Create configuration from environment variables."""
        return cls(
            tracing=TracingConfig(
                service_name=os.getenv("SERVICE_NAME", "unknown-service"),
                collector_url=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317"),
                service_version=os.getenv("SERVICE_VERSION", "1.0.0"),
            ),
            fastapi=FastAPIConfig(),
            http_client=HTTPClientConfig(),
        )
