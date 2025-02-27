"""
Setup script for PhotoMeta Restore.
"""

from setuptools import setup, find_packages
import os

# Get the version from photometa_restore/__init__.py
about = {}
with open(os.path.join("photometa_restore", "__init__.py"), "r") as f:
    exec(f.read(), about)

# Read the long description from README.md
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="photometa-restore",
    version=about["__version__"],
    author=about["__author__"],
    description="Restore metadata from Google Takeout JSON files to their corresponding media files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/axatjpr/photometa-restore",
    packages=find_packages(),
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Environment :: Console",
        "Environment :: Win32 (MS Windows)",
        "Environment :: X11 Applications",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Utilities",
    ],
    python_requires=">=3.6",
    install_requires=[
        "Pillow",
        "PySimpleGUI",
        "piexif",
        "win32-setctime",
    ],
    entry_points={
        "console_scripts": [
            "photometa-restore=photometa_restore.cli:run_cli",
        ],
        "gui_scripts": [
            "photometa-restore-gui=photometa_restore.gui:run_gui",
        ],
    },
) 