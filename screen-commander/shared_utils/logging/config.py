"""Logging configuration for all domains."""

import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional, Dict, Any

def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
    **kwargs: Any
) -> logging.Logger:
    """Set up a logger with common configuration.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level
        log_file: Optional file to log to
        format_string: Optional custom format string
        **kwargs: Additional configuration options
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Set level
    level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Create formatters
    if not format_string:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    formatter = logging.Formatter(format_string)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if requested
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create rotating file handler
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=kwargs.get("max_bytes", 10 * 1024 * 1024),  # 10MB
            backupCount=kwargs.get("backup_count", 5)
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

def get_domain_logger(
    domain: str,
    name: Optional[str] = None,
    **kwargs: Any
) -> logging.Logger:
    """Get a logger for a specific domain.
    
    Args:
        domain: Domain name (e.g., 'command_parser')
        name: Optional sub-logger name
        **kwargs: Additional configuration options
        
    Returns:
        Domain-specific logger instance
    """
    # Construct logger name
    logger_name = f"screencommander.{domain}"
    if name:
        logger_name = f"{logger_name}.{name}"
    
    # Set up log file
    log_dir = os.getenv("LOG_DIR", "logs")
    log_file = os.path.join(log_dir, f"{domain}.log")
    
    return setup_logger(
        logger_name,
        log_file=log_file,
        **kwargs
    )

class LoggerMixin:
    """Mixin to add logging capabilities to a class."""
    
    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize the logger."""
        super().__init__(*args, **kwargs)
        self.logger = logging.getLogger(self.__class__.__module__)
    
    def log_error(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an error message."""
        self.logger.error(message, *args, **kwargs)
    
    def log_warning(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a warning message."""
        self.logger.warning(message, *args, **kwargs)
    
    def log_info(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log an info message."""
        self.logger.info(message, *args, **kwargs)
    
    def log_debug(self, message: str, *args: Any, **kwargs: Any) -> None:
        """Log a debug message."""
        self.logger.debug(message, *args, **kwargs) 