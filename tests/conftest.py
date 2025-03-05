"""
Pytest configuration and fixtures for test scenarios.
"""

import os
import pytest
from pathlib import Path
from datetime import datetime, timezone
from photometa_restore.processor import MediaProcessor

@pytest.fixture
def test_dir():
    """Fixture providing the test directory path."""
    return Path("test_data/test_scenarios").resolve()

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