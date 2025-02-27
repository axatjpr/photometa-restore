"""
GUI interface for PhotoMeta Restore.

This module provides a graphical user interface for the PhotoMeta Restore application.
"""

import os
import sys
import PySimpleGUI as sg
from typing import Optional

from .config import get_config
from .processor import process_directory
from .resources.icon import get_icon_path


def create_window() -> sg.Window:
    """Create the main application window.
    
    Returns:
        PySimpleGUI window object.
    """
    config = get_config()
    
    # Set theme for a minimalist professional look
    sg.theme('SystemDefault')
    
    # Define minimal professional color scheme
    primary_color = "#2C5282"  # Blue for accents
    text_color = "#2D3748"     # Dark gray for text
    background_color = "#FFFFFF"  # White background
    button_color = ("#FFFFFF", "#3182CE")  # White text on blue buttons
    
    # Fonts
    title_font = ('Segoe UI', 18, 'bold')
    subtitle_font = ('Segoe UI', 11)
    main_font = ('Segoe UI', 10)
    
    # Create a clean header
    header = [
        [sg.Text('PhotoMeta Restore', font=title_font, text_color=primary_color, justification='center', expand_x=True, pad=((0, 0), (15, 5)))],
        [sg.Text('Restore your Google Takeout photos metadata', font=subtitle_font, text_color=text_color, justification='center', expand_x=True, pad=((0, 0), (0, 15)))],
    ]
    
    # Input section with clean styling
    input_section = [
        [sg.Text('Edited photos suffix (optional):', font=main_font, text_color=text_color, pad=((0, 0), (10, 5)))],
        [sg.Input(key='-INPUT_TEXT-', size=(40, 1), font=main_font, pad=((0, 5), (0, 15))), 
         sg.Button('?', tooltip='Help with edited suffix', key='Help', button_color=button_color, size=(2, 1), font=main_font)],
        
        [sg.Text('Google Takeout folder:', font=main_font, text_color=text_color, pad=((0, 0), (10, 5)))],
        [sg.Input(key='-FOLDER_PATH-', size=(40, 1), font=main_font, enable_events=True, pad=((0, 5), (0, 15))), 
         sg.FolderBrowse('Browse', key='-FOLDER_BROWSE-', button_color=button_color, size=(6, 1), font=main_font)],
    ]
    
    # Action section with clean button styling
    action_section = [
        [sg.Button('Restore Metadata', key='Match', button_color=button_color, size=(15, 1), font=main_font, pad=((0, 0), (10, 20)))],
    ]
    
    # Progress section
    progress_section = [
        [sg.ProgressBar(100, orientation='h', size=(46, 15), key='-PROGRESS_BAR-', bar_color=("#3182CE", "#E2E8F0"), visible=False)],
        [sg.Text('', key='-PROGRESS_LABEL-', size=(50, 2), font=main_font, justification='center')],
    ]
    
    # Footer with version
    footer = [
        [sg.Text(f'v{config.__version__}', font=('Segoe UI', 8), text_color='gray', justification='right', expand_x=True, pad=((0, 5), (10, 0)))],
    ]
    
    # Combine all sections into the main layout
    layout = [
        *header,
        [sg.HorizontalSeparator(pad=((0, 0), (0, 20)))],
        *input_section,
        *action_section,
        *progress_section,
        *footer
    ]
    
    # Get icon path
    icon_path = get_icon_path()
    
    # Create window with a clean professional look
    return sg.Window(
        'PhotoMeta Restore', 
        layout, 
        finalize=True,
        element_justification='center',
        font=main_font,
        resizable=False,
        margins=(25, 25),
        icon=icon_path
    )


def update_progress(window: sg.Window, progress: float, success_count: int, error_count: int) -> None:
    """Update the progress bar and label.
    
    Args:
        window: PySimpleGUI window object.
        progress: Progress percentage (0-100).
        success_count: Number of successfully processed files.
        error_count: Number of files with errors.
    """
    window['-PROGRESS_LABEL-'].update(f"{progress:.1f}% - Processing files... ({success_count} successful, {error_count} errors)", visible=True)
    window['-PROGRESS_BAR-'].update(progress, visible=True)
    window.refresh()


def show_help_popup() -> None:
    """Show help information in a popup."""
    config = get_config()
    icon_path = get_icon_path()
    
    sg.popup(
        'About Edited Photos Suffix',
        'When you download photos from Google Takeout that were edited in Google Photos, two versions of each photo are included:\n\n'
        '1. The original photo (e.g., "Example.jpg")\n'
        '2. The edited version with a suffix (e.g., "Example-edited.jpg")\n\n'
        'Why this matters: The app needs to know which files are edited versions so it can:\n'
        '• Process edited files differently than originals\n'
        '• Move original versions of edited photos to a separate folder\n'
        '• Correctly match metadata to both versions\n\n'
        'The suffix varies depending on your Google account language setting:\n'
        '• English: "edited" (default)\n'
        '• Spanish: "editado"\n'
        '• French: "modifié"\n'
        '• German: "bearbeitet"\n\n'
        'If you leave this field empty, the default suffix "edited" will be used.',
        title='Understanding Edited Photo Suffix',
        font=('Segoe UI', 10),
        button_color=("#FFFFFF", "#3182CE"),
        icon=icon_path
    )


def run_gui() -> None:
    """Run the GUI application."""
    # Create window with icon
    config = get_config()
    window = create_window()
    
    # Set window icon explicitly after creation
    if icon_path := get_icon_path():
        try:
            # On Windows, set the taskbar icon
            if hasattr(window, 'TKroot'):
                from PIL import Image, ImageTk
                
                img = Image.open(icon_path)
                img = img.resize((32, 32), Image.LANCZOS)  # Resize to standard size
                photo = ImageTk.PhotoImage(img)
                window.TKroot.iconphoto(True, photo)
        except Exception as e:
            print(f"Failed to set taskbar icon: {e}")
    
    # Color constants for status messages
    success_color = "#38A169"  # Green
    error_color = "#E53E3E"    # Red
    processing_color = "#3182CE"  # Blue
    
    while True:
        event, values = window.read()
        
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
            
        elif event == 'Match':
            folder_path = values['-FOLDER_PATH-']
            edited_suffix = values['-INPUT_TEXT-']
            
            if not folder_path:
                sg.popup_error(
                    "Please select a Google Takeout folder first.",
                    font=('Segoe UI', 10),
                    title="Missing Folder",
                    button_color=("#FFFFFF", error_color),
                    icon=get_icon_path()
                )
                continue
                
            # Make progress bar visible and set initial status
            window['-PROGRESS_BAR-'].update(0, visible=True)
            window['-PROGRESS_LABEL-'].update("0% - Starting process...", text_color=processing_color, visible=True)
            
            # Process the directory
            success_count, error_count = process_directory(
                folder_path, 
                edited_suffix,
                lambda progress, success, error: update_progress(window, progress, success, error)
            )
            
            # Update final status
            success_word = "success" if success_count == 1 else "successes"
            error_word = "error" if error_count == 1 else "errors"
            
            window['-PROGRESS_BAR-'].update(100, visible=True)
            
            # Set status color based on results
            status_color = success_color if success_count > 0 and error_count == 0 else error_color
            
            status_message = config.SUCCESS_MESSAGE.format(
                success_count=success_count,
                success_word=success_word,
                error_count=error_count,
                error_word=error_word
            )
            
            if error_count > 0:
                status_message += "\nCheck logs folder for details."
                
            window['-PROGRESS_LABEL-'].update(
                status_message,
                visible=True,
                text_color=status_color
            )
            
        elif event == 'Help':
            show_help_popup()
    
    window.close()
    

if __name__ == "__main__":
    run_gui() 