"""
Example: Using Function Tracing Decorators

This example shows how to use the @trace_function decorator to add
tracing to individual functions, including LLM API calls.
"""

import asyncio
import time
from distributed_observability import (
    TracingConfig,
    setup_tracing,
    trace_function,
    add_span_attributes,
)
from opentelemetry import trace

# Setup tracing
config = TracingConfig(
    service_name="decorator-example",
    collector_url="http://localhost:4317",
    environment="development",
)
tracer_manager, _ = setup_tracing(config)


# Example 1: Simple sync function with decorator
@trace_function(name="calculate_sum", attributes={"operation": "sum"})
def calculate_sum(numbers: list) -> int:
    """Calculate sum of numbers - automatically traced."""
    return sum(numbers)


# Example 2: Async function with decorator
@trace_function(name="fetch_data", attributes={"operation": "fetch"})
async def fetch_data(url: str) -> dict:
    """Simulate fetching data from an API - automatically traced."""
    await asyncio.sleep(0.1)  # Simulate network delay
    return {"url": url, "status": "success", "data": [1, 2, 3]}


# Example 3: LLM API call simulation with custom attributes
@trace_function(
    name="llm.openai.chat_completion",
    attributes={"llm.provider": "openai", "llm.model": "gpt-4"}
)
async def call_openai_llm(prompt: str, model: str = "gpt-4") -> str:
    """
    Simulate calling OpenAI LLM API.
    
    This demonstrates how to trace LLM calls with custom attributes.
    """
    # Get current span to add dynamic attributes
    span = trace.get_current_span()
    
    # Add prompt-specific attributes
    span.set_attributes({
        "llm.prompt_length": len(prompt),
        "llm.temperature": 0.7,
    })
    
    start_time = time.time()
    
    # Simulate API call
    await asyncio.sleep(0.2)
    response = f"Response to: {prompt[:50]}..."
    
    duration_ms = (time.time() - start_time) * 1000
    
    # Add response attributes
    span.set_attributes({
        "llm.response_length": len(response),
        "llm.tokens.prompt": 100,
        "llm.tokens.completion": 50,
        "llm.tokens.total": 150,
        "llm.duration_ms": duration_ms,
    })
    
    return response


# Example 4: Database operation with decorator
@trace_function(
    name="db.query.users",
    attributes={"db.system": "postgresql", "db.operation": "select"}
)
def query_users(user_id: int) -> dict:
    """Simulate database query - automatically traced."""
    # Add dynamic attributes
    add_span_attributes({
        "db.statement": f"SELECT * FROM users WHERE id = {user_id}",
        "db.table": "users",
    })
    
    # Simulate query
    time.sleep(0.05)
    
    return {
        "id": user_id,
        "name": "John Doe",
        "email": "john@example.com"
    }


# Example 5: Nested function calls (trace propagation)
@trace_function(name="process_user_request")
async def process_user_request(user_id: int, prompt: str):
    """
    Process a user request - demonstrates nested tracing.
    
    This will create a parent span with child spans for each operation.
    """
    # Step 1: Query user from database
    user = query_users(user_id)
    
    # Step 2: Call LLM API
    llm_response = await call_openai_llm(prompt)
    
    # Step 3: Fetch additional data
    data = await fetch_data(f"https://api.example.com/users/{user_id}")
    
    # Add custom attributes to parent span
    add_span_attributes({
        "user.id": user_id,
        "user.name": user["name"],
        "request.completed": True,
    })
    
    return {
        "user": user,
        "llm_response": llm_response,
        "additional_data": data,
    }


async def main():
    """Run examples."""
    print("=" * 80)
    print("FUNCTION TRACING DECORATOR EXAMPLES")
    print("=" * 80)
    print()
    
    # Example 1: Simple function
    print("Example 1: Simple sync function")
    result = calculate_sum([1, 2, 3, 4, 5])
    print(f"Sum: {result}")
    print()
    
    # Example 2: Async function
    print("Example 2: Async function")
    data = await fetch_data("https://api.example.com/data")
    print(f"Data: {data}")
    print()
    
    # Example 3: LLM call
    print("Example 3: LLM API call")
    response = await call_openai_llm("What is the meaning of life?")
    print(f"LLM Response: {response}")
    print()
    
    # Example 4: Database query
    print("Example 4: Database query")
    user = query_users(123)
    print(f"User: {user}")
    print()
    
    # Example 5: Nested operations
    print("Example 5: Nested operations (full request)")
    result = await process_user_request(
        user_id=123,
        prompt="Generate a test case for login functionality"
    )
    print(f"Request completed: {result['user']['name']}")
    print()
    
    print("=" * 80)
    print("All examples completed!")
    print("Check your OpenTelemetry collector/SigNoz for traces")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

