"""
Command-line interface for PhotoMeta Restore.

This module provides a command-line interface for PhotoMeta Restore.
"""

import os
import sys
import argparse
from typing import Optional

from .config import get_config
from .processor import process_directory


def cli_progress_callback(progress: float, success_count: int, error_count: int) -> None:
    """Update progress in the console.
    
    Args:
        progress: Progress percentage (0-100).
        success_count: Number of successfully processed files.
        error_count: Number of files with errors.
    """
    # Print progress as a percentage
    sys.stdout.write(f"\rProgress: {progress:.2f}% (Success: {success_count}, Errors: {error_count})")
    sys.stdout.flush()


def run_cli() -> None:
    """Run the command-line interface."""
    config = get_config()
    
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='PhotoMeta Restore - Restore metadata from Google Takeout JSON files to their corresponding media files.'
    )
    
    parser.add_argument(
        'folder_path',
        help='Path to the folder containing the Google Takeout media files and JSON metadata'
    )
    
    parser.add_argument(
        '--edited-suffix',
        default=config.DEFAULT_EDITED_SUFFIX,
        help=f'Suffix used for edited photos (default: {config.DEFAULT_EDITED_SUFFIX})'
    )
    
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress progress output'
    )
    
    args = parser.parse_args()
    
    # Validate folder path
    if not os.path.isdir(args.folder_path):
        print(f"Error: '{args.folder_path}' is not a valid directory")
        sys.exit(1)
    
    # Process the directory
    callback = None if args.quiet else cli_progress_callback
    
    print(f"Processing directory: {args.folder_path}")
    print(f"Using edited suffix: {args.edited_suffix}")
    
    success_count, error_count = process_directory(
        args.folder_path,
        args.edited_suffix,
        callback
    )
    
    # Print final summary
    success_word = "success" if success_count == 1 else "successes"
    error_word = "error" if error_count == 1 else "errors"
    
    print("\n")
    print(
        config.SUCCESS_MESSAGE.format(
            success_count=success_count,
            success_word=success_word,
            error_count=error_count,
            error_word=error_word
        )
    )


if __name__ == "__main__":
    run_cli() 