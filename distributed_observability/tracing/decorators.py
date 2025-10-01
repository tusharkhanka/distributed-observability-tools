"""
Decorators for function-level tracing.

Provides easy-to-use decorators for adding tracing to functions.
"""
import asyncio
import logging
from functools import wraps
from typing import Optional, Dict, Any, Callable
from opentelemetry import trace

logger = logging.getLogger(__name__)


def trace_function(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
):
    """
    Decorator to trace a function with custom attributes.
    
    Args:
        name: Custom span name (defaults to module.function_name)
        attributes: Static attributes to add to the span
        kind: Span kind (INTERNAL, CLIENT, SERVER, etc.)
    
    Example:
        >>> @trace_function(name="llm_api_call", attributes={"llm.provider": "openai"})
        >>> async def call_openai(prompt: str):
        >>>     return await openai.chat(prompt)
    """
    def decorator(func: Callable) -> Callable:
        span_name = name or f"{func.__module__}.{func.__name__}"
        
        if asyncio.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                tracer = trace.get_tracer(__name__)
                
                with tracer.start_as_current_span(span_name, kind=kind) as span:
                    # Add static attributes
                    if attributes:
                        span.set_attributes(attributes)
                    
                    # Add function metadata
                    span.set_attributes({
                        "code.function": func.__name__,
                        "code.namespace": func.__module__,
                    })
                    
                    try:
                        result = await func(*args, **kwargs)
                        return result
                    except Exception as e:
                        span.set_attributes({
                            "error": True,
                            "error.type": type(e).__name__,
                            "error.message": str(e),
                        })
                        span.record_exception(e)
                        raise
            
            return async_wrapper
        else:
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                tracer = trace.get_tracer(__name__)
                
                with tracer.start_as_current_span(span_name, kind=kind) as span:
                    # Add static attributes
                    if attributes:
                        span.set_attributes(attributes)
                    
                    # Add function metadata
                    span.set_attributes({
                        "code.function": func.__name__,
                        "code.namespace": func.__module__,
                    })
                    
                    try:
                        result = func(*args, **kwargs)
                        return result
                    except Exception as e:
                        span.set_attributes({
                            "error": True,
                            "error.type": type(e).__name__,
                            "error.message": str(e),
                        })
                        span.record_exception(e)
                        raise
            
            return sync_wrapper
    
    return decorator


def add_span_attributes(attributes: Dict[str, Any]):
    """
    Add attributes to the current span.
    
    Args:
        attributes: Dictionary of attributes to add
    
    Example:
        >>> span = trace.get_current_span()
        >>> add_span_attributes({"user.id": "123", "test.id": "test-456"})
    """
    span = trace.get_current_span()
    if span.is_recording():
        span.set_attributes(attributes)

