"""
File operation utilities for photometa-restore.

This module provides functions for file operations such as creating directories,
moving files, and handling common file operations.
"""

import os
import shutil
import time
from typing import Optional, List, Tuple

from ..config import get_config


def create_required_folders(base_path: str) -> Tuple[str, str]:
    """Create the required folders for the application.
    
    Args:
        base_path: The base directory where folders will be created.
        
    Returns:
        Tuple containing paths to matched_media_dir and edited_raw_dir.
    """
    config = get_config()
    
    matched_media_dir = os.path.join(base_path, config.MATCHED_MEDIA_DIR)
    edited_raw_dir = os.path.join(base_path, config.EDITED_RAW_DIR)
    
    if not os.path.exists(matched_media_dir):
        os.makedirs(matched_media_dir)
    
    if not os.path.exists(edited_raw_dir):
        os.makedirs(edited_raw_dir)
    
    return matched_media_dir, edited_raw_dir


def safe_move_file(source_path: str, dest_path: str, max_retries: int = 3, retry_delay: float = 1.0) -> bool:
    """Safely move a file from source to destination.
    
    Args:
        source_path: Path to the source file.
        dest_path: Path to the destination file.
        max_retries: Maximum number of retry attempts.
        retry_delay: Delay in seconds between retries.
    
    Returns:
        bool: True if move was successful, False otherwise.
    """
    retries = 0
    
    while retries < max_retries:
        try:
            if os.path.exists(dest_path):
                os.remove(dest_path)  # Remove existing file if it exists
            
            shutil.move(source_path, dest_path)
            return True
        except PermissionError:
            # File might be in use, wait and retry
            retries += 1
            if retries < max_retries:
                print(f"File is in use, retrying in {retry_delay} seconds... ({retries}/{max_retries})")
                time.sleep(retry_delay)
            else:
                print(f"Failed to move file after {max_retries} attempts: {source_path}")
                return False
        except Exception as e:
            print(f"Error moving file: {str(e)}")
            return False
    
    return False


def fix_title(title: str) -> str:
    """Remove incompatible characters from file titles.
    
    Args:
        title: Original file title.
        
    Returns:
        Sanitized file title.
    """
    incompatible_chars = [
        "%", "<", ">", "=", ":", "?", "¿", "*", "#", "&", 
        "{", "}", "\\", "@", "!", "¿", "+", "|", "\"", "\'"
    ]
    
    result = str(title)
    for char in incompatible_chars:
        result = result.replace(char, "")
    
    return result


def check_if_same_name(title: str, title_fixed: str, media_moved: List[str], recursion_time: int) -> str:
    """Recursively check if a file name already exists in moved media and append suffix if needed.
    
    Args:
        title: Original file title.
        title_fixed: Fixed file title (may have already been processed).
        media_moved: List of already moved media files.
        recursion_time: Counter for recursion to append to filename.
        
    Returns:
        Unique file name.
    """
    if title_fixed in media_moved:
        # Split the title into name and extension (if any)
        parts = title.rsplit('.', 1) if '.' in title else [title, '']
        
        if len(parts) == 2:
            name, ext = parts
            title_fixed = f"{name}({recursion_time}).{ext}"
        else:
            name = parts[0]
            title_fixed = f"{name}({recursion_time})"
            
        return check_if_same_name(title, title_fixed, media_moved, recursion_time + 1)
    else:
        return title_fixed 