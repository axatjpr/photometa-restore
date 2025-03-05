"""
Script to create test images and metadata for scenarios.

This script should be moved to tests/fixtures/create_test_images.py
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from PIL import Image

def create_base_image(path: Path, size: tuple = (800, 600)):
    """Create a base test image if it doesn't exist.
    
    Args:
        path: Path to save the image
        size: Image dimensions (width, height)
    """
    if not path.exists():
        # Create random image data
        img_array = np.random.randint(0, 256, (*size, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        
        # Save image
        img.save(str(path), format='JPEG', quality=85)
        print(f"Created base image: {path}")

def create_test_directories():
    """Create test directories if they don't exist."""
    base_dir = Path(__file__).parent
    dirs = ['EditedRaw', 'MatchedMedia', 'metadata_backups', 'logs']
    
    for dir_name in dirs:
        dir_path = base_dir / dir_name
        dir_path.mkdir(exist_ok=True)
        
    return base_dir

def create_test_image(base_dir: Path, name: str, timestamp: int, geo_data: dict = None):
    """Create a test image with metadata."""
    # Copy sample image to EditedRaw
    source_image = base_dir / 'original.jpg'
    edited_raw_dir = base_dir / 'EditedRaw'
    target_image = edited_raw_dir / f"{name}.jpg"
    
    if source_image.exists():
        shutil.copy2(str(source_image), str(target_image))
        print(f"Created image: {target_image}")
    
    # Create metadata JSON
    metadata = {
        "title": f"{name}.jpg",
        "description": f"Test image {name}",
        "photoTakenTime": {
            "timestamp": str(timestamp),
            "formatted": datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
        },
        "geoData": {
            "latitude": geo_data["latitude"] if geo_data else 0,
            "longitude": geo_data["longitude"] if geo_data else 0,
            "altitude": geo_data["altitude"] if geo_data else 0
        }
    }
    
    json_path = base_dir / f"{name}.jpg.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    print(f"Created metadata: {json_path}")

def main():
    """Create test images and metadata."""
    base_dir = create_test_directories()
    
    # Create base image if it doesn't exist
    base_image = base_dir / 'original.jpg'
    create_base_image(base_image)
    
    # Clean up existing files
    for dir_name in ['EditedRaw', 'MatchedMedia']:
        dir_path = base_dir / dir_name
        for file in dir_path.glob('*.jpg'):
            file.unlink()
    
    for json_file in base_dir.glob('*.json'):
        json_file.unlink()
    
    # Create test scenarios
    # 1. Basic image
    create_test_image(
        base_dir,
        "original",
        int(datetime.now(timezone.utc).timestamp())
    )
    
    # 2. Edited version
    create_test_image(
        base_dir,
        "original-edited",
        int(datetime.now(timezone.utc).timestamp())
    )
    
    # 3. Old timestamp
    create_test_image(
        base_dir,
        "original_old",
        int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp())
    )
    
    # 4. With geo data (New York)
    create_test_image(
        base_dir,
        "original_geo",
        int(datetime.now(timezone.utc).timestamp()),
        {
            "latitude": 40.7128,
            "longitude": -74.0060,
            "altitude": 10.0
        }
    )
    
    # 5. Template version (Paris)
    create_test_image(
        base_dir,
        "original_template",
        int(datetime(2021, 3, 3, tzinfo=timezone.utc).timestamp()),
        {
            "latitude": 48.8566,
            "longitude": 2.3522,
            "altitude": 75.0
        }
    )

if __name__ == "__main__":
    main() 