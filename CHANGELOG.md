# Changelog

All notable changes to the distributed-observability-tools package will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.3] - 2025-10-06

### Added
- **Automatic FastAPI Instrumentation**: `setup_tracing()` now accepts optional `app` and `fastapi_config` parameters to automatically instrument FastAPI applications
- When `app` is provided to `setup_tracing()`, FastAPI HTTP request tracing is automatically enabled via `FastAPIInstrumentor.instrument_app()`
- Clear error messages when `opentelemetry-instrumentation-fastapi` package is not installed
- Comprehensive test suite for auto-instrumentation feature (`test_auto_instrumentation.py`)
- Enhanced documentation in README.md with installation requirements and usage examples
- Migration guide section for upgrading from v0.1.2 to v0.1.3 in MIGRATION_GUIDE.md

### Changed
- `setup_tracing()` function signature now includes optional `app` and `fastapi_config` parameters
- Updated README.md to emphasize the requirement of `[fastapi]` extras for HTTP request tracing
- Updated MIGRATION_GUIDE.md with detailed v0.1.2 → v0.1.3 migration instructions
- Improved error handling with specific ImportError messages for missing dependencies

### Fixed
- **Critical**: HTTP request spans were not being created when using only `setup_tracing()` without manually calling `instrument_fastapi_app()`
- Correlation IDs were not being captured in HTTP spans when FastAPI instrumentation was missing
- Silent failure when `opentelemetry-instrumentation-fastapi` was not installed

### Documentation
- Added clear warning in README.md about requiring `[fastapi]` extras for HTTP tracing
- Added "What's New in v0.1.3" section with auto-instrumentation examples
- Added troubleshooting section for common issues (missing HTTP spans, correlation IDs not captured)
- Added migration checklist for upgrading from v0.1.2

### Backward Compatibility
- ✅ Fully backward compatible with v0.1.2
- Existing code using `setup_tracing(config)` without `app` parameter continues to work
- No breaking changes to existing APIs

### Migration Notes
To take advantage of automatic HTTP request tracing in v0.1.3:

1. **Update installation** to include `[fastapi]` extras:
   ```bash
   pip install distributed-observability-tools[fastapi]>=0.1.3
   ```

2. **Update code** to pass `app` to `setup_tracing()`:
   ```python
   # Before (v0.1.2)
   manager, middleware = setup_tracing(config)
   app = FastAPI()
   
   # After (v0.1.3)
   app = FastAPI()
   manager, middleware = setup_tracing(config, app=app, fastapi_config=fastapi_config)
   ```

See MIGRATION_GUIDE.md for complete migration instructions.

---

## [0.1.2] - 2025-10-05

### Added
- FastAPI dependency constraint updated to `>=0.104.0,<1.0.0` for broader compatibility
- Support for FastAPI versions 0.104.0 through 0.115.x

### Changed
- Relaxed FastAPI version constraint to support newer versions
- Updated package metadata and dependencies

### Fixed
- Compatibility issues with FastAPI 0.115.x

---

## [0.1.1] - 2025-10-04

### Added
- Configurable HTTP header capture for FastAPI applications
- `FastAPIConfig` class for controlling which headers are captured as span attributes
- Pattern-based header matching with wildcards (e.g., `x-*`, `*-id`)
- Header redaction support for sensitive headers (e.g., `authorization`, `cookie`)
- `HTTPClientConfig` for HTTP client header capture configuration
- Comprehensive header capture examples and documentation

### Changed
- Enhanced `instrument_fastapi_app()` with configurable header capture via `request_hook`
- Improved correlation ID extraction to support multiple header patterns
- Updated documentation with header capture examples

### Documentation
- Added HEADER_CAPTURE_FEATURE.md with detailed feature documentation
- Added example_usage/HEADER_CAPTURE_EXAMPLES.md with practical examples
- Updated README.md with header capture configuration examples

---

## [0.1.0] - 2025-10-03

### Added
- Initial release of distributed-observability-tools package
- Core OpenTelemetry tracing setup with `TracingConfig` and `setup_tracing()`
- FastAPI integration with `RequestTracingMiddleware`
- Correlation ID extraction and propagation
- Support for multiple correlation ID headers
- OTLP exporter for gRPC and HTTP protocols
- SQLAlchemy, Redis, Boto3, and gRPC instrumentation support
- Celery distributed task tracing
- HTTPX client instrumentation
- Configurable sampling rates
- Environment-based configuration
- Graceful degradation when tracing setup fails
- Comprehensive documentation and examples

### Framework Support
- FastAPI (with optional extras)
- SQLAlchemy (database tracing)
- Redis (cache tracing)
- Celery (task tracing)
- HTTPX (HTTP client tracing)
- gRPC (client and server tracing)
- Boto3 (AWS SDK tracing)

### Documentation
- README.md with quick start guide
- MIGRATION_GUIDE.md for migrating from embedded middleware
- PUBLISHING_GUIDE.md for package publishing workflow
- Example applications demonstrating distributed tracing
- Comprehensive API documentation

---

## Release Notes

### v0.1.3 Highlights

**🎉 Major Enhancement: Automatic FastAPI Instrumentation**

This release makes it significantly easier to set up distributed tracing for FastAPI applications. Simply pass your FastAPI app to `setup_tracing()` and HTTP request tracing is automatically enabled!

**Before (v0.1.2)**:
```python
manager, middleware = setup_tracing(config)
app = FastAPI()
# ❌ HTTP spans not created - missing manual instrumentation step
```

**After (v0.1.3)**:
```python
app = FastAPI()
manager, middleware = setup_tracing(config, app=app, fastapi_config=fastapi_config)
# ✅ HTTP spans automatically created!
```

**What You Get**:
- ✅ HTTP request spans (GET /api/users, POST /api/orders, etc.)
- ✅ HTTP attributes (method, status code, URL path)
- ✅ Correlation ID capture from headers
- ✅ Complete distributed trace trees
- ✅ Database and Redis span instrumentation

**Important**: Make sure to install with `[fastapi]` extras:
```bash
pip install distributed-observability-tools[fastapi]>=0.1.3
```

See MIGRATION_GUIDE.md for complete upgrade instructions.

---

[0.1.3]: https://github.com/tusharkhanka/distributed-observability-tools/releases/tag/v0.1.3
[0.1.2]: https://github.com/tusharkhanka/distributed-observability-tools/releases/tag/v0.1.2
[0.1.1]: https://github.com/tusharkhanka/distributed-observability-tools/releases/tag/v0.1.1
[0.1.0]: https://github.com/tusharkhanka/distributed-observability-tools/releases/tag/v0.1.0

