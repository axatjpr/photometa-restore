"""
Test cases for metadata processing functionality.
"""

import pytest
from pathlib import Path
from datetime import datetime, timezone
from ..utils.test_utils import get_file_timestamp, get_gps_data, format_timestamp


def test_file_organization(matched_media_dir):
    """Test that all files are in the correct location."""
    expected_files = {
        "original.jpg",
        "original-edited.jpg",
        "original_old.jpg",
        "original_geo.jpg",
        "original_template.jpg"
    }
    
    actual_files = {f.name for f in matched_media_dir.glob("*.jpg")}
    assert actual_files == expected_files, "Not all expected files are in MatchedMedia directory"


def test_timestamps(matched_media_dir, expected_timestamps):
    """Test that file timestamps are correctly set."""
    # Test files with specific timestamps
    for filename, expected_ts in expected_timestamps.items():
        file_path = matched_media_dir / filename
        actual_ts = get_file_timestamp(file_path)
        assert abs(actual_ts - expected_ts) < 86400, (  # Allow 1 day difference for timezone variations
            f"Timestamp mismatch for {filename}:\n"
            f"Expected: {format_timestamp(expected_ts)}\n"
            f"Actual: {format_timestamp(actual_ts)}"
        )
    
    # Test that current files have recent timestamps
    current_files = ["original.jpg", "original-edited.jpg", "original_geo.jpg"]
    now_ts = int(datetime.now(timezone.utc).timestamp())
    
    for filename in current_files:
        file_path = matched_media_dir / filename
        actual_ts = get_file_timestamp(file_path)
        assert abs(actual_ts - now_ts) < 3600, (  # Should be within the last hour
            f"Timestamp for {filename} is not recent:\n"
            f"Current time: {format_timestamp(now_ts)}\n"
            f"File time: {format_timestamp(actual_ts)}"
        )


def test_gps_data(matched_media_dir, expected_gps_data):
    """Test that GPS data is correctly set in EXIF."""
    # Test files with GPS data
    for filename, expected_data in expected_gps_data.items():
        file_path = matched_media_dir / filename
        actual_data = get_gps_data(file_path)
        
        assert actual_data is not None, f"No GPS data found in {filename}"
        
        for key in ["latitude", "longitude", "altitude"]:
            assert abs(actual_data[key] - expected_data[key]) < 0.0001, (
                f"GPS {key} mismatch in {filename}:\n"
                f"Expected: {expected_data[key]}\n"
                f"Actual: {actual_data[key]}"
            )
    
    # Test files without GPS data
    for filename in ["original.jpg", "original-edited.jpg", "original_old.jpg"]:
        file_path = matched_media_dir / filename
        actual_data = get_gps_data(file_path)
        assert actual_data is None, f"Unexpected GPS data found in {filename}"


def test_all_json_processed(test_dir):
    """Test that all JSON files have been processed."""
    json_files = list(test_dir.glob("*.json"))
    assert len(json_files) == 0, (
        f"Found unprocessed JSON files: {[f.name for f in json_files]}"
    ) 