# PhotoMeta Restore

A powerful tool to restore metadata from Google Takeout JSON files to their corresponding media files.

## Overview

When you download your photos from Google Photos using Google Takeout, the metadata (like date taken and geo-location) is separated from the actual media files and stored in accompanying JSON files. PhotoMeta Restore helps match that metadata back to your media files, ensuring your photos retain all their important information.

## Features

- Restore creation and modification dates to photos and videos
- Add EXIF metadata (including location data) to supported image formats
- Handle edited photos (with different suffixes based on your language)
- Organize files into structured folders
- Generate detailed logs of missing files and errors
- Support both GUI and command-line interfaces

## Installation

### Prerequisites

- Python 3.6 or newer
- Windows operating system (for full timestamp functionality)

### From Source (Currently Only Available Method)

```bash
git clone https://github.com/axatjpr/photometa-restore.git
cd photometa-restore
pip install -e .
```

## Usage

### Graphical Interface

You can launch the GUI by running:

```bash
photometa-restore-gui
```

Or if installed from source without pip:

```bash
python run.py
```

1. Enter the suffix used for edited photos (default is "edited")
2. Select the folder where your Google Takeout files are located
3. Click "Restore Metadata" to begin the process

### Command Line

```bash
photometa-restore /path/to/google/takeout/folder --edited-suffix=edited
```

#### Command-line options:

- `--edited-suffix`: Specify the suffix used for edited photos (default: "edited")
- `--quiet`: Suppress progress output

## How It Works

1. The tool scans the specified directory for JSON files created by Google Takeout
2. For each JSON file, it:
   - Looks for the corresponding media file
   - Sets the correct creation and modification dates
   - Adds GPS coordinates and other metadata through EXIF (for supported formats)
   - Moves the processed file to a "MatchedMedia" folder
   - Moves original versions of edited files to an "EditedRaw" folder
3. Generates logs of any missing files or errors

## Folder Structure

After processing, you'll have:

- `MatchedMedia/`: Contains all processed media files with restored metadata
- `EditedRaw/`: Contains original versions of edited files
- `logs/`: Contains detailed logs of the process

## Troubleshooting

### Missing Files

If files are reported as missing, check:
- The filename in the JSON matches the actual file
- Special characters in filenames might cause issues
- Check the missing_files log for a complete list

### Permission Errors

If you encounter permission errors:
- Ensure files aren't open in another program
- Try running as administrator
- Check the errors log for specific details

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

We welcome contributions to PhotoMeta Restore! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to submit changes and recommendations.

When contributing to this repository, please first discuss the change you wish to make via issue,
email, or any other method with the owners of this repository before making a change.

Please note we have a [Code of Conduct](CODE_OF_CONDUCT.md), please follow it in all your interactions with the project.

### Reporting Issues

- Use the [bug report](.github/ISSUE_TEMPLATE/bug_report.md) template for reporting problems
- Use the [feature request](.github/ISSUE_TEMPLATE/feature_request.md) template for suggesting enhancements

## Customization

### Themes
The application uses a professional minimalist theme by default. You can change the theme by modifying the `UI_COLORS` dictionary in `photometa_restore/config.py`.

### Application Icon
To customize the application icon:
1. Create a PNG image file with your desired icon
2. Save it as `app_icon.png` in the `photometa_restore/resources/icons/` folder
3. The recommended size is 32x32 or 64x64 pixels with a transparent background 