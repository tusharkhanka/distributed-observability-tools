# Distributed Observability Tools

A comprehensive Python package for observability in distributed systems, providing distributed tracing with correlation ID propagation and framework integrations.

![PyPI](https://img.shields.io/pypi/v/distributed-observability-tools)
![Python](https://img.shields.io/pypi/pyversions/distributed-observability-tools)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Quick Start

### Installation

```bash
# Basic installation (core tracing only)
pip install distributed-observability-tools

# With FastAPI support (REQUIRED for HTTP request tracing)
pip install distributed-observability-tools[fastapi]

# With HTTP client support
pip install distributed-observability-tools[httpx]

# Full installation (all features)
pip install distributed-observability-tools[all]
```

> **⚠️ Important**: For FastAPI applications, you **must** install with the `[fastapi]` extras to enable HTTP request tracing. Without this, only database and other instrumentations will work, but HTTP spans will not be created.

### Basic Usage

```python
from distributed_observability import TracingConfig, setup_tracing

# Configure tracing
config = TracingConfig(
    service_name="my-service",
    collector_url="http://otel-collector:4317"
)

# Setup tracing
tracer_manager, middleware = setup_tracing(config)
```

### FastAPI Integration

**New in v0.1.3**: Automatic FastAPI instrumentation! 🎉

```python
from distributed_observability import TracingConfig, FastAPIConfig, setup_tracing
from fastapi import FastAPI

# Configure tracing
config = TracingConfig(
    service_name="my-service",
    collector_url="http://otel-collector:4317"
)

# Configure header capture (optional)
fastapi_config = FastAPIConfig(
    capture_request_headers=["x-correlation-id", "user-agent"]
)

# Create FastAPI app
app = FastAPI()

# Setup tracing with automatic instrumentation (recommended)
tracer_manager, middleware = setup_tracing(
    config,
    app=app,  # Pass app for auto-instrumentation
    fastapi_config=fastapi_config
)

# Add middleware for correlation ID propagation
middleware_class, middleware_kwargs = middleware
app.add_middleware(middleware_class, **middleware_kwargs)
```

**What this does**:
- ✅ Creates HTTP request spans (GET /api/users, POST /api/orders, etc.)
- ✅ Captures HTTP method, status code, URL path
- ✅ Extracts and propagates correlation IDs from headers
- ✅ Instruments database queries (SQLAlchemy, Redis, etc.)
- ✅ Creates complete distributed trace trees

**Manual instrumentation** (advanced users):

```python
from distributed_observability import TracingConfig, setup_tracing
from distributed_observability.tracing.tracer import instrument_fastapi_app
from fastapi import FastAPI

config = TracingConfig(service_name="my-service")

# Setup tracing first
tracer_manager, middleware = setup_tracing(config)

# Create app
app = FastAPI()

# Manually instrument FastAPI
instrument_fastapi_app(app, config, fastapi_config)

# Add middleware
middleware_class, middleware_kwargs = middleware
app.add_middleware(middleware_class, **middleware_kwargs)
```

### Advanced Configuration

```python
from distributed_observability import TracingConfig, CorrelationConfig
from fastapi import FastAPI

# Advanced configuration
config = TracingConfig(
    service_name="my-service",
    service_version="1.2.3",
    collector_url="http://otel-collector:4317",
    sampling_rate=0.1,  # 10% sampling
    correlation=CorrelationConfig(
        headers=["x-correlation-id", "x-request-id"],
        propagation=True
    ),
    environment="production"
)

# Setup with custom middleware
from distributed_observability.framework import RequestTracingMiddleware
from distributed_observability.core import FastAPIConfig

fastapi_config = FastAPIConfig(
    enable_middleware=True,
    record_exceptions=True
)

app = FastAPI()
app.add_middleware(RequestTracingMiddleware, tracing_config=config, fastapi_config=fastapi_config)
```

### Custom HTTP Header Capture

Configure which HTTP request headers are captured as OpenTelemetry span attributes:

```python
from distributed_observability import TracingConfig, FastAPIConfig, setup_tracing
from distributed_observability.tracing.tracer import instrument_fastapi_app
from fastapi import FastAPI

# Configure tracing
tracing_config = TracingConfig(
    service_name="my-service",
    collector_url="http://otel-collector:4317"
)

# Configure custom header capture
fastapi_config = FastAPIConfig(
    enable_middleware=True,
    # Explicit list of headers to capture
    capture_request_headers=[
        "x-correlation-id",
        "x-request-id",
        "user-agent",
        "x-tenant-id",      # Custom business header
        "x-user-role",      # Custom business header
    ],
    # Headers to redact (captured but value masked)
    redact_headers=[
        "authorization",
        "cookie",
        "x-api-key"
    ],
    # Wildcard patterns for header matching
    header_patterns=[
        "x-*",              # Capture all headers starting with "x-"
        "*-id",             # Capture all headers ending with "-id"
        "cf-*"              # Capture all CloudFlare headers
    ]
)

# Setup tracing
tracer_manager, middleware_config = setup_tracing(tracing_config)
middleware_class, middleware_kwargs = middleware_config

# Add custom FastAPIConfig to middleware
middleware_kwargs['fastapi_config'] = fastapi_config

app = FastAPI()
app.add_middleware(middleware_class, **middleware_kwargs)

# Instrument FastAPI with custom config
instrument_fastapi_app(app, tracing_config, fastapi_config)
```

**Header Pattern Matching:**

The `header_patterns` field supports wildcard patterns using `fnmatch` syntax:

- `x-*` - Matches all headers starting with "x-" (e.g., `x-correlation-id`, `x-tenant-id`)
- `*-id` - Matches all headers ending with "-id" (e.g., `tenant-id`, `request-id`)
- `cf-*` - Matches all CloudFlare headers (e.g., `cf-ray`, `cf-connecting-ip`)
- `cloudfront-*` - Matches all CloudFront headers

**Header Redaction:**

Headers listed in `redact_headers` will be captured as span attributes but their values will be replaced with `[REDACTED]` for security. This is useful for sensitive headers like:

- `authorization` - OAuth tokens, API keys
- `cookie` - Session cookies
- `x-api-key` - API authentication keys
- `x-secret-*` - Any custom secret headers

**Default Configuration:**

If no `FastAPIConfig` is provided, the following defaults are used:

```python
# Default headers captured
capture_request_headers = [
    "x-correlation-id",
    "x-request-id",
    "correlation-id",
    "user-agent",
    "x-forwarded-for",
    "x-real-ip",
    "x-edge-location",
    "x-amz-cf-id"
]

# Default headers redacted
redact_headers = [
    "authorization",
    "cookie",
    "x-api-key",
    "api-key"
]

# Default patterns (empty - no wildcard matching)
header_patterns = []
```

## 📦 Installation

### Basic Installation

```bash
pip install distributed-observability-tools
```

### With HTTP Client Support

```bash
pip install distributed-observability-tools[httpx]
```

### Development Installation

```bash
git clone https://github.com/your-org/distributed-observability-tools.git
cd distributed-observability-tools
poetry install  # or pip install -e .
```

## 🔧 Features

### ✅ Distributed Tracing
- OpenTelemetry-based tracing with SigNoz compatibility
- Automatic span creation for HTTP requests
- Configurable sampling and resource attributes
- Graceful degradation when collector unavailable

### ✅ Correlation ID Propagation
- Automatic correlation ID extraction from headers
- Cross-service correlation ID propagation
- SigNoz-compatible span attributes (`correlation_id`)
- Multiple header format support

### ✅ Configurable Header Capture
- **Explicit Header Lists**: Specify exact headers to capture
- **Wildcard Pattern Matching**: Use patterns like `x-*` to capture multiple headers
- **Header Redaction**: Automatically redact sensitive headers (authorization, cookies, API keys)
- **Per-Framework Configuration**: Different settings for FastAPI and HTTP clients
- **Backward Compatible**: Sensible defaults that work out of the box

### ✅ Framework Integration
- **FastAPI**: Automatic middleware for request tracing
- **HTTP Clients**: httpx instrumentation for call propagation
- **Extensible**: Clean architecture for adding frameworks

### ✅ Production Ready
- Comprehensive error handling and logging
- Environment-based configuration
- Clean resource management and shutdown
- Performance optimized with minimal overhead

## 🏗️ Architecture

```
distributed_observability/
├── core/           # Configuration and base classes
├── tracing/        # Core tracing functionality
├── framework/      # Framework-specific integrations
└── utils/          # Utility functions and helpers
```

## 📚 API Reference

### Core Classes

#### TracingConfig

```python
from distributed_observability import TracingConfig

config = TracingConfig(
    service_name="my-service",                    # Required: Your service name
    collector_url="http://otel-collector:4317",   # Default OTLP endpoint
    collector_protocol="grpc",                    # or "http"
    sampling_rate=1.0,                            # Optional: 0.0-1.0 sampling
    environment="development",                    # Optional: deployment env
    resource_attributes={"team": "backend"}       # Optional: custom attributes
)
```

#### CorrelationConfig

```python
from distributed_observability.core import CorrelationConfig

correlation = CorrelationConfig(
    headers=["x-correlation-id", "x-request-id"],  # Headers to check
    propagation=True,                              # Propagate IDs
    generate_id=True                               # Generate ID if missing
)
```

### Setup Functions

#### setup_tracing()

```python
from distributed_observability import setup_tracing

# Returns (TracingManager, RequestTracingMiddleware)
tracer_manager, middleware = setup_tracing(config)
```

#### Framework Integration

```python
from distributed_observability.framework.fastapi import RequestTracingMiddleware

# Add custom middleware
app.add_middleware(RequestTracingMiddleware,
                  tracing_config=config,
                  fastapi_config=FastAPIConfig())
```

#### HTTP Client Instrumentation

```python
from distributed_observability.utils import instrument_httpx_client
from distributed_observability import HTTPClientConfig

# Create correlated client with custom header capture
http_config = HTTPClientConfig(
    enable_httpx=True,
    capture_headers=[
        "x-correlation-id",
        "x-request-id",
        "user-agent"
    ],
    redact_headers=["authorization", "cookie"],
    header_patterns=["x-*"]  # Capture all x- headers
)

client = instrument_httpx_client()

# All requests will include correlation headers automatically
response = await client.get("http://api.example.com/users")
```

#### FastAPIConfig

Configure header capture for incoming requests:

```python
from distributed_observability import FastAPIConfig

fastapi_config = FastAPIConfig(
    enable_middleware=True,
    record_exceptions=True,
    # Headers to capture as span attributes
    capture_request_headers=[
        "x-correlation-id",
        "x-request-id",
        "user-agent",
        "x-tenant-id",
        "x-user-role"
    ],
    # Headers to redact (capture but mask value)
    redact_headers=[
        "authorization",
        "cookie",
        "x-api-key"
    ],
    # Wildcard patterns for header matching
    header_patterns=[
        "x-*",      # All headers starting with x-
        "*-id",     # All headers ending with -id
        "cf-*"      # All CloudFlare headers
    ]
)
```

#### HTTPClientConfig

Configure header capture for outgoing requests:

```python
from distributed_observability import HTTPClientConfig

http_config = HTTPClientConfig(
    enable_httpx=True,
    # Headers to capture in outgoing request spans
    capture_headers=[
        "x-correlation-id",
        "x-request-id",
        "user-agent",
        "content-type"
    ],
    # Headers to redact in outgoing requests
    redact_headers=[
        "authorization",
        "cookie",
        "x-api-key"
    ],
    # Wildcard patterns (default includes x-*)
    header_patterns=["x-*"]
)
```

## 🎯 Usage Examples

### FastAPI Service

```python
from fastapi import FastAPI, Request, Response
from distributed_observability import TracingConfig, setup_tracing
from distributed_observability.framework.fastapi import get_current_correlation_id

# Setup tracing
config = TracingConfig(service_name="order-service")
tracer_manager, middleware = setup_tracing(config)

app = FastAPI()
app.add_middleware(middleware)

@app.get("/orders")
async def get_orders(request: Request):
    # Access correlation ID in handlers
    correlation_id = get_current_correlation_id()

    # Your business logic here
    return {"orders": [], "correlation_id": correlation_id}
```

### Inter-Service Communication

```python
import httpx
from distributed_observability.utils import CorrelatedClient, patch_httpx

# Option 1: Auto-patch httpx (all clients get correlation headers)
patch_httpx()

# Now all httpx requests include correlation headers
async with httpx.AsyncClient() as client:
    response = await client.get("http://inventory-service/api/items")

# Option 2: Explicit correlated client
from distributed_observability.utils import instrument_httpx_client

client = instrument_httpx_client()
response = await client.post("http://user-service/api/users", json={"name": "John"})
```

### Environment Configuration

Create a configuration file `.env`:

```bash
SERVICE_NAME=my-microservice
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
ENVIRONMENT=production
SAMPLING_RATE=0.1
```

```python
from distributed_observability.core import ObservabilityConfig

# Load from environment
config = ObservabilityConfig.from_env()
runner = setup_tracing(config.tracing)
```

## 🔍 SigNoz Dashboard Integration

### Query for Correlated Requests

```sql
-- Find all spans with a specific correlation ID
SELECT *
FROM signoz_traces.distributed_signoz_index_v3
WHERE mapContains(attributes_string, 'correlation_id')
  AND attributes_string['correlation_id'] = 'your-correlation-id'
ORDER BY timestamp ASC
```

### Service Timeline Dashboard

```sql
-- Timeline view of correlated requests
SELECT
    timestamp AS timestamp_datetime,
    trace_id,
    name AS operation_name,
    duration_nano / 1000000 AS duration_ms,
    attributes_string['correlation_id'] AS correlation_id,
    multiIf(resource.`service.name` IS NOT NULL,
            resource.`service.name`::String,
            resources_string['service.name'],
            'unknown') AS service_name
FROM signoz_traces.distributed_signoz_index_v3
WHERE mapContains(attributes_string, 'correlation_id')
  AND attributes_string['correlation_id'] != ''
ORDER BY timestamp ASC
```

### Error Correlation Analysis

```sql
-- Errors grouped by correlation ID
SELECT
    attributes_string['correlation_id'] AS correlation_id,
    countIf(status_code = 2) AS error_count,
    arrayStringConcat(groupUniqArray(if(status_code = 2, name, null)), ', ') AS error_operations
FROM signoz_traces.distributed_signoz_index_v3
WHERE mapContains(attributes_string, 'correlation_id')
  AND status_code = 2
GROUP BY correlation_id
ORDER BY error_count DESC
```

## ⚙️ Configuration Options

### TracingConfig Options

All available configuration options:

```python
TracingConfig(
    service_name="required-service-name",
    service_version="1.0.0",                    # Default: "1.0.0"
    collector_url="http://otel-collector:4317", # Default: "http://host.docker.internal:4317"
    collector_protocol="grpc",                  # "grpc" or "http"
    sampling_rate=1.0,                          # 0.0 to 1.0, None for default
    correlation=CorrelationConfig(...),        # Correlation configuration
    environment="development",                  # Environment name
    resource_attributes={"team": "backend"},    # Custom resource attributes
)
```

### Environment Variables

```bash
# Tracing Configuration
SERVICE_NAME=my-service
SERVICE_VERSION=1.0.0
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
OTEL_EXPORTER_OTLP_PROTOCOL=grpc
SAMPLING_RATE=1.0
ENVIRONMENT=production

# Correlation Configuration
CORRELATION_HEADERS=x-correlation-id,x-request-id
CORRELATION_PROPAGATION=true
CORRELATION_GENERATE_ID=true
```

## 🔧 Development

### Running Tests

```bash
# Install development dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Run with coverage
poetry run pytest --cov=distributed_observability tests/
```

### Code Quality

```bash
# Format code
poetry run black .

# Type checking
poetry run mypy distributed_observability

# Sort imports
poetry run isort .
```

### Building and Publishing

```bash
# Build package
poetry build

# Publish to PyPI
poetry publish
```

## 📋 Dependencies

### Core Dependencies

- `opentelemetry-sdk >= 1.21.0` - OpenTelemetry core
- `opentelemetry-exporter-otlp-proto-grpc >= 1.21.0` - OTLP export
- `opentelemetry-instrumentation-fastapi >= 0.42b0` - FastAPI integration
- `opentelemetry-instrumentation-httpx >= 0.42b0` - HTTP client integration
- `pydantic >= 2.5.0` - Configuration validation

### Optional Dependencies

- `httpx >= 0.25.0` - HTTP client wrapper support

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙋 Support

- 📚 [Documentation](https://distributed-observability-tools.readthedocs.io/)
- 🐛 [Issues](https://github.com/your-org/distributed-observability-tools/issues)
- 💬 [Discussions](https://github.com/your-org/distributed-observability-tools/discussions)

## 🎉 Acknowledgments

- OpenTelemetry community for the excellent observability standards
- FastAPI community for the amazing web framework
- SigNoz for the comprehensive observability platform

---

**Ready to make your distributed systems observable! 🚀**
