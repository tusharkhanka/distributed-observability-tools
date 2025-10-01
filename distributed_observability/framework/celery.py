"""
Celery instrumentation for distributed tracing.

Provides automatic trace context propagation for Celery tasks.
"""
import logging
from typing import Optional
from celery import signals
from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger(__name__)


class CeleryInstrumentor:
    """Instrumentor for Celery applications."""
    
    def __init__(self):
        self._propagator = TraceContextTextMapPropagator()
        self._instrumented = False
    
    def instrument(self, app=None):
        """
        Instrument Celery app with OpenTelemetry tracing.
        
        Args:
            app: Celery app instance (optional, will use default if not provided)
        """
        if self._instrumented:
            logger.warning("Celery already instrumented")
            return
        
        # Connect to Celery signals
        signals.before_task_publish.connect(self._before_task_publish)
        signals.task_prerun.connect(self._task_prerun)
        signals.task_postrun.connect(self._task_postrun)
        signals.task_failure.connect(self._task_failure)
        
        self._instrumented = True
        logger.info("Celery instrumentation enabled")
    
    def _before_task_publish(self, sender=None, headers=None, body=None, **kwargs):
        """Inject trace context into task headers before publishing."""
        if headers is None:
            return
        
        # Inject current trace context into task headers
        carrier = {}
        self._propagator.inject(carrier)
        headers.update(carrier)
        
        logger.debug(f"Injected trace context into task {sender}: {carrier}")
    
    def _task_prerun(self, task_id=None, task=None, **kwargs):
        """Extract trace context and start span when task starts."""
        if not task:
            return
        
        # Extract trace context from task headers
        headers = {}
        if hasattr(task, 'request') and hasattr(task.request, 'headers'):
            headers = task.request.headers or {}
        
        ctx = self._propagator.extract(headers)
        
        # Start a new span for this task
        tracer = trace.get_tracer(__name__)
        span = tracer.start_span(
            name=f"celery.task.{task.name}",
            context=ctx,
            kind=trace.SpanKind.CONSUMER,
        )
        
        # Set span attributes
        span.set_attributes({
            "celery.task_id": task_id,
            "celery.task_name": task.name,
            "messaging.system": "celery",
            "messaging.operation": "process",
        })
        
        # Store span in task request for later access
        if hasattr(task, 'request'):
            task.request._otel_span = span
        
        logger.debug(f"Started span for task {task.name} (ID: {task_id})")
    
    def _task_postrun(self, task_id=None, task=None, state=None, **kwargs):
        """End span when task completes successfully."""
        if not task or not hasattr(task, 'request'):
            return
        
        span = getattr(task.request, '_otel_span', None)
        if span:
            span.set_attribute("celery.state", state or "SUCCESS")
            span.end()
            logger.debug(f"Ended span for task {task.name} (ID: {task_id})")
    
    def _task_failure(self, task_id=None, task=None, exception=None, **kwargs):
        """Record exception and end span when task fails."""
        if not task or not hasattr(task, 'request'):
            return
        
        span = getattr(task.request, '_otel_span', None)
        if span:
            span.set_attributes({
                "celery.state": "FAILURE",
                "error": True,
                "error.type": type(exception).__name__ if exception else "Unknown",
                "error.message": str(exception) if exception else "",
            })
            span.record_exception(exception)
            span.end()
            logger.debug(f"Ended span for failed task {task.name} (ID: {task_id})")


# Singleton instance
_instrumentor = CeleryInstrumentor()


def instrument_celery(app=None):
    """
    Convenience function to instrument Celery.
    
    Args:
        app: Celery app instance (optional)
    
    Example:
        >>> from celery import Celery
        >>> from distributed_observability.framework.celery import instrument_celery
        >>> 
        >>> app = Celery('my-app')
        >>> instrument_celery(app)
    """
    _instrumentor.instrument(app)

