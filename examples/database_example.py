"""
Example: Using Database Instrumentation

This example shows how to instrument SQLAlchemy, Redis, and boto3
for automatic database operation tracing.
"""

from distributed_observability import TracingConfig, setup_tracing
from distributed_observability.framework.database import (
    instrument_sqlalchemy,
    instrument_redis,
    instrument_boto3,
)

# Setup tracing
config = TracingConfig(
    service_name="database-example",
    collector_url="http://localhost:4317",
    environment="development",
)
tracer_manager, _ = setup_tracing(config)


# Example 1: SQLAlchemy Instrumentation
def example_sqlalchemy():
    """
    Example of instrumenting SQLAlchemy for PostgreSQL tracing.
    
    All database queries will be automatically traced with:
    - SQL statement
    - Database name
    - Query duration
    - Connection info
    """
    try:
        from sqlalchemy import create_engine, text
        
        # Create SQLAlchemy engine
        engine = create_engine(
            "postgresql://user:password@localhost:5432/mydb",
            pool_size=10,
            max_overflow=20,
        )
        
        # Instrument the engine
        instrument_sqlalchemy(engine, service_name="myapp-db")
        
        # Now all queries will be traced
        with engine.connect() as conn:
            # This query will create a span with SQL details
            result = conn.execute(text("SELECT * FROM users WHERE id = :id"), {"id": 123})
            users = result.fetchall()
            print(f"Found {len(users)} users")
        
        print("✅ SQLAlchemy instrumentation example completed")
        
    except ImportError:
        print("⚠️  SQLAlchemy not installed - skipping example")
        print("   Install with: pip install sqlalchemy psycopg2-binary")
    except Exception as e:
        print(f"⚠️  SQLAlchemy example error: {e}")


# Example 2: Redis Instrumentation
def example_redis():
    """
    Example of instrumenting Redis for cache operation tracing.
    
    All Redis operations will be automatically traced with:
    - Command name (GET, SET, etc.)
    - Key name
    - Operation duration
    """
    try:
        import redis
        
        # Instrument Redis (must be done before creating client)
        instrument_redis()
        
        # Create Redis client - all operations will be traced
        client = redis.Redis(host='localhost', port=6379, db=0)
        
        # These operations will create spans
        client.set('user:123', 'John Doe')
        value = client.get('user:123')
        print(f"Redis value: {value}")
        
        # Hash operations
        client.hset('user:123:profile', mapping={
            'name': 'John Doe',
            'email': 'john@example.com'
        })
        profile = client.hgetall('user:123:profile')
        print(f"Redis hash: {profile}")
        
        print("✅ Redis instrumentation example completed")
        
    except ImportError:
        print("⚠️  Redis not installed - skipping example")
        print("   Install with: pip install redis")
    except Exception as e:
        print(f"⚠️  Redis example error: {e}")


# Example 3: boto3/DynamoDB Instrumentation
def example_boto3():
    """
    Example of instrumenting boto3 for AWS service tracing.
    
    All AWS API calls will be automatically traced with:
    - Service name (DynamoDB, S3, etc.)
    - Operation name
    - Request/response details
    - Duration
    """
    try:
        import boto3
        
        # Instrument boto3 (must be done before creating clients)
        instrument_boto3()
        
        # Create DynamoDB client - all operations will be traced
        dynamodb = boto3.resource(
            'dynamodb',
            region_name='us-east-1',
            endpoint_url='http://localhost:8000'  # Local DynamoDB
        )
        
        # Get table
        table = dynamodb.Table('Users')
        
        # Put item - will create a span
        table.put_item(
            Item={
                'user_id': '123',
                'name': 'John Doe',
                'email': 'john@example.com'
            }
        )
        
        # Get item - will create a span
        response = table.get_item(Key={'user_id': '123'})
        item = response.get('Item')
        print(f"DynamoDB item: {item}")
        
        # Query - will create a span
        response = table.query(
            KeyConditionExpression='user_id = :uid',
            ExpressionAttributeValues={':uid': '123'}
        )
        print(f"Query results: {response['Count']} items")
        
        print("✅ boto3 instrumentation example completed")
        
    except ImportError:
        print("⚠️  boto3 not installed - skipping example")
        print("   Install with: pip install boto3")
    except Exception as e:
        print(f"⚠️  boto3 example error: {e}")


# Example 4: Combined Usage
def example_combined():
    """
    Example showing all database instrumentations working together.
    
    This simulates a typical microservice that uses:
    - PostgreSQL for persistent data
    - Redis for caching
    - DynamoDB for session storage
    """
    print("\n" + "=" * 80)
    print("COMBINED DATABASE INSTRUMENTATION EXAMPLE")
    print("=" * 80)
    print()
    
    # Instrument all databases
    print("Setting up instrumentation...")
    
    try:
        from sqlalchemy import create_engine
        engine = create_engine("postgresql://localhost/mydb")
        instrument_sqlalchemy(engine, service_name="myapp-postgres")
        print("✅ SQLAlchemy instrumented")
    except:
        print("⚠️  SQLAlchemy not available")
    
    try:
        instrument_redis()
        print("✅ Redis instrumented")
    except:
        print("⚠️  Redis instrumentation not available")
    
    try:
        instrument_boto3()
        print("✅ boto3 instrumented")
    except:
        print("⚠️  boto3 instrumentation not available")
    
    print()
    print("All database operations will now be automatically traced!")
    print("Each operation will create a span with detailed attributes.")
    print()


def main():
    """Run all examples."""
    print("=" * 80)
    print("DATABASE INSTRUMENTATION EXAMPLES")
    print("=" * 80)
    print()
    
    print("Example 1: SQLAlchemy (PostgreSQL)")
    print("-" * 80)
    example_sqlalchemy()
    print()
    
    print("Example 2: Redis")
    print("-" * 80)
    example_redis()
    print()
    
    print("Example 3: boto3 (DynamoDB)")
    print("-" * 80)
    example_boto3()
    print()
    
    print("Example 4: Combined Usage")
    print("-" * 80)
    example_combined()
    print()
    
    print("=" * 80)
    print("Examples completed!")
    print("=" * 80)
    print()
    print("Note: Some examples may show warnings if databases aren't running")
    print("      or if optional dependencies aren't installed.")
    print()
    print("To install all database instrumentation dependencies:")
    print("  pip install distributed-observability-tools[database,aws]")


if __name__ == "__main__":
    main()

