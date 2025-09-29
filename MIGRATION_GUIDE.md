# Migration Guide: From Embedded Middleware to Distributed Observability Package

This guide shows how to migrate from the embedded middleware in `POC-docker-only/shared/middleware.py` to the new production-grade `distributed-observability-tools` package.

## 🚀 Quick Migration Overview

**Before (embedded middleware):**
- 400+ lines of embedded middleware code
- Manual configuration per service
- Limited reusability
- Basic error handling

**After (production package):**
- Clean, reusable package
- Environment-based configuration
- Comprehensive error handling
- Production-ready features
- Extensible for future observability components

## 📦 Installation

Install the new package:

```bash
# Install core tracing functionality
pip install distributed-observability-tools

# Optional: Install with HTTP client support
pip install distributed-observability-tools[httpx]
```

## 🔄 Service Migration Examples

### User Service Migration

**Before (POC-docker-only/user-service/main.py):**

```python
# OLD: Manual imports and complex setup
import os
import sys
sys.path.append('/app')
sys.path.append('/app/shared')
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from shared.middleware import RequestLoggingMiddleware, StructuredJSONFormatter

# Manual setup_otel function
def setup_otel():
    # 30+ lines of setup logic...

# Complex FastAPI setup
app.add_middleware(RequestLoggingMiddleware,
                  service_name=SERVICE_NAME,
                  service_port=SERVICE_PORT,
                  log_level="INFO")
```

**After (with distributed-observability-tools):**

```python
# NEW: Clean, minimal setup
from distributed_observability import TracingConfig, setup_tracing

# Configure tracing (just 5 lines!)
config = TracingConfig(
    service_name="user-service",
    collector_url="http://host.docker.internal:4317"
)

# Setup tracing (one line!)
tracer_manager, middleware = setup_tracing(config)

# Add to FastAPI (one line!)
app.add_middleware(middleware)

# That's it! 🎉
```

### Order Service Migration

**Before:**

```python
# Manual correlation ID propagation in HTTP client calls
async with httpx.AsyncClient() as client:
    # No automatic correlation propagation
    response = await client.get(f"{ORDER_SERVICE_URL}/api/v1/orders/user/{user_id}")
```

**After:**

```python
from distributed_observability.utils import patch_httpx

# Auto-patch httpx for correlation propagation (one line!)
patch_httpx()

# Now ALL httpx calls include correlation headers automatically!
async with httpx.AsyncClient() as client:
    response = await client.get(f"{ORDER_SERVICE_URL}/api/v1/orders/user/{user_id}")
```

### Docker Configuration Cleanup

**Before (POC-docker-only/docker-compose.yml):**
- Each service had duplicate environment variables
- Manual OTLP endpoint configuration
- No environment-based configuration

**After (POC-docker-only/docker-compose.yml):**

```yaml
# Much cleaner! Most config now comes from environment variables
services:
  user-service:
    # Core environment
    environment:
      - SERVICE_NAME=user-service
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://host.docker.internal:4317
    # That's all that's needed! 🎯
```

## 🛠️ Detailed Migration Steps

### Step 1: Replace Dependencies

Update `requirements.txt` in each service:

**Before:**
```
opentelemetry-distro
opentelemetry-exporter-otlp-proto-grpc
opentelemetry-instrumentation-fastapi
opentelemetry-instrumentation-httpx
```

**After:**
```
distributed-observability-tools[httpx]  # One dependency replaces five!
```

### Step 2: Update Service Code

#### Inventory Service (POC-docker-only/inventory-service/main.py)

```python
# BEFORE: Complex embedded setup
from shared.middleware import RequestLoggingMiddleware
from distributed_observability import TracingConfig, setup_tracing

def create_app():
    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware, ...)  # Complex config

# AFTER: Clean, simple setup
from distributed_observability import TracingConfig, setup_tracing

def create_app():
    config = TracingConfig(service_name="inventory-service")
    tracer_manager, middleware = setup_tracing(config)

    app = FastAPI()
    app.add_middleware(middleware)  # That's it!
    return app
```

#### Order Service (POC-docker-only/order-service/main.py)

```python
# BEFORE: Manual correlation handling
async with httpx.AsyncClient() as client:
    # Extract and inject correlation headers manually
    headers_to_propagate = {...}
    await client.get(url, headers=headers_to_propagate)

# AFTER: Automatic correlation propagation
from distributed_observability.utils import patch_httpx

# Call once at startup
patch_httpx()

# All calls now include correlation headers automatically!
async with httpx.AsyncClient() as client:
    await client.get(url)  # Headers added automatically
```

### Step 3: Remove Shared Middleware

Remove the `POC-docker-only/shared/` directory entirely - no longer needed!

### Step 4: Environment Configuration

Create `.env` files for each service:

**`.env` (user-service):**
```bash
SERVICE_NAME=user-service
OTEL_EXPORTER_OTLP_ENDPOINT=http://host.docker.internal:4317
ENVIRONMENT=development
```

**`.env` (order-service):**
```bash
SERVICE_NAME=order-service
OTEL_EXPORTER_OTLP_ENDPOINT=http://host.docker.internal:4317
ENVIRONMENT=development
```

**`.env` (inventory-service):**
```bash
SERVICE_NAME=inventory-service
OTEL_EXPORTER_OTLP_ENDPOINT=http://host.docker.internal:4317
ENVIRONMENT=development
```

### Step 5: Advanced Configuration (Optional)

For more control, use advanced configuration:

```python
from distributed_observability import TracingConfig, CorrelationConfig

config = TracingConfig(
    service_name="user-service",
    sampling_rate=0.1,  # 10% sampling in production
    correlation=CorrelationConfig(
        headers=["x-correlation-id", "x-request-id", "x-trace-id"],
        propagation=True
    ),
    resource_attributes={
        "team": "backend",
        "version": "1.2.3"
    }
)
```

## 📊 Feature Comparison

| Feature | Before (Embedded) | After (Package) |
|---------|-------------------|-----------------|
| **Setup Complexity** | 50+ lines per service | 5 lines per service |
| **Correlation Propagation** | Manual setup required | Automatic via patching |
| **Configuration** | Hardcoded per service | Environment-based |
| **Error Handling** | Basic | Comprehensive |
| **Code Duplication** | High (shared/middleware.py) | Low (reusable package) |
| **Testing** | Difficult | Isolated and testable |
| **Extensibility** | Limited | Future-ready architecture |
| **Maintenance** | Manual across services | Centralized package |

## 🔍 Verification After Migration

Test correlation ID propagation:

```bash
# Test cross-service flow with correlation ID
curl -v -X POST http://localhost:9001/api/v1/users/1/orders \
  -H "Content-Type: application/json" \
  -H "x-correlation-id: test-migration-123" \
  -d '{"product_name": "Laptop", "quantity": 1}'
```

Should see in logs:
- User Service: `🎯 CORRELATION ID DETECTED: test-migration-123`
- Order Service: `🎯 CORRELATION ID DETECTED: test-migration-123`
- Inventory Service: `🎯 CORRELATION ID DETECTED: test-migration-123`

## 🚀 Benefits of Migration

### 1. **Reduced Complexity**
- 80% reduction in setup code per service
- No more embedded middleware copying
- Single dependency replaces multiple libraries

### 2. **Improved Maintainability**
- Centralized error handling and logging
- Environment-based configuration
- Automatic feature updates via package

### 3. **Production Ready**
- Graceful collector failure handling
- Resource cleanup and shutdown hooks
- Performance optimizations

### 4. **Future Extensions**
- Ready for logging module addition
- Ready for metrics collection
- Extensible framework support

### 5. **Developer Experience**
- Clear API with excellent documentation
- Type-safe configuration with Pydantic
- Comprehensive examples and migration guides

## 🎯 Migration Checklist

- [ ] Install `distributed-observability-tools` package
- [ ] Remove `POC-docker-only/shared/` directory
- [ ] Replace embedded middleware calls with package functions
- [ ] Add environment variable configuration
- [ ] Update `requirements.txt` files
- [ ] Test correlation ID propagation
- [ ] Verify traces are still collected
- [ ] Deploy and monitor for issues

## ❓ Troubleshooting

### Correlation IDs not propagating?
```python
# Check that patch_httpx() was called at startup
from distributed_observability.utils import patch_httpx
patch_httpx()  # Call this early in your app startup
```

### Configuration not loading?
```python
# Check environment variables
import os
print("SERVICE_NAME:", os.getenv("SERVICE_NAME"))
print("OTEL_EXPORTER_OTLP_ENDPOINT:", os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"))
```

### Collapsing imports?
```python
# Fully qualified imports if needed
from distributed_observability.core.config import TracingConfig
from distributed_observability.tracing.tracer import setup_tracing
```

---

**Ready to migrate? The package provides the same functionality with dramatically improved developer experience! 🚀**
