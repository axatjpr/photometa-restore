"""
Icon data for PhotoMeta Restore.

This module provides access to the application icon.
"""

import os
from pathlib import Path

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