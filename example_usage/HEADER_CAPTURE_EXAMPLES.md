# HTTP Header Capture Configuration Examples

This directory contains examples demonstrating the configurable HTTP header capture feature in `distributed-observability-tools`.

## Overview

The package allows you to configure which HTTP request headers are captured as OpenTelemetry span attributes. This is useful for:

- **Debugging**: Capture custom business headers for troubleshooting
- **Correlation**: Track requests across services using custom correlation headers
- **Security**: Automatically redact sensitive headers like authorization tokens
- **Flexibility**: Use wildcard patterns to capture groups of headers

## Quick Start

### Run the Custom Header Example

```bash
# Install dependencies
pip install distributed-observability-tools[all]

# Run the example server
python custom_header_example.py
```

### Test with curl

```bash
# Send a request with custom headers
curl -X POST http://localhost:8000/test \
  -H "Content-Type: application/json" \
  -H "x-correlation-id: test-123" \
  -H "x-tenant-id: tenant-456" \
  -H "x-user-role: admin" \
  -H "x-custom-header: custom-value" \
  -H "authorization: Bearer secret-token" \
  -d '{"message": "test"}'
```

## Configuration Options

### 1. Explicit Header List

Specify exact headers to capture:

```python
from distributed_observability import FastAPIConfig

config = FastAPIConfig(
    capture_request_headers=[
        "x-correlation-id",
        "x-request-id",
        "user-agent",
        "x-tenant-id",      # Custom business header
        "x-user-role"       # Custom business header
    ]
)
```

### 2. Wildcard Pattern Matching

Use patterns to capture multiple headers:

```python
config = FastAPIConfig(
    header_patterns=[
        "x-*",              # Capture all headers starting with "x-"
        "*-id",             # Capture all headers ending with "-id"
        "cf-*",             # Capture all CloudFlare headers
        "cloudfront-*"      # Capture all CloudFront headers
    ]
)
```

**Pattern Examples:**

| Pattern | Matches | Examples |
|---------|---------|----------|
| `x-*` | All headers starting with "x-" | `x-correlation-id`, `x-tenant-id`, `x-custom` |
| `*-id` | All headers ending with "-id" | `tenant-id`, `request-id`, `user-id` |
| `cf-*` | All CloudFlare headers | `cf-ray`, `cf-connecting-ip` |
| `cloudfront-*` | All CloudFront headers | `cloudfront-viewer-country` |

### 3. Header Redaction

Automatically redact sensitive headers:

```python
config = FastAPIConfig(
    capture_request_headers=["x-correlation-id", "authorization"],
    redact_headers=[
        "authorization",    # OAuth tokens, Bearer tokens
        "cookie",          # Session cookies
        "x-api-key",       # API keys
        "x-secret-*"       # Any header starting with "x-secret-"
    ]
)
```

Headers in `redact_headers` will be captured as span attributes but their values will be replaced with `[REDACTED]`.

## Example Configurations

### Default Configuration (Backward Compatible)

If you don't specify any configuration, these defaults are used:

```python
FastAPIConfig(
    capture_request_headers=[
        "x-correlation-id",
        "x-request-id",
        "correlation-id",
        "user-agent",
        "x-forwarded-for",
        "x-real-ip",
        "x-edge-location",
        "x-amz-cf-id"
    ],
    redact_headers=[
        "authorization",
        "cookie",
        "x-api-key",
        "api-key"
    ],
    header_patterns=[]  # No wildcard patterns by default
)
```

### Custom Business Headers

Capture custom headers for multi-tenant applications:

```python
config = FastAPIConfig(
    capture_request_headers=[
        "x-correlation-id",
        "x-request-id",
        "x-tenant-id",          # Multi-tenancy
        "x-organization-id",    # Organization tracking
        "x-user-id",            # User tracking
        "x-user-role",          # Authorization context
        "x-api-version"         # API versioning
    ],
    header_patterns=["x-*"],
    redact_headers=["authorization", "cookie", "x-api-key"]
)
```

### Security-Focused Configuration

Minimal header capture with aggressive redaction:

```python
config = FastAPIConfig(
    capture_request_headers=[
        "x-correlation-id",
        "x-request-id",
        "user-agent"
    ],
    redact_headers=[
        "authorization",
        "cookie",
        "x-api-key",
        "api-key",
        "x-auth-token",
        "x-session-id",
        "x-csrf-token",
        "proxy-authorization"
    ],
    header_patterns=[]  # No wildcard patterns for security
)
```

### CloudFront/CloudFlare Integration

Capture CDN-specific headers:

```python
config = FastAPIConfig(
    capture_request_headers=[
        "x-correlation-id",
        "user-agent"
    ],
    header_patterns=[
        "cf-*",             # CloudFlare headers
        "cloudfront-*",     # CloudFront headers
        "x-amz-*"          # AWS headers
    ],
    redact_headers=["authorization", "cookie"]
)
```

## Testing Pattern Matching

Use the `match_header_pattern` function to test patterns:

```python
from distributed_observability import match_header_pattern

# Test if a header matches patterns
patterns = ["x-*", "*-id"]

print(match_header_pattern("x-correlation-id", patterns))  # True
print(match_header_pattern("tenant-id", patterns))         # True
print(match_header_pattern("user-agent", patterns))        # False
```

## Complete Example

See `custom_header_example.py` for a complete working example with:

- Default configuration
- Custom header lists
- Wildcard pattern matching
- Security-focused configuration
- Test endpoints

## Microservices Example

The three microservices in this directory (`user-service`, `order-service`, `inventory-service`) demonstrate distributed tracing with header capture across multiple services.

### Start the Services

```bash
# Build and start all services
docker compose up --build -d

# Check service health
curl http://localhost:9001/health
curl http://localhost:9002/health
curl http://localhost:9003/health
```

### Test Distributed Tracing

```bash
# Create an order (flows through all 3 services)
curl -X POST "http://localhost:9001/api/v1/users/1/orders" \
  -H "Content-Type: application/json" \
  -H "x-correlation-id: test-trace-123" \
  -H "x-tenant-id: tenant-456" \
  -d '{"product_name": "Laptop", "quantity": 1, "price": 999.99}'
```

The correlation ID and custom headers will be:
1. Captured in the user-service span
2. Propagated to order-service
3. Propagated to inventory-service
4. Visible in your tracing backend (SigNoz, Jaeger, etc.)

## Viewing Captured Headers

Headers are captured as span attributes with the prefix `http.request.header.`:

- `http.request.header.x-correlation-id`
- `http.request.header.x-tenant-id`
- `http.request.header.user-agent`
- etc.

In your tracing backend (SigNoz, Jaeger, etc.), you can:

1. Filter traces by header values
2. Search for specific correlation IDs
3. View all captured headers in span details
4. Create dashboards based on custom headers

## Best Practices

1. **Start with defaults**: The default configuration captures common headers
2. **Use patterns sparingly**: Too many patterns can capture sensitive data
3. **Always redact sensitive headers**: Include `authorization`, `cookie`, `x-api-key`
4. **Document custom headers**: Make sure your team knows which headers are captured
5. **Test in development**: Verify headers are captured correctly before production
6. **Monitor span size**: Too many headers can increase span size and costs

## Troubleshooting

### Headers not appearing in spans

1. Check that the header is in `capture_request_headers` or matches a pattern
2. Verify the header is not being filtered by middleware
3. Check that the header name is lowercase in configuration

### Sensitive data in spans

1. Add the header to `redact_headers`
2. Use pattern matching for groups of sensitive headers (e.g., `x-secret-*`)
3. Review captured headers regularly

### Pattern not matching

1. Patterns are case-insensitive
2. Use `match_header_pattern()` to test patterns
3. Remember that `*` matches any characters, not just one

## Additional Resources

- [OpenTelemetry Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/http/)
- [SigNoz Documentation](https://signoz.io/docs/)
- [Package README](../README.md)

