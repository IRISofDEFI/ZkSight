"""
Structured logging configuration for Chimera agents.

This module provides JSON-formatted logging with correlation IDs and
configurable log levels for all agent operations.
"""
import logging
import json
import sys
from typing import Optional, Dict, Any
from datetime import datetime
from contextvars import ContextVar

# Context variable for correlation ID
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def __init__(self, service_name: str = "chimera-agent"):
        super().__init__()
        self.service_name = service_name
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add correlation ID if available
        correlation_id = correlation_id_var.get()
        if correlation_id:
            log_data["correlation_id"] = correlation_id
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
        
        # Add standard fields
        log_data.update({
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread,
        })
        
        return json.dumps(log_data)


class CorrelationIdFilter(logging.Filter):
    """Filter to add correlation ID to log records"""
    
    def filter(self, record: logging.LogRecord) -> bool:
        correlation_id = correlation_id_var.get()
        if correlation_id:
            record.correlation_id = correlation_id
        return True


def setup_logging(
    service_name: str = "chimera-agent",
    log_level: str = "INFO",
    json_format: bool = True,
) -> logging.Logger:
    """
    Set up structured logging for the application.
    
    Args:
        service_name: Name of the service for log identification
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: Whether to use JSON formatting (True) or plain text (False)
    
    Returns:
        Configured logger instance
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, log_level.upper()))
    
    # Set formatter
    if json_format:
        formatter = JSONFormatter(service_name=service_name)
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    handler.setFormatter(formatter)
    
    # Add correlation ID filter
    handler.addFilter(CorrelationIdFilter())
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_correlation_id(correlation_id: str) -> None:
    """
    Set the correlation ID for the current context.
    
    Args:
        correlation_id: Unique identifier for request correlation
    """
    correlation_id_var.set(correlation_id)


def get_correlation_id() -> Optional[str]:
    """
    Get the correlation ID for the current context.
    
    Returns:
        Correlation ID or None if not set
    """
    return correlation_id_var.get()


def clear_correlation_id() -> None:
    """Clear the correlation ID for the current context"""
    correlation_id_var.set(None)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds extra fields to all log records.
    
    Usage:
        logger = LoggerAdapter(logging.getLogger(__name__), {"user_id": "123"})
        logger.info("User action", extra_fields={"action": "login"})
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add extra fields to log record"""
        extra_fields = kwargs.pop('extra_fields', {})
        extra_fields.update(self.extra)
        
        # Store extra fields in the record
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        kwargs['extra']['extra_fields'] = extra_fields
        
        return msg, kwargs


def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **kwargs: Any
) -> None:
    """
    Log a message with additional context fields.
    
    Args:
        logger: Logger instance
        level: Log level (debug, info, warning, error, critical)
        message: Log message
        **kwargs: Additional context fields to include in the log
    """
    log_func = getattr(logger, level.lower())
    log_func(message, extra={'extra_fields': kwargs})


# Example usage functions
def log_agent_start(logger: logging.Logger, agent_name: str, config: Dict[str, Any]) -> None:
    """Log agent startup"""
    log_with_context(
        logger,
        'info',
        f'{agent_name} starting',
        agent=agent_name,
        config=config,
        event='agent_start'
    )


def log_agent_stop(logger: logging.Logger, agent_name: str) -> None:
    """Log agent shutdown"""
    log_with_context(
        logger,
        'info',
        f'{agent_name} stopping',
        agent=agent_name,
        event='agent_stop'
    )


def log_message_received(
    logger: logging.Logger,
    agent_name: str,
    message_type: str,
    correlation_id: str
) -> None:
    """Log message receipt"""
    set_correlation_id(correlation_id)
    log_with_context(
        logger,
        'info',
        f'{agent_name} received message',
        agent=agent_name,
        message_type=message_type,
        event='message_received'
    )


def log_message_sent(
    logger: logging.Logger,
    agent_name: str,
    message_type: str,
    correlation_id: str
) -> None:
    """Log message sending"""
    set_correlation_id(correlation_id)
    log_with_context(
        logger,
        'info',
        f'{agent_name} sent message',
        agent=agent_name,
        message_type=message_type,
        event='message_sent'
    )


def log_error(
    logger: logging.Logger,
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """Log an error with context"""
    context = context or {}
    log_with_context(
        logger,
        'error',
        f'Error occurred: {str(error)}',
        error_type=type(error).__name__,
        error_message=str(error),
        event='error',
        **context
    )
