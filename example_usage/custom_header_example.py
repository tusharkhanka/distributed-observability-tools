"""
Example demonstrating custom HTTP header capture configuration.

This example shows how to configure which HTTP request headers are captured
as OpenTelemetry span attributes, including:
- Explicit header lists
- Wildcard pattern matching
- Header redaction for sensitive data
"""
import os
from fastapi import FastAPI, Request
from pydantic import BaseModel

# Import distributed observability tools
from distributed_observability import (
    TracingConfig,
    FastAPIConfig,
    setup_tracing,
    match_header_pattern
)
from distributed_observability.tracing.tracer import instrument_fastapi_app


# Example 1: Default Configuration (Backward Compatible)
def create_app_with_defaults():
    """Create app with default header capture configuration."""
    app = FastAPI(title="Default Header Capture Example")
    
    # Default configuration captures standard headers
    config = TracingConfig(
        service_name="default-header-service",
        collector_url=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    )
    
    tracer_manager, middleware_config = setup_tracing(config)
    middleware_class, middleware_kwargs = middleware_config
    app.add_middleware(middleware_class, **middleware_kwargs)
    
    # Default FastAPIConfig will be used
    instrument_fastapi_app(app, config)
    
    return app


# Example 2: Custom Header List
def create_app_with_custom_headers():
    """Create app with custom list of headers to capture."""
    app = FastAPI(title="Custom Header List Example")
    
    # Configure tracing
    tracing_config = TracingConfig(
        service_name="custom-header-service",
        collector_url=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    )
    
    # Configure FastAPI with custom headers to capture
    fastapi_config = FastAPIConfig(
        enable_middleware=True,
        capture_request_headers=[
            "x-correlation-id",
            "x-request-id",
            "user-agent",
            "x-tenant-id",           # Custom business header
            "x-user-role",           # Custom business header
            "x-api-version",         # Custom API versioning header
            "accept-language",       # Localization header
        ],
        redact_headers=[
            "authorization",
            "cookie",
            "x-api-key"
        ]
    )
    
    tracer_manager, middleware_config = setup_tracing(tracing_config)
    middleware_class, middleware_kwargs = middleware_config
    
    # Pass the custom FastAPIConfig to middleware
    middleware_kwargs['fastapi_config'] = fastapi_config
    app.add_middleware(middleware_class, **middleware_kwargs)
    
    # Pass fastapi_config to instrumentation
    instrument_fastapi_app(app, tracing_config, fastapi_config)
    
    return app


# Example 3: Wildcard Pattern Matching
def create_app_with_patterns():
    """Create app with wildcard pattern matching for headers."""
    app = FastAPI(title="Pattern Matching Example")
    
    tracing_config = TracingConfig(
        service_name="pattern-header-service",
        collector_url=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    )
    
    # Configure with wildcard patterns
    fastapi_config = FastAPIConfig(
        enable_middleware=True,
        capture_request_headers=[
            "user-agent",
            "content-type"
        ],
        header_patterns=[
            "x-*",              # Capture all headers starting with "x-"
            "cf-*",             # Capture all CloudFlare headers
            "cloudfront-*",     # Capture all CloudFront headers
            "*-id",             # Capture all headers ending with "-id"
        ],
        redact_headers=[
            "authorization",
            "cookie",
            "x-api-key",
            "x-secret-*"        # Redact any header starting with "x-secret-"
        ]
    )
    
    tracer_manager, middleware_config = setup_tracing(tracing_config)
    middleware_class, middleware_kwargs = middleware_config
    middleware_kwargs['fastapi_config'] = fastapi_config
    app.add_middleware(middleware_class, **middleware_kwargs)
    
    instrument_fastapi_app(app, tracing_config, fastapi_config)
    
    return app


# Example 4: Security-Focused Configuration
def create_app_with_security_focus():
    """Create app with security-focused header configuration."""
    app = FastAPI(title="Security-Focused Example")
    
    tracing_config = TracingConfig(
        service_name="secure-header-service",
        collector_url=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
    )
    
    # Minimal header capture with aggressive redaction
    fastapi_config = FastAPIConfig(
        enable_middleware=True,
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
    
    tracer_manager, middleware_config = setup_tracing(tracing_config)
    middleware_class, middleware_kwargs = middleware_config
    middleware_kwargs['fastapi_config'] = fastapi_config
    app.add_middleware(middleware_class, **middleware_kwargs)
    
    instrument_fastapi_app(app, tracing_config, fastapi_config)
    
    return app


# Example 5: Testing Pattern Matching
def test_pattern_matching():
    """Demonstrate how pattern matching works."""
    
    # Test various patterns
    patterns = ["x-*", "*-id", "cf-*"]
    
    test_headers = [
        "x-correlation-id",
        "x-request-id",
        "x-custom-header",
        "tenant-id",
        "user-id",
        "cf-ray",
        "cf-connecting-ip",
        "user-agent",
        "authorization"
    ]
    
    print("\nPattern Matching Test:")
    print(f"Patterns: {patterns}\n")
    
    for header in test_headers:
        matches = match_header_pattern(header, patterns)
        print(f"  {header:25} -> {'MATCH' if matches else 'NO MATCH'}")


# Sample endpoints for testing
class TestRequest(BaseModel):
    message: str


def add_test_endpoints(app: FastAPI):
    """Add test endpoints to demonstrate header capture."""
    
    @app.get("/")
    async def root():
        return {"message": "Header capture example service"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    @app.post("/test")
    async def test_endpoint(request: Request, data: TestRequest):
        """
        Test endpoint that returns captured headers.
        
        Send requests with custom headers to see them captured in traces:
        
        curl -X POST http://localhost:8000/test \
          -H "Content-Type: application/json" \
          -H "x-correlation-id: test-123" \
          -H "x-tenant-id: tenant-456" \
          -H "x-user-role: admin" \
          -H "authorization: Bearer secret-token" \
          -d '{"message": "test"}'
        """
        headers = dict(request.headers)
        
        return {
            "message": data.message,
            "headers_received": {
                k: v if k != "authorization" else "[REDACTED]"
                for k, v in headers.items()
            },
            "note": "Check your tracing backend to see which headers were captured as span attributes"
        }


# Main application factory
def create_app(config_type: str = "default"):
    """
    Create application with specified configuration type.
    
    Args:
        config_type: One of "default", "custom", "patterns", "security"
    """
    if config_type == "custom":
        app = create_app_with_custom_headers()
    elif config_type == "patterns":
        app = create_app_with_patterns()
    elif config_type == "security":
        app = create_app_with_security_focus()
    else:
        app = create_app_with_defaults()
    
    add_test_endpoints(app)
    return app


if __name__ == "__main__":
    import uvicorn
    
    # Run pattern matching test
    test_pattern_matching()
    
    # Start server with pattern-based configuration
    print("\n" + "="*60)
    print("Starting server with pattern-based header capture...")
    print("="*60)
    print("\nTest with:")
    print("  curl -X POST http://localhost:8000/test \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -H 'x-correlation-id: test-123' \\")
    print("    -H 'x-tenant-id: tenant-456' \\")
    print("    -H 'x-custom-header: custom-value' \\")
    print("    -H 'authorization: Bearer secret' \\")
    print("    -d '{\"message\": \"test\"}'\n")
    
    app = create_app("patterns")
    uvicorn.run(app, host="0.0.0.0", port=8000)

