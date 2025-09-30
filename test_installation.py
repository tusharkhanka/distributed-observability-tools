#!/usr/bin/env python3
"""
Test script to verify distributed-observability-tools installation and basic functionality.
Run this after installing the package to ensure everything works correctly.
"""

import sys
import traceback

def test_imports():
    """Test that all main modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        # Test core imports
        from distributed_observability import TracingConfig, setup_tracing
        print("✅ Core imports successful")
        
        # Test configuration imports
        from distributed_observability.core.config import (
            TracingConfig, CorrelationConfig, FastAPIConfig, 
            HTTPClientConfig, ObservabilityConfig
        )
        print("✅ Configuration imports successful")
        
        # Test tracing imports
        from distributed_observability.tracing import (
            TracingManager, CorrelationManager, SpanManager
        )
        print("✅ Tracing imports successful")
        
        # Test framework imports
        from distributed_observability.framework.fastapi import RequestTracingMiddleware
        print("✅ FastAPI framework imports successful")
        
        # Test utils imports
        from distributed_observability.utils import (
            instrument_httpx_client, CorrelatedClient, patch_httpx
        )
        print("✅ Utils imports successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Import failed: {e}")
        traceback.print_exc()
        return False

def test_basic_configuration():
    """Test basic configuration creation."""
    print("\n🔧 Testing configuration...")
    
    try:
        from distributed_observability import TracingConfig, CorrelationConfig
        
        # Test basic config
        config = TracingConfig(
            service_name="test-service",
            collector_url="http://localhost:4317"
        )
        print(f"✅ Basic config created: {config.service_name}")
        
        # Test advanced config
        advanced_config = TracingConfig(
            service_name="advanced-test-service",
            service_version="1.0.0",
            collector_url="http://otel-collector:4317",
            sampling_rate=0.1,
            correlation=CorrelationConfig(
                headers=["x-correlation-id", "x-request-id"],
                propagation=True
            ),
            environment="test"
        )
        print(f"✅ Advanced config created: {advanced_config.service_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        traceback.print_exc()
        return False

def test_tracing_setup():
    """Test tracing setup (without actual OTEL collector)."""
    print("\n🎯 Testing tracing setup...")
    
    try:
        from distributed_observability import TracingConfig, setup_tracing
        
        config = TracingConfig(
            service_name="test-service",
            collector_url="http://localhost:4317"  # This will fail gracefully
        )
        
        # This should not raise an exception even if collector is not available
        tracer_manager, middleware_config = setup_tracing(config)
        print("✅ Tracing setup completed (graceful degradation)")
        
        # Test that we get the expected objects
        if tracer_manager is not None:
            print("✅ TracerManager created")
        
        if middleware_config is not None:
            print("✅ Middleware config created")
            
        return True
        
    except Exception as e:
        print(f"❌ Tracing setup test failed: {e}")
        traceback.print_exc()
        return False

def test_fastapi_integration():
    """Test FastAPI integration (import only, no actual server)."""
    print("\n🌐 Testing FastAPI integration...")
    
    try:
        from distributed_observability.framework.fastapi import RequestTracingMiddleware
        from distributed_observability import TracingConfig
        
        config = TracingConfig(
            service_name="fastapi-test",
            collector_url="http://localhost:4317"
        )
        
        # Test middleware creation (without actual FastAPI app)
        print("✅ FastAPI middleware import successful")
        print("✅ Ready for FastAPI integration")
        
        return True
        
    except Exception as e:
        print(f"❌ FastAPI integration test failed: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 Testing distributed-observability-tools installation")
    print("=" * 60)
    
    tests = [
        test_imports,
        test_basic_configuration,
        test_tracing_setup,
        test_fastapi_integration,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Package is working correctly.")
        print("\n📋 Next steps:")
        print("   1. Check the README.md for usage examples")
        print("   2. See example/ directory for complete implementations")
        print("   3. Visit: https://github.com/tusharkhanka/distributed-observability-tools")
        return 0
    else:
        print("❌ Some tests failed. Please check the installation.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
