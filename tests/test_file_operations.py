"""
Tests for file operation utilities.
"""

import os
import shutil
import tempfile
import unittest

from photometa_restore.utils.file_operations import (
    fix_title,
    check_if_same_name,
    create_required_folders
)


class TestFileOperations(unittest.TestCase):
    """Test case for file operations."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary directory
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Tear down test environment."""
        # Remove the temporary directory
        shutil.rmtree(self.test_dir)
    
    def test_fix_title(self):
        """Test fixing incompatible characters in titles."""
        # Test with various invalid characters
        test_cases = [
            ("%file.jpg", "file.jpg"),
            ("file<1>.jpg", "file1.jpg"),
            ("file>1<.jpg", "file1.jpg"),
            ("file:1.jpg", "file1.jpg"),
            ("file?.jpg", "file.jpg"),
            ("file*.jpg", "file.jpg"),
            ("file{1}.jpg", "file1.jpg"),
            ("file\\1.jpg", "file1.jpg"),
            ("file@1.jpg", "file1.jpg"),
            ("file!1.jpg", "file1.jpg"),
            ("file+1.jpg", "file1.jpg"),
            ("file|1.jpg", "file1.jpg"),
            ("file\"1\".jpg", "file1.jpg"),
            ("file'1'.jpg", "file1.jpg"),
        ]
        
        for input_title, expected_title in test_cases:
            self.assertEqual(fix_title(input_title), expected_title)
    
    def test_check_if_same_name(self):
        """Test checking for duplicate filenames."""
        # Test with various cases
        media_moved = ["file1.jpg", "file2.jpg", "file3.jpg"]
        
        # Test case where name doesn't exist in media_moved
        result = check_if_same_name("file4.jpg", "file4.jpg", media_moved, 1)
        self.assertEqual(result, "file4.jpg")
        
        # Test case where name exists in media_moved
        result = check_if_same_name("file1.jpg", "file1.jpg", media_moved, 1)
        self.assertEqual(result, "file1(1).jpg")
        
        # Test case where name with suffix already exists in media_moved
        media_moved.append("file4(1).jpg")
        result = check_if_same_name("file4.jpg", "file4(1).jpg", media_moved, 1)
        self.assertEqual(result, "file4(2).jpg")
    
    def test_create_required_folders(self):
        """Test creating required folders."""
        matched_dir, edited_dir = create_required_folders(self.test_dir)
        
        # Check if directories were created
        self.assertTrue(os.path.exists(matched_dir))
        self.assertTrue(os.path.exists(edited_dir))
        
        # Check if directories are in the correct place
        self.assertEqual(os.path.dirname(matched_dir), self.test_dir)
        self.assertEqual(os.path.dirname(edited_dir), self.test_dir)


if __name__ == "__main__":
    unittest.main() 