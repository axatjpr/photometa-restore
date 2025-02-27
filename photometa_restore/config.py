"""
Configuration settings for the PhotoMeta Restore application.

This module contains default values and settings that can be customized by the user.
"""

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

# Version information
__version__ = '1.0.0'


@dataclass
class Config:
    """Main configuration class for PhotoMeta Restore."""
    
    # Version information
    __version__: str = __version__
    
    # Default suffix for edited photos
    DEFAULT_EDITED_SUFFIX: str = "edited"
    
    # Supported file formats for EXIF manipulation
    EXIF_SUPPORTED_FORMATS: List[str] = field(
        default_factory=lambda: ["tif", "tiff", "jpeg", "jpg"]
    )
    
    # Directory names
    MATCHED_MEDIA_DIR: str = "MatchedMedia"
    EDITED_RAW_DIR: str = "EditedRaw"
    LOGS_DIR: str = "logs"
    
    # Log file naming patterns
    ERROR_LOG_PATTERN: str = "errors_{timestamp}.log"
    MISSING_FILES_LOG_PATTERN: str = "missing_files_{timestamp}.log"
    
    # Error messages
    ERROR_MESSAGES: Dict[str, str] = field(
        default_factory=lambda: {
            "invalid_directory": "Please select a valid directory",
            "file_not_found": "File not found: {filepath}",
            "processing_error": "Error processing file: {error}",
            "metadata_error": "Error setting metadata: {error}",
            "moving_error": "Error moving file: {error}",
        }
    )
    
    # Success message templates
    SUCCESS_MESSAGE: str = "Matching process finished with {success_count} {success_word} and {error_count} {error_word}."
    
    # UI color themes - using modern, professional colors
    UI_COLORS: Dict[str, str] = field(
        default_factory=lambda: {
            "primary_color": "#2C5282",  # Deep blue
            "secondary_color": "#4A5568", # Dark slate gray
            "accent_color": "#3182CE",    # Bright blue
            "background_color": "#F7FAFC", # Very light blue/gray
            "success_color": "#38A169",   # Green
            "error_color": "#E53E3E",     # Red
            "processing_color": "#3182CE" # Blue
        }
    )


# Create a global config instance
config = Config()


def get_config() -> Config:
    """Get the global configuration instance.
    
    Returns:
        Config: The global configuration object.
    """
    return config


def update_config(updates: Dict[str, Any]) -> None:
    """Update configuration values.
    
    Args:
        updates: Dictionary of configuration values to update.
    """
    for key, value in updates.items():
        if hasattr(config, key):
            setattr(config, key, value) 