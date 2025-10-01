"""
Database instrumentation for distributed tracing.

Provides instrumentation for SQLAlchemy, Redis, and boto3.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# SQLAlchemy instrumentation
try:
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False
    logger.warning("SQLAlchemy instrumentation not available")

# Redis instrumentation
try:
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis instrumentation not available")

# boto3 instrumentation
try:
    from opentelemetry.instrumentation.botocore import BotocoreInstrumentor
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    logger.warning("boto3 instrumentation not available")


def instrument_sqlalchemy(engine, service_name: Optional[str] = None):
    """
    Instrument SQLAlchemy engine with OpenTelemetry.
    
    Args:
        engine: SQLAlchemy engine instance
        service_name: Optional service name for database spans
    
    Example:
        >>> from sqlalchemy import create_engine
        >>> from distributed_observability.framework.database import instrument_sqlalchemy
        >>> 
        >>> engine = create_engine("postgresql://...")
        >>> instrument_sqlalchemy(engine, service_name="my-service-db")
    """
    if not SQLALCHEMY_AVAILABLE:
        logger.error("SQLAlchemy instrumentation not available. Install: pip install opentelemetry-instrumentation-sqlalchemy")
        return
    
    SQLAlchemyInstrumentor().instrument(
        engine=engine,
        service=service_name,
    )
    logger.info(f"SQLAlchemy instrumentation enabled for {service_name or 'database'}")


def instrument_redis():
    """
    Instrument Redis client with OpenTelemetry.
    
    Example:
        >>> from distributed_observability.framework.database import instrument_redis
        >>> instrument_redis()
        >>> 
        >>> import redis
        >>> client = redis.Redis()  # Automatically instrumented
    """
    if not REDIS_AVAILABLE:
        logger.error("Redis instrumentation not available. Install: pip install opentelemetry-instrumentation-redis")
        return
    
    RedisInstrumentor().instrument()
    logger.info("Redis instrumentation enabled")


def instrument_boto3():
    """
    Instrument boto3 for AWS service calls (DynamoDB, S3, etc.).
    
    Example:
        >>> from distributed_observability.framework.database import instrument_boto3
        >>> instrument_boto3()
        >>> 
        >>> import boto3
        >>> dynamodb = boto3.resource('dynamodb')  # Automatically instrumented
    """
    if not BOTO3_AVAILABLE:
        logger.error("boto3 instrumentation not available. Install: pip install opentelemetry-instrumentation-botocore")
        return
    
    BotocoreInstrumentor().instrument()
    logger.info("boto3 instrumentation enabled")

