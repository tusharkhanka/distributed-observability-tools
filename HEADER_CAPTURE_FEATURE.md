# HTTP Header Capture Feature - Implementation Summary

## Overview

This document summarizes the implementation of configurable HTTP request header capture in OpenTelemetry spans for the `distributed-observability-tools` package.

## Feature Description

The package now supports configurable capture of HTTP request headers as OpenTelemetry span attributes, with:

- **Explicit header lists**: Specify exact headers to capture
- **Wildcard pattern matching**: Use patterns like `x-*` to capture multiple headers
- **Header redaction**: Automatically redact sensitive headers (authorization, cookies, API keys)
- **Per-framework configuration**: Different settings for FastAPI and HTTP clients
- **Backward compatibility**: Sensible defaults that work out of the box

## Implementation Details

### 1. Configuration Classes Enhanced

#### `FastAPIConfig` (distributed_observability/core/config.py)

Added three new fields:

```python
class FastAPIConfig(BaseModel):
    # ... existing fields ...
    
    capture_request_headers: List[str] = Field(
        default=[
            "x-correlation-id",
            "x-request-id",
            "correlation-id",
            "user-agent",
            "x-forwarded-for",
            "x-real-ip",
            "x-edge-location",
            "x-amz-cf-id"
        ],
        description="HTTP request headers to capture as span attributes"
    )
    
    redact_headers: List[str] = Field(
        default=["authorization", "cookie", "x-api-key", "api-key"],
        description="Headers to redact (capture but mask value for security)"
    )
    
    header_patterns: List[str] = Field(
        default=[],
        description="Wildcard patterns for headers to capture (e.g., 'x-*')"
    )
    
    def should_capture_header(self, header_name: str) -> bool:
        """Check if a header should be captured based on configuration."""
        # Implementation checks explicit list and patterns
    
    def should_redact_header(self, header_name: str) -> bool:
        """Check if a header value should be redacted."""
        # Implementation checks redact list
```

#### `HTTPClientConfig` (distributed_observability/core/config.py)

Enhanced existing `capture_headers` field and added new fields:

```python
class HTTPClientConfig(BaseModel):
    # ... existing fields ...
    
    capture_headers: List[str] = Field(
        default=[
            "x-correlation-id",
            "x-request-id",
            "user-agent",
            "content-type"
        ],
        description="HTTP headers to capture in outgoing request spans"
    )
    
    redact_headers: List[str] = Field(
        default=["authorization", "cookie", "x-api-key", "api-key"],
        description="Headers to redact in outgoing requests"
    )
    
    header_patterns: List[str] = Field(
        default=["x-*"],
        description="Wildcard patterns for headers to capture"
    )
    
    def should_capture_header(self, header_name: str) -> bool:
        """Check if a header should be captured based on configuration."""
    
    def should_redact_header(self, header_name: str) -> bool:
        """Check if a header value should be redacted."""
```

### 2. Pattern Matching Utility

Added `match_header_pattern()` function (distributed_observability/core/config.py):

```python
def match_header_pattern(header_name: str, patterns: List[str]) -> bool:
    """
    Check if a header name matches any of the given patterns.
    
    Supports wildcard patterns using fnmatch (e.g., 'x-*' matches 'x-correlation-id').
    """
    # Uses Python's fnmatch module for pattern matching
    # Case-insensitive matching
```

### 3. Request Hook Modified

Updated `request_hook` in `instrument_fastapi_app()` (distributed_observability/tracing/tracer.py):

**Before:**
- Hardcoded list of headers to capture
- Hardcoded redaction for `authorization` only

**After:**
- Configuration-driven header capture
- Pattern matching support
- Configurable redaction
- Maintains backward compatibility

```python
def instrument_fastapi_app(app, config: TracingConfig = None, fastapi_config=None):
    # ... setup code ...
    
    def request_hook(span, scope):
        """Hook to add custom attributes to FastAPI spans."""
        if span and span.is_recording():
            # Extract headers from ASGI scope
            headers = {}
            for name, value in scope.get("headers", []):
                header_name = name.decode("latin-1").lower()
                header_value = value.decode("latin-1")
                headers[header_name] = header_value
            
            # Iterate through all headers and capture based on configuration
            for header_name, header_value in headers.items():
                if fastapi_config.should_capture_header(header_name):
                    if fastapi_config.should_redact_header(header_name):
                        value_to_set = "[REDACTED]"
                    else:
                        value_to_set = header_value
                    
                    span.set_attribute(f"http.request.header.{header_name}", value_to_set)
                    
                    # Check if this is a correlation ID header
                    if "correlation" in header_name or "request-id" in header_name:
                        if not correlation_id:
                            correlation_id = header_value
                            span.set_attribute("correlation_id", correlation_id)
```

### 4. Middleware Enhanced

Updated `RequestTracingMiddleware` (distributed_observability/framework/fastapi.py):

**Before:**
- Hardcoded checks for specific headers (x-request-id, x-edge-location, x-amz-cf-id)

**After:**
- Configuration-driven header capture
- Maintains backward compatibility for CloudFront-specific attributes

```python
# Add request headers as span attributes based on configuration
for header_name, header_value in headers_dict.items():
    if not header_value or header_value == 'not-found':
        continue
    
    if self.fastapi_config.should_capture_header(header_name):
        if self.fastapi_config.should_redact_header(header_name):
            value_to_set = "[REDACTED]"
        else:
            value_to_set = header_value
        
        current_span.set_attribute(f"http.request.header.{header_name}", value_to_set)
        
        # Backward compatibility for specific headers
        if header_name == 'x-request-id':
            current_span.set_attribute("cloudfront.request_id", value_to_set)
            current_span.set_attribute("x-request-id", value_to_set)
        # ... etc
```

### 5. Exports Updated

Updated `__init__.py` to export new configuration classes and utilities:

```python
from .core.config import FastAPIConfig, HTTPClientConfig, match_header_pattern

__all__ = [
    # ... existing exports ...
    "FastAPIConfig",
    "HTTPClientConfig",
    "match_header_pattern",
]
```

## Testing

### Test Coverage

Created comprehensive test suite (`test_header_config.py`):

1. **Import Tests**: Verify all new imports work
2. **Pattern Matching Tests**: Test wildcard pattern matching with various patterns
3. **FastAPIConfig Tests**: Test default configuration and helper methods
4. **Custom Config Tests**: Test custom configuration with patterns
5. **HTTPClientConfig Tests**: Test HTTP client configuration
6. **Integration Tests**: Test TracingConfig integration
7. **Backward Compatibility Tests**: Ensure existing code still works

**All tests pass successfully!**

### Example Files

Created example files demonstrating usage:

1. **`example_usage/custom_header_example.py`**: Complete working examples with:
   - Default configuration
   - Custom header lists
   - Wildcard pattern matching
   - Security-focused configuration
   - Test endpoints

2. **`example_usage/HEADER_CAPTURE_EXAMPLES.md`**: Comprehensive documentation with:
   - Quick start guide
   - Configuration options
   - Pattern matching examples
   - Best practices
   - Troubleshooting

## Backward Compatibility

✅ **Fully backward compatible**

- Existing code continues to work without changes
- Default configuration captures the same headers as before
- No breaking changes to existing APIs
- Graceful degradation if configuration not provided

## Documentation

Updated documentation in:

1. **`README.md`**: Added sections on:
   - Custom HTTP header capture
   - Header pattern matching
   - Header redaction
   - FastAPIConfig and HTTPClientConfig examples

2. **`example_usage/HEADER_CAPTURE_EXAMPLES.md`**: Comprehensive guide

3. **`HEADER_CAPTURE_FEATURE.md`**: This implementation summary

## Usage Examples

### Basic Usage (Default Configuration)

```python
from distributed_observability import TracingConfig, setup_tracing
from fastapi import FastAPI

config = TracingConfig(service_name="my-service")
tracer_manager, middleware_config = setup_tracing(config)

app = FastAPI()
middleware_class, middleware_kwargs = middleware_config
app.add_middleware(middleware_class, **middleware_kwargs)
```

### Custom Header Capture

```python
from distributed_observability import TracingConfig, FastAPIConfig, setup_tracing
from distributed_observability.tracing.tracer import instrument_fastapi_app

tracing_config = TracingConfig(service_name="my-service")

fastapi_config = FastAPIConfig(
    capture_request_headers=["x-correlation-id", "x-tenant-id"],
    redact_headers=["authorization", "cookie"],
    header_patterns=["x-*", "*-id"]
)

tracer_manager, middleware_config = setup_tracing(tracing_config)
middleware_class, middleware_kwargs = middleware_config
middleware_kwargs['fastapi_config'] = fastapi_config

app = FastAPI()
app.add_middleware(middleware_class, **middleware_kwargs)
instrument_fastapi_app(app, tracing_config, fastapi_config)
```

## Benefits

1. **Flexibility**: Capture any custom headers needed for your use case
2. **Security**: Automatically redact sensitive headers
3. **Efficiency**: Use patterns to capture groups of headers
4. **Debugging**: Capture business-specific headers for troubleshooting
5. **Compliance**: Control what data is captured in traces

## Future Enhancements

Potential future improvements:

1. Support for response header capture
2. Dynamic header capture based on request path
3. Header transformation/normalization
4. Integration with other frameworks (Django, Flask)
5. Performance metrics for header capture overhead

