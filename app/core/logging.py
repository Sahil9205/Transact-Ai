from __future__ import annotations

import logging
import sys
import structlog


def setup_logging(log_level: str, environment: str, stream: Any = None) -> None:
    """Configure structured logging for the application."""
    if stream is None:
        stream = sys.stdout
    logging.basicConfig(format="%(message)s", stream=stream, level=log_level.upper(), force=True)
    
    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if environment.lower() == "production":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
        
    structlog.configure(
        processors=processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """Get a structured logger instance.
    
    Args:
        name: The name of the logger.
        
    Returns:
        A bound structured logger.
    """
    return structlog.get_logger(name)
