"""
Icon data for PhotoMeta Restore.

This module provides access to the application icon.
"""

import os
from pathlib import Path
from typing import Optional, Union

def get_icon_path():
    """Get path to the icon file.
    
    Returns:
        str: Path to the icon file.
    """
    # Get the directory where this script is located
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Construct path to the icon in the icons folder
    icon_file = os.path.join(current_dir, "icons", "app_icon.png")
    
    # If icon doesn't exist, return None
    if not os.path.exists(icon_file):
        print(f"Warning: Icon file not found at {icon_file}")
        return None
    
    return icon_file 

def get_app_icon() -> Optional[Union[bytes, str]]:
    """Get the application icon as bytes.
    
    Returns:
        Bytes representation of the icon or None if not found
    """
    # Check for icon in the resources directory
    icon_path = os.path.join(os.path.dirname(__file__), "app_icon.png")
    
    if os.path.exists(icon_path):
        with open(icon_path, "rb") as icon_file:
            return icon_file.read()
    
    # Fallback to embedded icon if file doesn't exist
    return None 