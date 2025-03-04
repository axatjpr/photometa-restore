"""
Main entry point for PhotoMeta Restore.

This module serves as the main entry point for the application,
supporting both GUI and CLI modes.
"""

import sys
from .cli import cli
from .gui import run_gui

def main():
    """Run the application in either GUI or CLI mode."""
    if len(sys.argv) > 1:
        # If arguments are provided, run in CLI mode
        cli()
    else:
        # No arguments, run in GUI mode
        run_gui()

if __name__ == "__main__":
    main() 