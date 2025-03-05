"""
Metadata utilities for photometa-restore.

This module provides functions for manipulating metadata in media files,
including EXIF data and file timestamps.
"""

import os
import time
from datetime import datetime
from typing import Dict, Any

import piexif
from win32_setctime import setctime
from PIL import Image


def set_windows_file_time(filepath: str, timestamp: int) -> None:
    """Set Windows file creation and modification time.
    
    Args:
        filepath: Path to the file.
        timestamp: Unix timestamp to set.
    """
    setctime(filepath, timestamp)  # Set windows file creation time
    date = datetime.fromtimestamp(timestamp)
    mod_time = time.mktime(date.timetuple())
    os.utime(filepath, (mod_time, mod_time))  # Set windows file modification time


def set_exif_data(file_path: str, latitude: float, longitude: float, altitude: float, timestamp: int) -> None:
    """Set EXIF data in an image file.
    
    Args:
        file_path: Path to the image file
        latitude: GPS latitude
        longitude: GPS longitude
        altitude: GPS altitude in meters
        timestamp: Unix timestamp
    """
    try:
        # Load existing EXIF data or create new
        try:
            exif_dict = piexif.load(file_path)
        except:
            exif_dict = {
                "0th": {},
                "Exif": {},
                "GPS": {},
                "1st": {},
                "thumbnail": None
            }
        
        # Convert latitude to degrees/minutes/seconds
        lat_deg = int(abs(latitude))
        lat_min = int((abs(latitude) - lat_deg) * 60)
        lat_sec = int(((abs(latitude) - lat_deg) * 60 - lat_min) * 60 * 100)
        
        # Convert longitude to degrees/minutes/seconds
        lon_deg = int(abs(longitude))
        lon_min = int((abs(longitude) - lon_deg) * 60)
        lon_sec = int(((abs(longitude) - lon_deg) * 60 - lon_min) * 60 * 100)
        
        # Set GPS data
        exif_dict["GPS"] = {
            piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
            piexif.GPSIFD.GPSLatitudeRef: 'N' if latitude >= 0 else 'S',
            piexif.GPSIFD.GPSLatitude: ((lat_deg, 1), (lat_min, 1), (lat_sec, 100)),
            piexif.GPSIFD.GPSLongitudeRef: 'E' if longitude >= 0 else 'W',
            piexif.GPSIFD.GPSLongitude: ((lon_deg, 1), (lon_min, 1), (lon_sec, 100)),
            piexif.GPSIFD.GPSAltitudeRef: 1 if altitude < 0 else 0,  # 0 = above sea level
            piexif.GPSIFD.GPSAltitude: (int(abs(altitude) * 10), 10)
        }
        
        # Set date/time
        try:
            dt = datetime.fromtimestamp(timestamp)
            date_str = dt.strftime("%Y:%m:%d %H:%M:%S")
            exif_dict["0th"][piexif.ImageIFD.DateTime] = date_str
            exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = date_str
            exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = date_str
        except Exception as e:
            print(f"Warning: Could not set date/time EXIF for {file_path}: {str(e)}")
        
        # Save EXIF data
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, file_path)
        
    except Exception as e:
        raise Exception(f"Error setting EXIF data for {file_path}: {str(e)}")


def convert_to_jpg_if_needed(filepath: str) -> str:
    """Convert an image to JPG format if it's not already in RGB mode.
    
    Args:
        filepath: Path to the image file.
        
    Returns:
        Path to the converted file (may be the same as input if no conversion needed).
    """
    with Image.open(filepath) as img:
        if img.mode != 'RGB':
            # Convert to RGB
            rgb_img = img.convert('RGB')
            
            # Create new filename with .jpg extension
            new_filepath = filepath.rsplit('.', 1)[0] + ".jpg"
            
            # Only save if converting to a different file
            if filepath != new_filepath:
                rgb_img.save(new_filepath)
                
                # Delete old file if it exists
                if os.path.exists(filepath):
                    os.remove(filepath)
                    
                return new_filepath
    
    return filepath


def extract_metadata_from_json(json_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract relevant metadata from JSON data.
    
    Args:
        json_data: JSON data loaded from file.
        
    Returns:
        Dictionary of extracted metadata.
    """
    metadata = {
        'title': json_data.get('title', ''),
        'timestamp': int(json_data.get('photoTakenTime', {}).get('timestamp', 0)),
        'geo_data': {
            'latitude': json_data.get('geoData', {}).get('latitude', 0),
            'longitude': json_data.get('geoData', {}).get('longitude', 0),
            'altitude': json_data.get('geoData', {}).get('altitude', 0),
        }
    }
    
    return metadata 