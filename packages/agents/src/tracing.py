"""
Distributed tracing configuration using OpenTelemetry.

This module provides instrumentation for tracing requests across agents
and external services.
"""
from typing import Optional, Dict, Any, Callable
from functools import wraps
import os

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.pymongo import PymongoInstrumentor
from opentelemetry.trace import Status, StatusCode, Span
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


# Global tracer instance
_tracer: Optional[trace.Tracer] = None


def setup_tracing(
    service_name: str = "chimera-agent",
    service_version: str = "1.0.0",
    jaeger_endpoint: Optional[str] = None,
    enable_console_export: bool = False,
) -> trace.Tracer:
    """
    Set up OpenTelemetry tracing for the application.
    
    Args:
        service_name: Name of the service for trace identification
        service_version: Version of the service
        jaeger_endpoint: Jaeger collector endpoint (e.g., "http://localhost:4317")
        enable_console_export: Whether to export traces to console for debugging
    
    Returns:
        Configured tracer instance
    """
    global _tracer
    
    # Create resource with service information
    resource = Resource.create({
        SERVICE_NAME: service_name,
        SERVICE_VERSION: service_version,
    })
    
    # Create tracer provider
    provider = TracerProvider(resource=resource)
    
    # Add span processors
    if jaeger_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        # Use OTLP exporter for Jaeger
        otlp_exporter = OTLPSpanExporter(
            endpoint=jaeger_endpoint or os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
            insecure=True,  # Use insecure for local development
        )
        provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    
    if enable_console_export:
        # Add console exporter for debugging
        console_exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(console_exporter))
    
    # Set the tracer provider
    trace.set_tracer_provider(provider)
    
    # Instrument libraries
    RequestsInstrumentor().instrument()
    RedisInstrumentor().instrument()
    PymongoInstrumentor().instrument()
    
    # Get tracer
    _tracer = trace.get_tracer(__name__)
    
    return _tracer


def get_tracer() -> trace.Tracer:
    """
    Get the global tracer instance.
    
    Returns:
        Tracer instance
    
    Raises:
        RuntimeError: If tracing has not been set up
    """
    if _tracer is None:
        raise RuntimeError("Tracing not initialized. Call setup_tracing() first.")
    return _tracer


def create_span(
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    kind: trace.SpanKind = trace.SpanKind.INTERNAL,
) -> Span:
    """
    Create a new span.
    
    Args:
        name: Name of the span
        attributes: Optional attributes to add to the span
        kind: Type of span (INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
    
    Returns:
        Span instance
    """
    tracer = get_tracer()
    span = tracer.start_span(name, kind=kind)
    
    if attributes:
        for key, value in attributes.items():
            span.set_attribute(key, value)
    
    return span


def trace_function(
    name: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
) -> Callable:
    """
    Decorator to trace a function execution.
    
    Args:
        name: Optional custom name for the span (defaults to function name)
        attributes: Optional attributes to add to the span
    
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            span_name = name or f"{func.__module__}.{func.__name__}"
            
            with tracer.start_as_current_span(span_name) as span:
                # Add attributes
                if attributes:
                    for key, value in attributes.items():
                        span.set_attribute(key, value)
                
                # Add function info
                span.set_attribute("function.name", func.__name__)
                span.set_attribute("function.module", func.__module__)
                
                try:
                    result = func(*args, **kwargs)
                    span.set_status(Status(StatusCode.OK))
                    return result
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator


def trace_agent_operation(operation: str) -> Callable:
    """
    Decorator to trace agent operations.
    
    Args:
        operation: Name of the operation (e.g., "process_query", "fetch_data")
    
    Returns:
        Decorated function
    """
    return trace_function(
        name=f"agent.{operation}",
        attributes={"operation.type": "agent"}
    )


def inject_trace_context(carrier: Dict[str, str]) -> None:
    """
    Inject trace context into a carrier (e.g., message headers).
    
    Args:
        carrier: Dictionary to inject trace context into
    """
    propagator = TraceContextTextMapPropagator()
    propagator.inject(carrier)


def extract_trace_context(carrier: Dict[str, str]) -> None:
    """
    Extract trace context from a carrier and set as current context.
    
    Args:
        carrier: Dictionary containing trace context
    """
    propagator = TraceContextTextMapPropagator()
    context = propagator.extract(carrier)
    trace.set_span_in_context(trace.get_current_span(), context)


def add_span_event(name: str, attributes: Optional[Dict[str, Any]] = None) -> None:
    """
    Add an event to the current span.
    
    Args:
        name: Name of the event
        attributes: Optional attributes for the event
    """
    span = trace.get_current_span()
    if span:
        span.add_event(name, attributes or {})


def set_span_attribute(key: str, value: Any) -> None:
    """
    Set an attribute on the current span.
    
    Args:
        key: Attribute key
        value: Attribute value
    """
    span = trace.get_current_span()
    if span:
        span.set_attribute(key, value)


def set_span_error(error: Exception) -> None:
    """
    Mark the current span as error and record the exception.
    
    Args:
        error: Exception that occurred
    """
    span = trace.get_current_span()
    if span:
        span.set_status(Status(StatusCode.ERROR, str(error)))
        span.record_exception(error)


# Context manager for manual span creation
class traced_span:
    """
    Context manager for creating traced spans.
    
    Usage:
        with traced_span("operation_name", attributes={"key": "value"}):
            # Your code here
            pass
    """
    
    def __init__(
        self,
        name: str,
        attributes: Optional[Dict[str, Any]] = None,
        kind: trace.SpanKind = trace.SpanKind.INTERNAL,
    ):
        self.name = name
        self.attributes = attributes or {}
        self.kind = kind
        self.span: Optional[Span] = None
    
    def __enter__(self) -> Span:
        tracer = get_tracer()
        self.span = tracer.start_span(self.name, kind=self.kind)
        
        for key, value in self.attributes.items():
            self.span.set_attribute(key, value)
        
        return self.span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.span:
            if exc_type is not None:
                self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                self.span.record_exception(exc_val)
            else:
                self.span.set_status(Status(StatusCode.OK))
            
            self.span.end()


# Helper functions for common tracing patterns
def trace_message_processing(
    message_type: str,
    correlation_id: str,
) -> traced_span:
    """
    Create a span for message processing.
    
    Args:
        message_type: Type of message being processed
        correlation_id: Correlation ID for the message
    
    Returns:
        Context manager for the span
    """
    return traced_span(
        f"message.process.{message_type}",
        attributes={
            "message.type": message_type,
            "correlation.id": correlation_id,
        },
        kind=trace.SpanKind.CONSUMER,
    )


def trace_external_call(
    service: str,
    operation: str,
) -> traced_span:
    """
    Create a span for external service calls.
    
    Args:
        service: Name of the external service
        operation: Operation being performed
    
    Returns:
        Context manager for the span
    """
    return traced_span(
        f"external.{service}.{operation}",
        attributes={
            "service.name": service,
            "operation": operation,
        },
        kind=trace.SpanKind.CLIENT,
    )


def trace_database_operation(
    database: str,
    operation: str,
    collection: Optional[str] = None,
) -> traced_span:
    """
    Create a span for database operations.
    
    Args:
        database: Database name
        operation: Operation being performed (e.g., "find", "insert")
        collection: Optional collection/table name
    
    Returns:
        Context manager for the span
    """
    attributes = {
        "db.system": database,
        "db.operation": operation,
    }
    
    if collection:
        attributes["db.collection"] = collection
    
    return traced_span(
        f"db.{database}.{operation}",
        attributes=attributes,
        kind=trace.SpanKind.CLIENT,
    )
