"""
Pytest configuration and fixtures for test scenarios.
"""

import os
import shutil
import pytest
import piexif
import platform
from pathlib import Path
from datetime import datetime, timezone
from photometa_restore.processor import MediaProcessor

def _set_file_timestamp(file_path: Path, timestamp: int) -> None:
    """Set both access and modification times of a file."""
    try:
        file_path_str = str(file_path)
        # Set access and modification times
        os.utime(file_path_str, (timestamp, timestamp))
        
        # On Windows, also set creation time
        if platform.system() == 'Windows':
            from win32_setctime import setctime
            setctime(file_path_str, timestamp)
            
    except Exception as e:
        print(f"Error setting timestamp for {file_path}: {e}")

def _add_gps_to_image(image_path: Path, lat: float, lon: float, alt: float) -> None:
    """Add GPS data to an image's EXIF."""
    try:
        # Convert degrees to deg/min/sec tuple
        def decimal_to_dms(decimal_deg):
            deg = int(decimal_deg)
            min_float = (decimal_deg - deg) * 60
            min = int(min_float)
            sec = int((min_float - min) * 60 * 100)
            return ((deg, 1), (min, 1), (sec, 100))

        # Create GPS dictionary
        gps_ifd = {
            piexif.GPSIFD.GPSVersionID: (2, 2, 0, 0),
            piexif.GPSIFD.GPSLatitudeRef: 'N' if lat >= 0 else 'S',
            piexif.GPSIFD.GPSLatitude: decimal_to_dms(abs(lat)),
            piexif.GPSIFD.GPSLongitudeRef: 'E' if lon >= 0 else 'W',
            piexif.GPSIFD.GPSLongitude: decimal_to_dms(abs(lon)),
            piexif.GPSIFD.GPSAltitudeRef: 0,
            piexif.GPSIFD.GPSAltitude: (int(alt * 100), 100)
        }

        # Create EXIF dictionary
        exif_dict = {"GPS": gps_ifd}
        exif_bytes = piexif.dump(exif_dict)

        # Add EXIF to image
        piexif.insert(exif_bytes, str(image_path))
    except Exception as e:
        print(f"Error adding GPS data to {image_path}: {e}")

@pytest.fixture(scope="session", autouse=True)
def setup_test_data(tmp_path_factory):
    """Set up test data before any tests run."""
    # Create a temporary test directory
    test_root = tmp_path_factory.mktemp("test_data")
    test_dir = test_root / "test_scenarios"
    
    # Create required directories
    matched_media = test_dir / "MatchedMedia"
    edited_raw = test_dir / "EditedRaw"
    logs = test_dir / "logs"
    metadata_backups = test_dir / "metadata_backups"
    
    for directory in [matched_media, edited_raw, logs, metadata_backups]:
        directory.mkdir(parents=True, exist_ok=True)
    
    # Create test image files with sample data
    sample_image = Path("test_data/copyright-free-images-750x420.jpg")
    if not sample_image.exists():
        raise FileNotFoundError(f"Sample image not found: {sample_image}")
    
    # Copy sample image to create test files with specific timestamps
    timestamp_files = {
        "original_old.jpg": int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp()),
        "original_template.jpg": int(datetime(2021, 3, 3, tzinfo=timezone.utc).timestamp())
    }
    
    for filename, timestamp in timestamp_files.items():
        dest = matched_media / filename
        shutil.copy2(sample_image, dest)
        _set_file_timestamp(dest, timestamp)
    
    # Create files with GPS data
    gps_files = {
        "original_geo.jpg": (40.7128, -74.0060, 10.0),  # New York
        "original_template.jpg": (48.8566, 2.3522, 75.0)  # Paris
    }
    
    for filename, (lat, lon, alt) in gps_files.items():
        dest = matched_media / filename
        if not dest.exists():  # Only copy if not already created for timestamps
            shutil.copy2(sample_image, dest)
        _add_gps_to_image(dest, lat, lon, alt)
    
    # Create remaining test files
    remaining_files = ["original.jpg", "original-edited.jpg"]
    for filename in remaining_files:
        dest = matched_media / filename
        if not dest.exists():
            shutil.copy2(sample_image, dest)
    
    return test_dir

@pytest.fixture
def test_dir(setup_test_data):
    """Fixture providing the test directory path."""
    return setup_test_data

@pytest.fixture
def matched_media_dir(test_dir):
    """Fixture providing the MatchedMedia directory path."""
    return test_dir / "MatchedMedia"

@pytest.fixture
def edited_raw_dir(test_dir):
    """Fixture providing the EditedRaw directory path."""
    return test_dir / "EditedRaw"

@pytest.fixture
def processor(test_dir):
    """Fixture providing a MediaProcessor instance."""
    return MediaProcessor(str(test_dir))

@pytest.fixture
def expected_timestamps():
    """Fixture providing expected timestamps for test files."""
    return {
        "original_old.jpg": int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp()),
        "original_template.jpg": int(datetime(2021, 3, 3, tzinfo=timezone.utc).timestamp())
    }

@pytest.fixture
def expected_gps_data():
    """Fixture providing expected GPS data for test files."""
    return {
        "original_geo.jpg": {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "altitude": 10.0
        },
        "original_template.jpg": {
            "latitude": 48.8566,
            "longitude": 2.3522,
            "altitude": 75.0
        }
    } 