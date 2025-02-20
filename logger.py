"""
Module for initializing and configuring loggers for the web scraping application.
Handles both file and console logging with appropriate formatting.
"""

import os
import logging
import inspect
from datetime import datetime
from typing import Optional

# Configuration constants
LOG_LEVEL = "INFO"
LOG_FOLDER = "logs"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
SCRAPER_LOG = "scraper.log"
ANALYSIS_LOG = "analysis.log"
ERROR_LOG = "error.log"

def setup_log_folder() -> None:
    """Create logging directory if it doesn't exist."""
    try:
        if not os.path.exists(LOG_FOLDER):
            os.makedirs(LOG_FOLDER)
    except Exception as e:
        print(f"Failed to create log folder: {str(e)}")

def get_module_logger(name: str) -> logging.Logger:
    """
    Initialize and return a logger for a specific module.

    Args:
        name (str): Name of the module requesting the logger

    Returns:
        logging.Logger: Configured logger instance
    """
    # Transform __main__ to app for the logger name
    logger_name = "app" if name == "__main__" else name
    logger = logging.getLogger(logger_name)

    # Return existing logger if it's already configured
    if logger.hasHandlers():
        return logger

    # Set base logging level
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    try:
        setup_log_folder()

        # Get caller information
        caller_frame = inspect.stack()[1]
        module_name = os.path.splitext(os.path.basename(caller_frame.filename))[0]

        # Set up file handlers for different log types
        handlers = _create_handlers(module_name)
        formatter = logging.Formatter(LOG_FORMAT)

        for handler in handlers:
            handler.setFormatter(formatter)
            logger.addHandler(handler)

    except Exception as e:
        # Fallback to console logging if file logging fails
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(console_handler)
        logger.warning(f"Defaulting to console logging due to error: {str(e)}")

    return logger

def _create_handlers(module_name: str) -> list:
    """
    Create and return appropriate log handlers based on the module.

    Args:
        module_name (str): Name of the module requesting handlers

    Returns:
        list: List of configured handlers
    """
    handlers = []

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    handlers.append(console_handler)

    # Create module-specific file handler
    module_log = os.path.join(LOG_FOLDER, f"{module_name}.log")
    file_handler = logging.FileHandler(module_log)
    file_handler.setLevel(logging.DEBUG)
    handlers.append(file_handler)

    # Add error handler for all modules
    error_handler = logging.FileHandler(os.path.join(LOG_FOLDER, ERROR_LOG))
    error_handler.setLevel(logging.ERROR)
    handlers.append(error_handler)

    # Add specific handlers based on module
    if module_name == "scraper":
        scraper_handler = logging.FileHandler(os.path.join(LOG_FOLDER, SCRAPER_LOG))
        scraper_handler.setLevel(logging.INFO)
        handlers.append(scraper_handler)
    elif module_name == "analysis":
        analysis_handler = logging.FileHandler(os.path.join(LOG_FOLDER, ANALYSIS_LOG))
        analysis_handler.setLevel(logging.INFO)
        handlers.append(analysis_handler)

    return handlers

def get_request_logger(request_id: str) -> logging.Logger:
    """
    Get a logger specifically for tracking a single scraping request.

    Args:
        request_id (str): Unique identifier for the request

    Returns:
        logging.Logger: Logger configured for the specific request
    """
    logger = logging.getLogger(f"request_{request_id}")

    if logger.hasHandlers():
        return logger

    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    try:
        setup_log_folder()

        # Create request-specific log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(LOG_FOLDER, f"request_{request_id}_{timestamp}.log")

        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(handler)

    except Exception as e:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        logger.addHandler(console_handler)
        logger.warning(f"Failed to create request log file: {str(e)}")

    return logger

def init(name: str) -> logging.Logger:
    """
    Initialize a logger with the given name. Main entry point for backward compatibility.

    Args:
        name (str): Name of the module requesting the logger

    Returns:
        logging.Logger: Configured logger instance
    """
    return get_module_logger(name)