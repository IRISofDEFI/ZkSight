"""
Initialize distributed tracing for agents.

This module should be imported and called at agent startup to enable
OpenTelemetry tracing with Jaeger.
"""
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def init_agent_tracing(
    agent_name: str,
    service_version: str = "1.0.0",
    jaeger_endpoint: Optional[str] = None,
    enable_console_export: bool = False,
) -> None:
    """
    Initialize OpenTelemetry tracing for an agent.
    
    This should be called once at agent startup, before any message processing begins.
    
    Args:
        agent_name: Name of the agent (e.g., "query_agent", "analysis_agent")
        service_version: Version of the service
        jaeger_endpoint: Jaeger OTLP endpoint (defaults to env var or localhost:4317)
        enable_console_export: Whether to also export traces to console for debugging
    
    Example:
        >>> from init_tracing import init_agent_tracing
        >>> init_agent_tracing("query_agent")
        >>> # Now all agent operations will be traced
    """
    try:
        from .tracing import setup_tracing
        
        # Get Jaeger endpoint from environment or use default
        if jaeger_endpoint is None:
            jaeger_endpoint = os.getenv(
                "OTEL_EXPORTER_OTLP_ENDPOINT",
                "http://localhost:4317"
            )
        
        # Enable console export in development
        if enable_console_export is None:
            enable_console_export = os.getenv("ENVIRONMENT", "development") == "development"
        
        logger.info(
            f"Initializing tracing for {agent_name} "
            f"(endpoint: {jaeger_endpoint})"
        )
        
        setup_tracing(
            service_name=agent_name,
            service_version=service_version,
            jaeger_endpoint=jaeger_endpoint,
            enable_console_export=enable_console_export,
        )
        
        logger.info(f"Tracing initialized successfully for {agent_name}")
        
    except ImportError:
        logger.warning(
            "OpenTelemetry not available. Install with: "
            "pip install opentelemetry-api opentelemetry-sdk "
            "opentelemetry-exporter-otlp-proto-grpc "
            "opentelemetry-instrumentation-requests "
            "opentelemetry-instrumentation-redis "
            "opentelemetry-instrumentation-pymongo"
        )
    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}", exc_info=True)
        # Don't fail agent startup if tracing fails
        logger.warning("Agent will continue without tracing")


def shutdown_agent_tracing() -> None:
    """
    Shutdown tracing gracefully.
    
    This should be called when the agent is shutting down to ensure
    all spans are flushed to Jaeger.
    """
    try:
        from opentelemetry import trace
        
        # Get the tracer provider and shutdown
        provider = trace.get_tracer_provider()
        if hasattr(provider, 'shutdown'):
            provider.shutdown()
            logger.info("Tracing shutdown complete")
    except Exception as e:
        logger.debug(f"Error during tracing shutdown: {e}")
