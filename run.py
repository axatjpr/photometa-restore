#!/usr/bin/env python
# Launcher script for PhotoMeta Restore.

# This script provides a simple way to launch the application
# without installing it as a package.

import sys
import os

# Add the current directory to the path so we can import the package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    from photometa_restore.__main__ import main
    main() 