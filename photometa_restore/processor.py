"""
Core processor module for photometa-restore.

This module contains the main processing logic for matching JSON metadata
to media files and applying metadata.
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Optional, Any, Callable
from pathlib import Path

from .config import get_config
from .utils.logging_utils import setup_logging
from .utils.file_operations import (
    create_required_folders,
    safe_move_file,
    fix_title,
    check_if_same_name
)
from .utils.metadata import (
    set_windows_file_time,
    set_exif_data,
    convert_to_jpg_if_needed,
    extract_metadata_from_json
)
from .utils.metadata_enhanced import MetadataBackup, MetadataTemplate, BatchProcessor
from .utils.validation import validate_metadata_file, FileValidator, ValidationResult


class MediaProcessor:
    """Main class for processing media files and matching them with JSON metadata."""
    
    def __init__(self, base_path: str, edited_suffix: Optional[str] = None):
        """Initialize the processor.
        
        Args:
            base_path: Path to the directory containing media files and JSON metadata.
            edited_suffix: Suffix used for edited media files (default from config if None).
        """
        self.config = get_config()
        self.base_path = Path(base_path).resolve()
        self.edited_suffix = edited_suffix or self.config.DEFAULT_EDITED_SUFFIX
        
        # Setup output directories
        self.matched_media_dir, self.edited_raw_dir = create_required_folders(str(self.base_path))
        
        # Setup logging
        self.error_logger, self.missing_logger = setup_logging(str(self.base_path))
        
        # Track processed files
        self.media_moved: List[str] = []
        self.success_counter = 0
        self.error_counter = 0
        
        # Initialize enhanced metadata handlers
        self.backup_handler = MetadataBackup(str(self.base_path))
        self.template_handler = MetadataTemplate()
        self.batch_processor = BatchProcessor(self)
    
    def search_media_file(self, title: str) -> Optional[str]:
        """Search for media file matching the given title.
        
        Args:
            title: Original title from JSON.
            
        Returns:
            Found media filename or None if not found.
        """
        title = fix_title(title)
        
        try:
            # Split filename and extension
            if '.' in title:
                name, ext = title.rsplit('.', 1)
            else:
                # Handle files without extension
                name = title
                ext = ""
            
            # Define search paths
            search_paths = [
                self.base_path,
                Path(self.matched_media_dir),
                Path(self.edited_raw_dir)
            ]
            
            # Check for edited version with suffix
            if ext:
                edited_name = f"{name}-{self.edited_suffix}.{ext}"
            else:
                edited_name = f"{name}-{self.edited_suffix}"
            
            # Search in all paths
            for search_path in search_paths:
                # Check for edited version
                edited_path = search_path / edited_name
                if edited_path.exists():
                    # If found in base path, move original to edited_raw if it exists
                    if search_path == self.base_path:
                        orig_path = self.base_path / title
                        if orig_path.exists():
                            safe_move_file(str(orig_path), str(Path(self.edited_raw_dir) / title))
                    return edited_name
                
                # Check for version with (1) suffix
                if ext:
                    alt_name = f"{name}(1).{ext}"
                else:
                    alt_name = f"{name}(1)"
                
                alt_path = search_path / alt_name
                if alt_path.exists() and not (search_path / f"{title}(1).json").exists():
                    # If found in base path, move original to edited_raw if it exists
                    if search_path == self.base_path:
                        orig_path = self.base_path / title
                        if orig_path.exists():
                            safe_move_file(str(orig_path), str(Path(self.edited_raw_dir) / title))
                    return alt_name
                
                # Check for original version
                orig_path = search_path / title
                if orig_path.exists():
                    return title
                
                # Check for possible name conflicts
                alt_name = check_if_same_name(title, title, self.media_moved, 1)
                alt_path = search_path / alt_name
                if alt_path.exists():
                    return alt_name
                
                # Try with truncated title (Google sometimes limits to 47 chars)
                if len(name) > 47:
                    short_name = name[:47]
                    
                    if ext:
                        short_title = f"{short_name}.{ext}"
                        short_edited_name = f"{short_name}-{self.edited_suffix}.{ext}"
                    else:
                        short_title = short_name
                        short_edited_name = f"{short_name}-{self.edited_suffix}"
                    
                    short_edited_path = search_path / short_edited_name
                    if short_edited_path.exists():
                        # If found in base path, move original to edited_raw if it exists
                        if search_path == self.base_path:
                            orig_path = search_path / short_title
                            if orig_path.exists():
                                safe_move_file(str(orig_path), str(Path(self.edited_raw_dir) / short_title))
                        return short_edited_name
                    
                    if ext:
                        short_alt_name = f"{short_name}(1).{ext}"
                    else:
                        short_alt_name = f"{short_name}(1)"
                    
                    short_alt_path = search_path / short_alt_name
                    if short_alt_path.exists():
                        # If found in base path, move original to edited_raw if it exists
                        if search_path == self.base_path:
                            orig_path = search_path / short_title
                            if orig_path.exists():
                                safe_move_file(str(orig_path), str(Path(self.edited_raw_dir) / short_title))
                        return short_alt_name
                    
                    short_orig_path = search_path / short_title
                    if short_orig_path.exists():
                        return short_title
                    
                    alt_name = check_if_same_name(short_title, short_title, self.media_moved, 1)
                    alt_path = search_path / alt_name
                    if alt_path.exists():
                        return alt_name
            
            # No matching file found in any location
            return None
            
        except Exception as e:
            error_msg = f"Error searching for media file {title}: {str(e)}"
            print(error_msg)
            self.error_logger.error(error_msg)
            return None
    
    def process_json_file(self, json_file_path: str, progress_callback: Optional[Callable[[float], None]] = None) -> bool:
        """Process a single JSON file and its associated media.
        
        Args:
            json_file_path: Path to the JSON file.
            progress_callback: Optional callback for progress updates.
            
        Returns:
            bool: True if processing was successful, False otherwise.
        """
        try:
            # Convert to Path object and resolve
            json_path = Path(json_file_path).resolve()
            
            # Skip if already processed (JSON file no longer exists)
            if not json_path.exists():
                return True
            
            # Validate metadata file
            validation_result = validate_metadata_file(str(json_path), str(self.base_path))
            if not validation_result.is_valid:
                for error in validation_result.errors:
                    self.error_logger.error(f"Validation error in {json_file_path}: {error}")
                for warning in validation_result.warnings:
                    self.error_logger.warning(f"Validation warning in {json_file_path}: {warning}")
                self.error_counter += 1
                return False
            
            # Load and extract metadata
            with open(json_path, encoding="utf8") as f:
                json_data = json.load(f)
            
            metadata = extract_metadata_from_json(json_data)
            title_original = metadata['title']
            
            # Search for media file
            media_title = self.search_media_file(title_original)
            
            if not media_title:
                self.missing_logger.info(title_original)
                print(f"{title_original} not found")
                self.error_counter += 1
                return False
            
            # Get full path to media file and validate
            media_path = None
            search_paths = [
                self.base_path,
                Path(self.matched_media_dir),
                Path(self.edited_raw_dir)
            ]
            
            # Find the actual file location
            for search_path in search_paths:
                test_path = (search_path / media_title).resolve()
                if test_path.exists():
                    media_path = test_path
                    break
            
            if not media_path:
                self.missing_logger.info(media_title)
                print(f"File not found: {media_title}")
                self.error_counter += 1
                return False
            
            # Validate file access
            file_validator = FileValidator(str(self.base_path))
            is_valid, error = file_validator.validate_file(str(media_path))
            
            if not is_valid:
                self.missing_logger.info(media_title)
                print(f"File validation failed: {error}")
                self.error_counter += 1
                return False
            
            # Get the timestamp
            timestamp = metadata['timestamp']
            print(str(media_path))
            
            # Process EXIF data for supported formats
            ext = media_path.suffix.lower()[1:] if media_path.suffix else ""
            
            if ext in self.config.EXIF_SUPPORTED_FORMATS:
                try:
                    # Convert to JPG if needed
                    media_path = Path(convert_to_jpg_if_needed(str(media_path)))
                    
                    # Set EXIF data if geo data exists
                    geo_data = metadata['geo_data']
                    if any(geo_data.values()):
                        try:
                            set_exif_data(
                                str(media_path),
                                geo_data['latitude'],
                                geo_data['longitude'],
                                geo_data['altitude'],
                                timestamp
                            )
                        except Exception as e:
                            error_msg = f"EXIF data error for {media_path}: {str(e)}"
                            print(error_msg)
                            self.error_logger.error(error_msg)
                            # Continue processing even if EXIF fails
                
                except Exception as e:
                    error_msg = f"Error processing image {media_title}: {str(e)}"
                    print(error_msg)
                    self.error_logger.error(error_msg)
                    self.error_counter += 1
                    return False
            
            # Set file timestamps
            try:
                set_windows_file_time(str(media_path), timestamp)
            except Exception as e:
                error_msg = f"Error setting file time for {media_path}: {str(e)}"
                print(error_msg)
                self.error_logger.error(error_msg)
            
            # Move file and delete JSON
            try:
                dest_path = Path(self.matched_media_dir) / media_path.name
                if safe_move_file(str(media_path), str(dest_path)):
                    os.remove(json_path)
                    self.media_moved.append(media_title)
                    self.success_counter += 1
                    return True
                else:
                    error_msg = f"Error moving file {media_path}"
                    print(error_msg)
                    self.error_logger.error(error_msg)
                    self.error_counter += 1
                    return False
                    
            except Exception as e:
                error_msg = f"Error moving file {media_path}: {str(e)}"
                print(error_msg)
                self.error_logger.error(error_msg)
                self.error_counter += 1
                return False
                
        except Exception as e:
            error_msg = f"Error processing JSON {json_file_path}: {str(e)}"
            print(error_msg)
            self.error_logger.error(error_msg)
            self.error_counter += 1
            return False
    
    def process_all(self, progress_callback: Optional[Callable[[float, int, int], None]] = None) -> Tuple[int, int]:
        """Process all JSON files in the base directory.
        
        Args:
            progress_callback: Optional callback for progress updates.
            
        Returns:
            Tuple of (success_count, error_count).
        """
        self.error_logger.error("=== Starting new processing session ===")
        self.missing_logger.info("=== Missing Files List ===")
        
        try:
            # Get all JSON files
            json_files = []
            for entry in os.scandir(self.base_path):
                if entry.is_file() and entry.name.endswith(".json"):
                    json_files.append(entry.path)
            
            # Sort by name length to process shorter names first
            json_files.sort(key=lambda s: len(os.path.basename(s)))
            total_files = len(json_files)
            
            # Process each JSON file
            for i, json_file in enumerate(json_files):
                # Calculate progress
                progress = (i / total_files) * 100 if total_files > 0 else 0
                
                # Update progress if callback provided
                if progress_callback:
                    progress_callback(progress, self.success_counter, self.error_counter)
                
                # Process the JSON file
                self.process_json_file(json_file)
        
        except Exception as e:
            error_msg = f"Error during processing: {str(e)}"
            print(error_msg)
            self.error_logger.error(error_msg)
        
        self.error_logger.error("=== Processing session ended ===")
        self.missing_logger.info("\n=== Processing session ended ===")
        
        return self.success_counter, self.error_counter

    def apply_template(self, media_file: str, template_name: str) -> bool:
        """Apply a metadata template to a media file.
        
        Args:
            media_file: Path to the media file
            template_name: Name of the template to apply
            
        Returns:
            True if successful, False otherwise
        """
        try:
            template = self.template_handler.load_template(template_name)
            return self.apply_metadata(media_file, template)
        except Exception as e:
            self.error_logger.error(f"Failed to apply template {template_name} to {media_file}: {str(e)}")
            return False

    def process_batch(self, files: List[str], progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
        """Process a batch of files with automatic backup.
        
        Args:
            files: List of files to process
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dictionary with processing results
        """
        return self.batch_processor.process_batch(files, progress_callback)

    def backup_metadata(self, file_path: str) -> Optional[str]:
        """Create a backup of file metadata.
        
        Args:
            file_path: Path to the file to backup
            
        Returns:
            Path to backup file if successful, None otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            return self.backup_handler.create_backup(file_path, metadata)
        except Exception as e:
            self.error_logger.error(f"Failed to create backup for {file_path}: {str(e)}")
            return None

    def restore_from_backup(self, backup_path: str) -> bool:
        """Restore metadata from a backup file.
        
        Args:
            backup_path: Path to the backup file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            original_file, metadata = self.backup_handler.restore_from_backup(backup_path)
            return self.apply_metadata(original_file, metadata)
        except Exception as e:
            self.error_logger.error(f"Failed to restore from backup {backup_path}: {str(e)}")
            return False

    def apply_metadata(self, media_file: str, metadata: Dict[str, Any]) -> bool:
        """Apply metadata to a media file.
        
        Args:
            media_file: Path to the media file
            metadata: Metadata to apply
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Extract metadata in the correct format
            processed_metadata = extract_metadata_from_json(metadata)
            
            # Get file extension
            ext = os.path.splitext(media_file)[1].lower()[1:]
            
            # Process EXIF data for supported formats
            if ext in self.config.EXIF_SUPPORTED_FORMATS:
                try:
                    # Convert to JPG if needed
                    media_file = convert_to_jpg_if_needed(media_file)
                    
                    # Set EXIF data if geo data exists
                    geo_data = processed_metadata['geo_data']
                    if any(geo_data.values()):
                        set_exif_data(
                            media_file,
                            geo_data['latitude'],
                            geo_data['longitude'],
                            geo_data['altitude'],
                            processed_metadata['timestamp']
                        )
                except Exception as e:
                    self.error_logger.error(f"EXIF data error for {media_file}: {str(e)}")
                    return False
            
            # Set file timestamps
            try:
                set_windows_file_time(media_file, processed_metadata['timestamp'])
            except Exception as e:
                self.error_logger.error(f"Error setting file time for {media_file}: {str(e)}")
                return False
            
            return True
            
        except Exception as e:
            self.error_logger.error(f"Failed to apply metadata to {media_file}: {str(e)}")
            return False


def process_directory(
    directory: str,
    edited_suffix: Optional[str] = None,
    progress_callback: Optional[Callable[[float, int, int], None]] = None
) -> Tuple[int, int]:
    """Process a directory containing Google Photos Takeout media and JSONs.
    
    Args:
        directory: Path to the directory to process.
        edited_suffix: Optional suffix for edited photos.
        progress_callback: Optional callback for progress updates.
        
    Returns:
        Tuple of (success_count, error_count).
    """
    processor = MediaProcessor(directory, edited_suffix)
    return processor.process_all(progress_callback) 