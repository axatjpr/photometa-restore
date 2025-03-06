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
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Environment :: Win32 (MS Windows)",
        "Environment :: X11 Applications",
        "Topic :: Multimedia :: Graphics",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=[
        "Pillow>=10.0.0",
        "PySimpleGUI>=4.60.0",
        "piexif>=1.1.3",
        "win32-setctime>=1.1.0",
        "exif>=1.6.0",
        "click>=8.0.0",
        "tqdm>=4.65.0",
        "pathlib>=1.0.1",
        "psutil>=5.9.0",
    ],
    extras_require={
        "dev": [
            "black>=23.0.0",
            "isort>=5.12.0",
            "flake8>=6.0.0",
            "mypy>=1.0.0",
        ],
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "photometa-restore=photometa_restore.cli:run_cli",
        ],
        "gui_scripts": [
            "photometa-restore-gui=photometa_restore.gui:run_gui",
        ],
    },
) 