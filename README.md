# FileOrganize

## Overview
FileOrganize is a Python-based application designed to automate the organization of files in a directory. It categorizes and moves files into appropriate subdirectories based on their attributes and metadata. The application supports handling various file types, including images, audio, documents, and videos.

## Features
- **File Categorization:** Organizes files based on type and metadata (e.g., images by resolution, audio by duration).
- **Duplicate Handling:** Detects duplicates with options to keep, overwrite, or rename.
- **Metadata Extraction:** Extracts metadata such as image size, audio duration, document word count, and video duration.
- **Recursive Processing:** Capable of processing files in subdirectories.
- **Preview Mode:** Allows previewing the organization changes without actual file movement.
- **GUI Support:** Features a user-friendly graphical interface built with PyQt5.
- **Drag-and-Drop:** Enables dragging and dropping folders for processing.
- **Real-Time Progress Update:** Shows the progress of file organization in real-time.

## Components
- `file_handler/file_utils.py`: Handles file operations, including moving, duplicate handling, and metadata extraction.
- `config/config_handler.py`: Manages configuration settings.
- `event/file_organizer_event.py`: Defines event handlers for file system monitoring.
- `gui/main_window.py`: Implements the GUI's main window for user interactions and status display.

## Installation
Ensure Python is installed on your system. Clone the repository and install dependencies:

```bash
git clone https://github.com/merknu/FileOrganize.git
cd FileOrganize
pip install -r requirements.txt
```
## Usage
# Run the application with Python:
python main.py
Use the GUI to select folders and start the organization process. Options to preview changes are available.

## Configuration
Edit config.json to specify file categories, default actions for duplicates, and other preferences.

## Contributing
Contributions are welcome. Please read the contributing guidelines before submitting pull requests.

## License
This project is licensed under the MIT License - see the LICENSE file for details.
