"""
Utility functions for testing metadata processing.
"""

import os
import piexif
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, Tuple

def get_file_timestamp(file_path: Path) -> int:
    """Get the file's last write timestamp.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Unix timestamp of last write time
    """
    return int(os.path.getmtime(file_path))

def get_gps_data(image_path: Path) -> Optional[Dict[str, float]]:
    """Extract GPS data from image EXIF.
    
    Args:
        image_path: Path to the image file
        
    Returns:
        Dictionary with latitude, longitude, altitude or None if no GPS data
    """
    try:
        exif_dict = piexif.load(str(image_path))
        if "GPS" not in exif_dict or not exif_dict["GPS"]:
            return None
            
        gps_data = exif_dict["GPS"]
        
        def convert_to_degrees(value: Tuple[Tuple[int, int], ...]) -> float:
            """Convert GPS coordinates to decimal degrees."""
            d = float(value[0][0]) / float(value[0][1])
            m = float(value[1][0]) / float(value[1][1])
            s = float(value[2][0]) / float(value[2][1])
            return d + (m / 60.0) + (s / 3600.0)
        
        # Extract latitude
        if all(tag in gps_data for tag in [1, 2, 3, 4]):  # Required GPS tags
            lat = convert_to_degrees(gps_data[2])
            lat_ref = gps_data[1].decode('ascii')
            latitude = lat if lat_ref == 'N' else -lat
            
            lon = convert_to_degrees(gps_data[4])
            lon_ref = gps_data[3].decode('ascii')
            longitude = lon if lon_ref == 'E' else -lon
            
            # Extract altitude if available
            altitude = None
            if 6 in gps_data:
                alt = float(gps_data[6][0]) / float(gps_data[6][1])
                alt_ref = gps_data.get(5, 0)  # 0 = above sea level
                altitude = alt if not alt_ref else -alt
            
            return {
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
                "altitude": round(altitude, 1) if altitude is not None else None
            }
            
    except Exception as e:
        print(f"Error reading EXIF from {image_path}: {str(e)}")
        return None
    
    return None

def format_timestamp(timestamp: int) -> str:
    """Format a Unix timestamp as a human-readable string.
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Formatted datetime string
    """
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") 