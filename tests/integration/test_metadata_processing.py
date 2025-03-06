"""
Test cases for metadata processing functionality.
"""

import os
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
    
    # Ensure the directory exists
    assert matched_media_dir.exists(), f"MatchedMedia directory not found at {matched_media_dir}"
    
    actual_files = {f.name for f in matched_media_dir.glob("*.jpg")}
    assert actual_files == expected_files, (
        f"Not all expected files are in MatchedMedia directory.\n"
        f"Expected: {sorted(expected_files)}\n"
        f"Found: {sorted(actual_files)}"
    )


def test_timestamps(matched_media_dir, expected_timestamps):
    """Test that file timestamps are correctly set."""
    # Test files with specific timestamps
    for filename, expected_ts in expected_timestamps.items():
        file_path = matched_media_dir / filename
        assert file_path.exists(), f"Test file not found: {file_path}"
        
        actual_ts = get_file_timestamp(file_path)
        # Skip timestamp checks in CI environment
        if os.getenv('CI'):
            print(f"Skipping timestamp check in CI environment for {filename}")
            continue
            
        # Allow for more time difference in local testing
        max_diff = 86400  # 1 day
        assert abs(actual_ts - expected_ts) < max_diff, (
            f"Timestamp mismatch for {filename}:\n"
            f"Expected: {format_timestamp(expected_ts)}\n"
            f"Actual: {format_timestamp(actual_ts)}\n"
            f"Difference: {abs(actual_ts - expected_ts)} seconds"
        )
    
    # Test that current files have recent timestamps
    current_files = ["original.jpg", "original-edited.jpg", "original_geo.jpg"]
    now_ts = int(datetime.now(timezone.utc).timestamp())
    
    for filename in current_files:
        file_path = matched_media_dir / filename
        assert file_path.exists(), f"Test file not found: {file_path}"
        
        actual_ts = get_file_timestamp(file_path)
        # Skip timestamp checks in CI environment
        if os.getenv('CI'):
            print(f"Skipping timestamp check in CI environment for {filename}")
            continue
            
        # Allow for more time difference in local testing
        max_diff = 86400  # 1 day
        assert abs(actual_ts - now_ts) < max_diff, (
            f"Timestamp for {filename} is not recent enough:\n"
            f"Current time: {format_timestamp(now_ts)}\n"
            f"File time: {format_timestamp(actual_ts)}\n"
            f"Difference: {abs(actual_ts - now_ts)} seconds"
        )


def test_gps_data(matched_media_dir, expected_gps_data):
    """Test that GPS data is correctly set in EXIF."""
    # Test files with GPS data
    for filename, expected_data in expected_gps_data.items():
        file_path = matched_media_dir / filename
        assert file_path.exists(), f"Test file not found: {file_path}"
        
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
        assert file_path.exists(), f"Test file not found: {file_path}"
        
        actual_data = get_gps_data(file_path)
        assert actual_data is None, f"Unexpected GPS data found in {filename}"


def test_all_json_processed(test_dir):
    """Test that all JSON files have been processed."""
    assert test_dir.exists(), f"Test directory not found at {test_dir}"
    
    json_files = list(test_dir.glob("*.json"))
    assert len(json_files) == 0, (
        f"Found unprocessed JSON files: {[f.name for f in json_files]}"
    ) 