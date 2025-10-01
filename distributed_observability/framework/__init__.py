"""Framework integrations for observability tools."""
from .fastapi import RequestTracingMiddleware

# Optional Celery integration
try:
    from .celery import instrument_celery, CeleryInstrumentor
    _CELERY_AVAILABLE = True
except ImportError:
    instrument_celery = None
    CeleryInstrumentor = None
    _CELERY_AVAILABLE = False

# Optional database integrations
try:
    from .database import instrument_sqlalchemy, instrument_redis, instrument_boto3
    _DATABASE_AVAILABLE = True
except ImportError:
    instrument_sqlalchemy = None
    instrument_redis = None
    instrument_boto3 = None
    _DATABASE_AVAILABLE = False

# Optional gRPC integration
try:
    from .grpc import instrument_grpc_client, instrument_grpc_server
    _GRPC_AVAILABLE = True
except ImportError:
    instrument_grpc_client = None
    instrument_grpc_server = None
    _GRPC_AVAILABLE = False

__all__ = [
    "RequestTracingMiddleware",
]

# Add optional exports if available
if _CELERY_AVAILABLE:
    __all__.extend(["instrument_celery", "CeleryInstrumentor"])

if _DATABASE_AVAILABLE:
    __all__.extend(["instrument_sqlalchemy", "instrument_redis", "instrument_boto3"])

if _GRPC_AVAILABLE:
    __all__.extend(["instrument_grpc_client", "instrument_grpc_server"])

