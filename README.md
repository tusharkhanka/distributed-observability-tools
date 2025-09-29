# Distributed Observability Tools

A comprehensive Python package for observability in distributed systems, providing distributed tracing with correlation ID propagation and framework integrations.

![PyPI](https://img.shields.io/pypi/v/distributed-observability-tools)
![Python](https://img.shields.io/pypi/pyversions/distributed-observability-tools)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 Quick Start

### Basic Usage

```python
from distributed_observability import TracingConfig, setup_tracing
from fastapi import FastAPI

# Configure tracing
config = TracingConfig(
    service_name="my-service",
    collector_url="http://otel-collector:4317"
)

# Setup tracing
tracer_manager, middleware = setup_tracing(config)

# Add to FastAPI app
app = FastAPI()
app.add_middleware(middleware)
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

# Create correlated client
client = instrument_httpx_client()

# All requests will include correlation headers automatically
response = await client.get("http://api.example.com/users")
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
