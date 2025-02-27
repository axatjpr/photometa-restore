"""
Main entry point for PhotoMeta Restore.

This module serves as the main entry point for the application,
supporting both GUI and CLI modes.
"""

import sys
import os


def main():
    """Run the application, choosing between GUI and CLI mode."""
    # Default to GUI mode
    gui_mode = True
    
    # Check for CLI arguments
    if len(sys.argv) > 1:
        gui_mode = False
    
    if gui_mode:
        from .gui import run_gui
        run_gui()
    else:
        from .cli import run_cli
        run_cli()


if __name__ == "__main__":
    main() 