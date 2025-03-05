"""
Validation utilities for photometa-restore.

This module provides validation and error handling functionality for metadata operations.
"""

import os
import json
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class ValidationResult:
    """Container for validation results."""
    is_valid: bool
    errors: list[str]
    warnings: list[str]


class MetadataValidator:
    """Validates metadata structure and content."""
    
    REQUIRED_FIELDS = {
        'title': str,
        'photoTakenTime': dict,
        'geoData': dict
    }
    
    TIMESTAMP_FIELDS = {
        'photoTakenTime': ['timestamp', 'formatted']
    }
    
    GEO_FIELDS = {
        'latitude': (-90, 90),
        'longitude': (-180, 180),
        'altitude': (None, None)  # No specific range
    }
    
    def __init__(self):
        """Initialize the validator."""
        self.reset()
    
    def reset(self):
        """Reset validation state."""
        self._errors = []
        self._warnings = []
    
    def validate_metadata(self, metadata: Dict[str, Any]) -> ValidationResult:
        """Validate metadata structure and content.
        
        Args:
            metadata: Metadata dictionary to validate
            
        Returns:
            ValidationResult with validation status and messages
        """
        self.reset()
        
        # Check required fields
        self._validate_required_fields(metadata)
        
        # Validate specific sections if they exist
        if 'photoTakenTime' in metadata:
            self._validate_timestamp(metadata['photoTakenTime'])
        
        if 'geoData' in metadata:
            self._validate_geo_data(metadata['geoData'])
        
        return ValidationResult(
            is_valid=len(self._errors) == 0,
            errors=self._errors.copy(),
            warnings=self._warnings.copy()
        )
    
    def _validate_required_fields(self, metadata: Dict[str, Any]):
        """Validate presence and types of required fields."""
        for field, expected_type in self.REQUIRED_FIELDS.items():
            if field not in metadata:
                self._errors.append(f"Missing required field: {field}")
            elif not isinstance(metadata[field], expected_type):
                self._errors.append(
                    f"Invalid type for {field}: expected {expected_type.__name__}, "
                    f"got {type(metadata[field]).__name__}"
                )
    
    def _validate_timestamp(self, timestamp_data: Dict[str, Any]):
        """Validate timestamp data."""
        for field in self.TIMESTAMP_FIELDS['photoTakenTime']:
            if field not in timestamp_data:
                self._errors.append(f"Missing timestamp field: {field}")
        
        if 'timestamp' in timestamp_data:
            try:
                timestamp = int(timestamp_data['timestamp'])
                # Check if timestamp is in reasonable range (1970-2100)
                if not (0 <= timestamp <= 4102444800):  # Jan 1, 1970 to Jan 1, 2100
                    self._warnings.append("Timestamp outside reasonable range")
            except ValueError:
                self._errors.append("Invalid timestamp format")
    
    def _validate_geo_data(self, geo_data: Dict[str, Any]):
        """Validate geographic data."""
        for field, (min_val, max_val) in self.GEO_FIELDS.items():
            if field in geo_data:
                try:
                    value = float(geo_data[field])
                    if min_val is not None and value < min_val:
                        self._errors.append(f"{field} below minimum value: {value} < {min_val}")
                    if max_val is not None and value > max_val:
                        self._errors.append(f"{field} above maximum value: {value} > {max_val}")
                except ValueError:
                    self._errors.append(f"Invalid {field} format")


class FileValidator:
    """Validates file existence and accessibility."""
    
    def __init__(self, base_path: str):
        """Initialize file validator.
        
        Args:
            base_path: Base directory for file operations
        """
        self.base_path = Path(base_path).resolve()
    
    def validate_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate file existence and accessibility.
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(file_path)
            if not path.is_absolute():
                path = (self.base_path / path).resolve()
            
            # Convert to string for os.access
            path_str = str(path)
            
            if not path.exists():
                return False, f"File not found: {path_str}"
            
            if not path.is_file():
                return False, f"Not a file: {path_str}"
            
            # Check read access
            if not os.access(path_str, os.R_OK):
                return False, f"No read permission: {path_str}"
            
            # Check write access
            if not os.access(path_str, os.W_OK):
                return False, f"No write permission: {path_str}"
            
            return True, None
            
        except Exception as e:
            return False, f"Error validating file {file_path}: {str(e)}"
    
    def validate_json_file(self, file_path: str) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """Validate JSON file existence and content.
        
        Args:
            file_path: Path to the JSON file
            
        Returns:
            Tuple of (is_valid, error_message, parsed_content)
        """
        is_valid, error = self.validate_file(file_path)
        if not is_valid:
            return False, error, None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
            return True, None, content
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format in {file_path}: {str(e)}", None
        except Exception as e:
            return False, f"Error reading JSON file {file_path}: {str(e)}", None


def validate_metadata_file(file_path: str, base_path: Optional[str] = None) -> ValidationResult:
    """Validate a metadata file.
    
    Args:
        file_path: Path to the metadata file
        base_path: Optional base directory for relative paths
        
    Returns:
        ValidationResult with validation status and messages
    """
    if base_path is None:
        base_path = os.path.dirname(file_path)
    
    file_validator = FileValidator(base_path)
    metadata_validator = MetadataValidator()
    
    # Validate file first
    is_valid, error, content = file_validator.validate_json_file(file_path)
    if not is_valid:
        return ValidationResult(
            is_valid=False,
            errors=[error],
            warnings=[]
        )
    
    # Validate metadata content
    return metadata_validator.validate_metadata(content) 