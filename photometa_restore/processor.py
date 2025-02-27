"""
Core processor module for photometa-restore.

This module contains the main processing logic for matching JSON metadata
to media files and applying metadata.
"""

import os
import json
import logging
from typing import Dict, List, Tuple, Optional, Any, Callable

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


class MediaProcessor:
    """Main class for processing media files and matching them with JSON metadata."""
    
    def __init__(self, base_path: str, edited_suffix: Optional[str] = None):
        """Initialize the processor.
        
        Args:
            base_path: Path to the directory containing media files and JSON metadata.
            edited_suffix: Suffix used for edited media files (default from config if None).
        """
        self.config = get_config()
        self.base_path = base_path
        self.edited_suffix = edited_suffix or self.config.DEFAULT_EDITED_SUFFIX
        
        # Setup output directories
        self.matched_media_dir, self.edited_raw_dir = create_required_folders(base_path)
        
        # Setup logging
        self.error_logger, self.missing_logger = setup_logging(base_path)
        
        # Track processed files
        self.media_moved: List[str] = []
        self.success_counter = 0
        self.error_counter = 0
    
    def search_media_file(self, title: str) -> Optional[str]:
        """Search for media file matching the given title.
        
        Args:
            title: Original title from JSON.
            
        Returns:
            Found media filename or None if not found.
        """
        title = fix_title(title)
        
        # Try to find edited version of the file
        try:
            # Split filename and extension
            if '.' in title:
                name, ext = title.rsplit('.', 1)
            else:
                # Handle files without extension
                name = title
                ext = ""
            
            # Check for edited version with suffix
            if ext:
                edited_name = f"{name}-{self.edited_suffix}.{ext}"
            else:
                edited_name = f"{name}-{self.edited_suffix}"
                
            edited_path = os.path.join(self.base_path, edited_name)
            
            if os.path.exists(edited_path):
                # Move original to edited_raw_dir if we find the edited version
                orig_path = os.path.join(self.base_path, title)
                if os.path.exists(orig_path):
                    safe_move_file(orig_path, os.path.join(self.edited_raw_dir, title))
                return edited_name
            
            # Check for version with (1) suffix
            if ext:
                alt_name = f"{name}(1).{ext}"
            else:
                alt_name = f"{name}(1)"
                
            alt_path = os.path.join(self.base_path, alt_name)
            
            if os.path.exists(alt_path) and not os.path.exists(os.path.join(self.base_path, f"{title}(1).json")):
                # Move original to edited_raw_dir if we find alt version
                orig_path = os.path.join(self.base_path, title)
                if os.path.exists(orig_path):
                    safe_move_file(orig_path, os.path.join(self.edited_raw_dir, title))
                return alt_name
            
            # Check for original version
            orig_path = os.path.join(self.base_path, title)
            if os.path.exists(orig_path):
                return title
            
            # Check for possible name conflicts and add suffix if needed
            alt_name = check_if_same_name(title, title, self.media_moved, 1)
            alt_path = os.path.join(self.base_path, alt_name)
            if os.path.exists(alt_path):
                return alt_name
            
            # Try with truncated title (Google sometimes limits to 47 chars)
            if len(name) > 47:
                short_name = name[:47]
                
                if ext:
                    short_title = f"{short_name}.{ext}"
                    # Try similar patterns with the short title
                    short_edited_name = f"{short_name}-{self.edited_suffix}.{ext}"
                else:
                    short_title = short_name
                    short_edited_name = f"{short_name}-{self.edited_suffix}"
                    
                short_edited_path = os.path.join(self.base_path, short_edited_name)
                
                if os.path.exists(short_edited_path):
                    orig_path = os.path.join(self.base_path, short_title)
                    if os.path.exists(orig_path):
                        safe_move_file(orig_path, os.path.join(self.edited_raw_dir, short_title))
                    return short_edited_name
                
                if ext:
                    short_alt_name = f"{short_name}(1).{ext}"
                else:
                    short_alt_name = f"{short_name}(1)"
                    
                short_alt_path = os.path.join(self.base_path, short_alt_name)
                
                if os.path.exists(short_alt_path):
                    orig_path = os.path.join(self.base_path, short_title)
                    if os.path.exists(orig_path):
                        safe_move_file(orig_path, os.path.join(self.edited_raw_dir, short_title))
                    return short_alt_name
                
                short_orig_path = os.path.join(self.base_path, short_title)
                if os.path.exists(short_orig_path):
                    return short_title
                
                alt_name = check_if_same_name(short_title, short_title, self.media_moved, 1)
                alt_path = os.path.join(self.base_path, alt_name)
                if os.path.exists(alt_path):
                    return alt_name
            
            # No matching file found
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
            # Load JSON data
            with open(json_file_path, encoding="utf8") as f:
                json_data = json.load(f)
            
            # Extract metadata
            metadata = extract_metadata_from_json(json_data)
            title_original = metadata['title']
            
            # Search for media file
            media_title = self.search_media_file(title_original)
            
            if not media_title:
                self.missing_logger.info(title_original)
                print(f"{title_original} not found")
                self.error_counter += 1
                return False
            
            # Get full path to media file
            media_path = os.path.join(self.base_path, media_title)
            
            if not os.path.exists(media_path):
                self.missing_logger.info(media_title)
                print(f"File not found: {media_path}")
                self.error_counter += 1
                return False
            
            # Get the timestamp
            timestamp = metadata['timestamp']
            print(media_path)
            
            # Process EXIF data for supported formats
            ext = ""
            if '.' in media_title:
                _, ext = media_title.rsplit('.', 1)
                ext = ext.casefold()
                
            if ext in self.config.EXIF_SUPPORTED_FORMATS:
                try:
                    # Convert to JPG if needed
                    media_path = convert_to_jpg_if_needed(media_path)
                    
                    # Set EXIF data if geo data exists
                    geo_data = metadata['geo_data']
                    if any(geo_data.values()):
                        try:
                            set_exif_data(
                                media_path,
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
                set_windows_file_time(media_path, timestamp)
            except Exception as e:
                error_msg = f"Error setting file time for {media_path}: {str(e)}"
                print(error_msg)
                self.error_logger.error(error_msg)
            
            # Move file and delete JSON
            try:
                dest_path = os.path.join(self.matched_media_dir, os.path.basename(media_path))
                if safe_move_file(media_path, dest_path):
                    os.remove(json_file_path)
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