"""
Example: Using Celery Instrumentation with distributed-observability-tools

This example shows how to instrument a Celery application for distributed tracing.
"""

from celery import Celery
from distributed_observability import TracingConfig, setup_tracing
from distributed_observability.framework.celery import instrument_celery

# Step 1: Configure tracing
tracing_config = TracingConfig(
    service_name="celery-worker",
    collector_url="http://localhost:4317",
    environment="development",
    sampling_rate=1.0,  # 100% sampling for development
)

# Step 2: Setup tracing
tracer_manager, _ = setup_tracing(tracing_config)

# Step 3: Create Celery app
app = Celery(
    'example-app',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

# Step 4: Instrument Celery app
instrument_celery(app)

# Step 5: Define tasks (they will be automatically traced)
@app.task(name='tasks.add')
def add(x, y):
    """Add two numbers - this task will be automatically traced."""
    return x + y

@app.task(name='tasks.multiply')
def multiply(x, y):
    """Multiply two numbers - this task will be automatically traced."""
    return x * y

@app.task(name='tasks.process_data')
def process_data(data):
    """
    Process data - demonstrates trace context propagation.
    
    When this task is called from another service, the trace context
    will be automatically propagated through Celery task headers.
    """
    result = {
        'processed': True,
        'item_count': len(data),
        'items': data
    }
    return result


if __name__ == '__main__':
    # Example: Enqueue tasks
    print("Enqueueing tasks...")
    
    # These tasks will have trace context injected into their headers
    result1 = add.delay(4, 6)
    result2 = multiply.delay(4, 6)
    result3 = process_data.delay(['item1', 'item2', 'item3'])
    
    print(f"Task 1 (add): {result1.id}")
    print(f"Task 2 (multiply): {result2.id}")
    print(f"Task 3 (process_data): {result3.id}")
    
    print("\nTo run the worker:")
    print("  celery -A celery_example worker --loglevel=info")

