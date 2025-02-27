"""
Logging utilities for photometa-restore.

This module provides functions to set up and configure loggers for the application.
"""

import os
import logging
from datetime import datetime
from typing import Tuple

from ..config import get_config


def setup_logging(base_path: str) -> Tuple[logging.Logger, logging.Logger]:
    """Set up logging for the application.
    
    Args:
        base_path: The base directory where log files will be stored.
        
    Returns:
        Tuple containing error_logger and missing_files_logger.
    """
    config = get_config()
    
    # Create logs directory
    logs_dir = os.path.join(base_path, config.LOGS_DIR)
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    
    # Get timestamps for log file names
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    error_log_filename = config.ERROR_LOG_PATTERN.format(timestamp=timestamp)
    missing_files_log_filename = config.MISSING_FILES_LOG_PATTERN.format(timestamp=timestamp)
    
    error_log_path = os.path.join(logs_dir, error_log_filename)
    missing_files_log_path = os.path.join(logs_dir, missing_files_log_filename)
    
    # Configure error logger
    error_logger = logging.getLogger('error_logger')
    error_logger.setLevel(logging.ERROR)
    
    # Reset handlers if they exist (to avoid duplicates)
    if error_logger.handlers:
        error_logger.handlers.clear()
        
    error_handler = logging.FileHandler(error_log_path, encoding='utf-8')
    error_handler.setFormatter(logging.Formatter('%(asctime)s - %(message)s'))
    error_logger.addHandler(error_handler)
    
    # Configure missing files logger
    missing_logger = logging.getLogger('missing_logger')
    missing_logger.setLevel(logging.INFO)
    
    # Reset handlers if they exist
    if missing_logger.handlers:
        missing_logger.handlers.clear()
        
    missing_handler = logging.FileHandler(missing_files_log_path, encoding='utf-8')
    missing_handler.setFormatter(logging.Formatter('%(message)s'))
    missing_logger.addHandler(missing_handler)
    
    return error_logger, missing_logger 