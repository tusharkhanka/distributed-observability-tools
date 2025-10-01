#!/usr/bin/env python3
"""Test script to verify all new imports work correctly."""

import sys
sys.path.insert(0, '.')

print("Testing distributed-observability-tools package imports...\n")

# Test 1: Core tracing imports
try:
    from distributed_observability import TracingConfig, setup_tracing, TracingManager
    print("✅ Core tracing imports: SUCCESS")
except Exception as e:
    print(f"❌ Core tracing imports: FAILED - {e}")

# Test 2: Decorator imports
try:
    from distributed_observability import trace_function, add_span_attributes
    print("✅ Decorator imports: SUCCESS")
except Exception as e:
    print(f"❌ Decorator imports: FAILED - {e}")

# Test 3: FastAPI middleware
try:
    from distributed_observability.framework import RequestTracingMiddleware
    print("✅ FastAPI middleware import: SUCCESS")
except Exception as e:
    print(f"❌ FastAPI middleware import: FAILED - {e}")

# Test 4: Celery instrumentation (may fail if celery not installed)
try:
    from distributed_observability.framework.celery import instrument_celery
    print("✅ Celery instrumentation import: SUCCESS")
except ImportError as e:
    print(f"⚠️  Celery instrumentation import: Optional dependency not installed - {e}")
except Exception as e:
    print(f"❌ Celery instrumentation import: FAILED - {e}")

# Test 5: Database instrumentation (may fail if dependencies not installed)
try:
    from distributed_observability.framework.database import instrument_sqlalchemy, instrument_redis, instrument_boto3
    print("✅ Database instrumentation imports: SUCCESS")
except ImportError as e:
    print(f"⚠️  Database instrumentation imports: Optional dependencies not installed")
except Exception as e:
    print(f"❌ Database instrumentation imports: FAILED - {e}")

# Test 6: gRPC instrumentation (may fail if grpc not installed)
try:
    from distributed_observability.framework.grpc import instrument_grpc_client, instrument_grpc_server
    print("✅ gRPC instrumentation imports: SUCCESS")
except ImportError as e:
    print(f"⚠️  gRPC instrumentation imports: Optional dependency not installed")
except Exception as e:
    print(f"❌ gRPC instrumentation imports: FAILED - {e}")

# Test 7: Direct module imports
try:
    from distributed_observability.tracing.decorators import trace_function
    from distributed_observability.framework.celery import CeleryInstrumentor
    print("✅ Direct module imports: SUCCESS")
except ImportError as e:
    print(f"⚠️  Direct module imports: Some optional dependencies not installed")
except Exception as e:
    print(f"❌ Direct module imports: FAILED - {e}")

print("\n" + "="*60)
print("📦 Package structure verification complete!")
print("="*60)
print("\nNote: ⚠️  warnings are expected if optional dependencies aren't installed.")
print("Install with: pip install distributed-observability-tools[all]")

