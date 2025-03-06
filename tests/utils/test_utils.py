"""
Utility functions for tests.
"""

import os
import piexif
from datetime import datetime, timezone
from typing import Dict, Optional, Union
from pathlib import Path


def get_file_timestamp(file_path: str) -> int:
    """Get the modification timestamp of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Unix timestamp as integer
    """
    return int(os.path.getmtime(file_path))


def format_timestamp(timestamp: int) -> str:
    """Format a Unix timestamp as a human-readable string.
    
    Args:
        timestamp: Unix timestamp
        
    Returns:
        Formatted datetime string
    """
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def get_gps_data(file_path: str) -> Optional[Dict[str, float]]:
    """Extract GPS data from an image file's EXIF.
    
    Args:
        file_path: Path to the image file
        
    Returns:
        Dictionary with latitude, longitude, and altitude if GPS data exists,
        None otherwise
    """
    try:
        exif_dict = piexif.load(str(file_path))
        if "GPS" not in exif_dict or not exif_dict["GPS"]:
            return None
        
        gps_data = exif_dict["GPS"]
        
        def convert_to_degrees(value: tuple) -> float:
            """Convert GPS coordinates to decimal degrees."""
            d = float(value[0][0]) / float(value[0][1])
            m = float(value[1][0]) / float(value[1][1])
            s = float(value[2][0]) / float(value[2][1])
            return d + (m / 60.0) + (s / 3600.0)
        
        # Extract latitude
        if all(tag in gps_data for tag in [piexif.GPSIFD.GPSLatitude, piexif.GPSIFD.GPSLatitudeRef,
                                         piexif.GPSIFD.GPSLongitude, piexif.GPSIFD.GPSLongitudeRef]):
            lat = convert_to_degrees(gps_data[piexif.GPSIFD.GPSLatitude])
            lat_ref = gps_data[piexif.GPSIFD.GPSLatitudeRef].decode('ascii')
            latitude = lat if lat_ref == 'N' else -lat
            
            lon = convert_to_degrees(gps_data[piexif.GPSIFD.GPSLongitude])
            lon_ref = gps_data[piexif.GPSIFD.GPSLongitudeRef].decode('ascii')
            longitude = lon if lon_ref == 'E' else -lon
            
            # Extract altitude if available
            altitude = 0.0
            if piexif.GPSIFD.GPSAltitude in gps_data:
                alt = float(gps_data[piexif.GPSIFD.GPSAltitude][0]) / float(gps_data[piexif.GPSIFD.GPSAltitude][1])
                alt_ref = gps_data.get(piexif.GPSIFD.GPSAltitudeRef, 0)
                altitude = alt if not alt_ref else -alt
            
            return {
                "latitude": round(latitude, 4),
                "longitude": round(longitude, 4),
                "altitude": round(altitude, 1)
            }
            
    except Exception as e:
        print(f"Error reading EXIF from {file_path}: {e}")
        return None
    
    return None 