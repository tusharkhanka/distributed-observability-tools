"""
Test script to verify header configuration functionality.

This script tests the new header capture configuration without requiring Docker.
"""
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all new imports work correctly."""
    logger.info("Testing imports...")
    
    try:
        from distributed_observability import (
            TracingConfig,
            FastAPIConfig,
            HTTPClientConfig,
            match_header_pattern
        )
        logger.info("✓ All imports successful")
        return True
    except ImportError as e:
        logger.error(f"✗ Import failed: {e}")
        return False


def test_pattern_matching():
    """Test the pattern matching functionality."""
    logger.info("\nTesting pattern matching...")
    
    from distributed_observability import match_header_pattern
    
    test_cases = [
        # (header, patterns, expected_result)
        ("x-correlation-id", ["x-*"], True),
        ("x-request-id", ["x-*"], True),
        ("user-agent", ["x-*"], False),
        ("tenant-id", ["*-id"], True),
        ("user-id", ["*-id"], True),
        ("x-tenant-id", ["x-*", "*-id"], True),
        ("cf-ray", ["cf-*"], True),
        ("cloudfront-viewer-country", ["cloudfront-*"], True),
        ("authorization", ["x-*", "*-id"], False),
        ("X-Correlation-ID", ["x-*"], True),  # Case insensitive
        ("X-CUSTOM-HEADER", ["x-*"], True),   # Case insensitive
    ]
    
    all_passed = True
    for header, patterns, expected in test_cases:
        result = match_header_pattern(header, patterns)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        logger.info(f"  {status} {header:30} + {str(patterns):20} = {result} (expected {expected})")
    
    if all_passed:
        logger.info("✓ All pattern matching tests passed")
    else:
        logger.error("✗ Some pattern matching tests failed")
    
    return all_passed


def test_fastapi_config():
    """Test FastAPIConfig functionality."""
    logger.info("\nTesting FastAPIConfig...")
    
    from distributed_observability import FastAPIConfig
    
    # Test default configuration
    config = FastAPIConfig()
    logger.info(f"  Default capture_request_headers: {len(config.capture_request_headers)} headers")
    logger.info(f"  Default redact_headers: {len(config.redact_headers)} headers")
    logger.info(f"  Default header_patterns: {len(config.header_patterns)} patterns")
    
    # Test should_capture_header
    test_headers = [
        ("x-correlation-id", True),
        ("x-request-id", True),
        ("user-agent", True),
        ("x-edge-location", True),  # In default list
        ("random-header", False),
    ]
    
    all_passed = True
    for header, expected in test_headers:
        result = config.should_capture_header(header)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        logger.info(f"  {status} should_capture_header('{header}'): {result} (expected {expected})")
    
    # Test should_redact_header
    test_redact = [
        ("authorization", True),
        ("cookie", True),
        ("x-api-key", True),
        ("x-correlation-id", False),
        ("user-agent", False),
    ]
    
    for header, expected in test_redact:
        result = config.should_redact_header(header)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        logger.info(f"  {status} should_redact_header('{header}'): {result} (expected {expected})")
    
    if all_passed:
        logger.info("✓ All FastAPIConfig tests passed")
    else:
        logger.error("✗ Some FastAPIConfig tests failed")
    
    return all_passed


def test_custom_config():
    """Test custom configuration."""
    logger.info("\nTesting custom configuration...")
    
    from distributed_observability import FastAPIConfig
    
    # Create custom configuration
    config = FastAPIConfig(
        capture_request_headers=["x-correlation-id", "x-tenant-id", "x-user-role"],
        redact_headers=["authorization", "x-secret-key"],
        header_patterns=["x-*", "*-id"]
    )
    
    logger.info(f"  Custom capture_request_headers: {config.capture_request_headers}")
    logger.info(f"  Custom redact_headers: {config.redact_headers}")
    logger.info(f"  Custom header_patterns: {config.header_patterns}")
    
    # Test pattern matching with custom config
    test_cases = [
        ("x-correlation-id", True),   # Explicit + pattern
        ("x-tenant-id", True),        # Explicit + pattern
        ("x-custom-header", True),    # Pattern match
        ("tenant-id", True),          # Pattern match (*-id)
        ("user-agent", False),        # Not in list or patterns
    ]
    
    all_passed = True
    for header, expected in test_cases:
        result = config.should_capture_header(header)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        logger.info(f"  {status} should_capture_header('{header}'): {result} (expected {expected})")
    
    if all_passed:
        logger.info("✓ All custom config tests passed")
    else:
        logger.error("✗ Some custom config tests failed")
    
    return all_passed


def test_http_client_config():
    """Test HTTPClientConfig functionality."""
    logger.info("\nTesting HTTPClientConfig...")
    
    from distributed_observability import HTTPClientConfig
    
    # Test default configuration
    config = HTTPClientConfig()
    logger.info(f"  Default capture_headers: {config.capture_headers}")
    logger.info(f"  Default redact_headers: {config.redact_headers}")
    logger.info(f"  Default header_patterns: {config.header_patterns}")
    
    # Test with default patterns (x-*)
    test_cases = [
        ("x-correlation-id", True),   # Explicit + pattern
        ("x-request-id", True),       # Explicit + pattern
        ("x-custom-header", True),    # Pattern match
        ("user-agent", True),         # Explicit
        ("content-type", True),       # Explicit
        ("random-header", False),     # Not in list or patterns
    ]
    
    all_passed = True
    for header, expected in test_cases:
        result = config.should_capture_header(header)
        status = "✓" if result == expected else "✗"
        if result != expected:
            all_passed = False
        logger.info(f"  {status} should_capture_header('{header}'): {result} (expected {expected})")
    
    if all_passed:
        logger.info("✓ All HTTPClientConfig tests passed")
    else:
        logger.error("✗ Some HTTPClientConfig tests failed")
    
    return all_passed


def test_tracing_config_integration():
    """Test that TracingConfig works with new FastAPIConfig."""
    logger.info("\nTesting TracingConfig integration...")
    
    from distributed_observability import TracingConfig, FastAPIConfig
    
    try:
        # Create tracing config
        tracing_config = TracingConfig(
            service_name="test-service",
            collector_url="http://localhost:4317"
        )
        
        # Create FastAPI config
        fastapi_config = FastAPIConfig(
            capture_request_headers=["x-correlation-id", "x-tenant-id"],
            header_patterns=["x-*"]
        )
        
        logger.info(f"  TracingConfig service_name: {tracing_config.service_name}")
        logger.info(f"  FastAPIConfig capture_request_headers: {fastapi_config.capture_request_headers}")
        logger.info("✓ TracingConfig integration test passed")
        return True
    except Exception as e:
        logger.error(f"✗ TracingConfig integration test failed: {e}")
        return False


def test_backward_compatibility():
    """Test that existing code still works (backward compatibility)."""
    logger.info("\nTesting backward compatibility...")
    
    from distributed_observability import TracingConfig, FastAPIConfig
    
    try:
        # Old-style configuration (should still work)
        config = TracingConfig(
            service_name="legacy-service",
            collector_url="http://localhost:4317"
        )
        
        # Default FastAPIConfig should be created automatically
        fastapi_config = FastAPIConfig()
        
        # Should have sensible defaults
        assert len(fastapi_config.capture_request_headers) > 0
        assert len(fastapi_config.redact_headers) > 0
        assert "x-correlation-id" in fastapi_config.capture_request_headers
        assert "authorization" in fastapi_config.redact_headers
        
        logger.info("✓ Backward compatibility test passed")
        return True
    except Exception as e:
        logger.error(f"✗ Backward compatibility test failed: {e}")
        return False


def main():
    """Run all tests."""
    logger.info("="*60)
    logger.info("Testing Header Configuration Enhancements")
    logger.info("="*60)
    
    results = []
    
    # Run all tests
    results.append(("Imports", test_imports()))
    results.append(("Pattern Matching", test_pattern_matching()))
    results.append(("FastAPIConfig", test_fastapi_config()))
    results.append(("Custom Config", test_custom_config()))
    results.append(("HTTPClientConfig", test_http_client_config()))
    results.append(("TracingConfig Integration", test_tracing_config_integration()))
    results.append(("Backward Compatibility", test_backward_compatibility()))
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("Test Summary")
    logger.info("="*60)
    
    all_passed = True
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"  {status}: {test_name}")
        if not passed:
            all_passed = False
    
    logger.info("="*60)
    
    if all_passed:
        logger.info("✓ All tests passed!")
        return 0
    else:
        logger.error("✗ Some tests failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

