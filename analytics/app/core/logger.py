import os
import logging
import logging.handlers
from typing import Optional
from pathlib import Path

def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    log_dir: str = "logs",
    log_format: Optional[str] = None,
    error_log_format: Optional[str] = None
) -> None:
    """
    Setup logging configuration for the service.
    
    Args:
        service_name: Name of the service for log identification
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory to store log files
        log_format: Optional custom log format
        error_log_format: Optional custom error log format
    """
    try:
        # Create log directory if it doesn't exist
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Set default log formats if not provided
        if log_format is None:
            log_format = (
                "%(asctime)s | %(service_name)s | %(levelname)-8s | "
                "%(filename)s:%(lineno)d | %(message)s"
            )
        
        if error_log_format is None:
            error_log_format = (
                "%(asctime)s | %(service_name)s | %(levelname)-8s | "
                "%(filename)s:%(lineno)d | %(funcName)s | %(message)s"
            )
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(log_level)
        
        # Clear any existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Create formatters
        formatter = logging.Formatter(log_format)
        error_formatter = logging.Formatter(error_log_format)
        
        # Add console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
        
        # Add file handler for all logs
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path / f"{service_name}.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
        
        # Add file handler for error logs
        error_file_handler = logging.handlers.RotatingFileHandler(
            filename=log_path / f"{service_name}_errors.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(error_formatter)
        root_logger.addHandler(error_file_handler)
        
        # Add filter to inject service name
        class ServiceNameFilter(logging.Filter):
            def filter(self, record):
                record.service_name = service_name
                return True
        
        # Add service name filter to all handlers
        service_filter = ServiceNameFilter()
        for handler in root_logger.handlers:
            handler.addFilter(service_filter)
        
        # Log successful initialization
        root_logger.info(f"Logging initialized for {service_name}")
        root_logger.info(f"Log level: {log_level}")
        root_logger.info(f"Log file: {log_path / f'{service_name}.log'}")
        root_logger.info(f"Error log file: {log_path / f'{service_name}_errors.log'}")
        
    except Exception as e:
        # If logging setup fails, configure basic logging as fallback
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(message)s'
        )
        logging.error(f"Failed to setup logging: {str(e)}")
        # Don't raise the exception - we want the application to start even if logging setup fails 