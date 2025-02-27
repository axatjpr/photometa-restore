"""
Metadata utilities for photometa-restore.

This module provides functions for manipulating metadata in media files,
including EXIF data and file timestamps.
"""

import os
import time
from datetime import datetime
from fractions import Fraction
from typing import Tuple, Union, Dict, Any

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


def convert_to_degrees(value: float, loc: list) -> Tuple[int, int, float, str]:
    """Convert decimal coordinates into degrees, minutes and seconds tuple.
    
    Args:
        value: Float GPS value.
        loc: Direction list ["S", "N"] or ["W", "E"].
        
    Returns:
        Tuple of (degrees, minutes, seconds, direction).
    """
    if value < 0:
        loc_value = loc[0]
    elif value > 0:
        loc_value = loc[1]
    else:
        loc_value = ""
        
    abs_value = abs(value)
    degrees = int(abs_value)
    t1 = (abs_value - degrees) * 60
    minutes = int(t1)
    seconds = round((t1 - minutes) * 60, 5)
    
    return (degrees, minutes, seconds, loc_value)


def change_to_rational(number: Union[int, float]) -> Tuple[int, int]:
    """Convert a number to rational representation.
    
    Args:
        number: Number to convert.
        
    Returns:
        Tuple of (numerator, denominator).
    """
    f = Fraction(str(number))
    return (f.numerator, f.denominator)


def set_exif_data(filepath: str, lat: float, lng: float, altitude: float, timestamp: int) -> None:
    """Set EXIF data in an image file.
    
    Args:
        filepath: Path to the image file.
        lat: Latitude coordinate.
        lng: Longitude coordinate.
        altitude: Altitude value.
        timestamp: Unix timestamp.
    """
    try:
        exif_dict = piexif.load(filepath)
        
        # Set date/time
        date_time = datetime.fromtimestamp(timestamp).strftime("%Y:%m:%d %H:%M:%S")
        exif_dict['0th'][piexif.ImageIFD.DateTime] = date_time
        exif_dict['Exif'][piexif.ExifIFD.DateTimeOriginal] = date_time
        exif_dict['Exif'][piexif.ExifIFD.DateTimeDigitized] = date_time
        
        # Set GPS data
        lat_deg = convert_to_degrees(lat, ["S", "N"])
        lng_deg = convert_to_degrees(lng, ["W", "E"])
        
        exiv_lat = (
            change_to_rational(lat_deg[0]),
            change_to_rational(lat_deg[1]),
            change_to_rational(lat_deg[2])
        )
        
        exiv_lng = (
            change_to_rational(lng_deg[0]),
            change_to_rational(lng_deg[1]),
            change_to_rational(lng_deg[2])
        )
        
        gps_ifd = {
            piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
            piexif.GPSIFD.GPSAltitudeRef: 1,
            piexif.GPSIFD.GPSAltitude: change_to_rational(round(altitude, 2)),
            piexif.GPSIFD.GPSLatitudeRef: lat_deg[3],
            piexif.GPSIFD.GPSLatitude: exiv_lat,
            piexif.GPSIFD.GPSLongitudeRef: lng_deg[3],
            piexif.GPSIFD.GPSLongitude: exiv_lng,
        }
        
        exif_dict['GPS'] = gps_ifd
        
        # Write EXIF data to file
        exif_bytes = piexif.dump(exif_dict)
        piexif.insert(exif_bytes, filepath)
    except Exception as e:
        raise Exception(f"Error setting EXIF data: {str(e)}")


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