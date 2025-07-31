# FileOrganizer

## Overview
FileOrganizer is a powerful Python-based application designed to automate the organization of files in directories. It intelligently categorizes and moves files into appropriate subdirectories based on their type, metadata, and configurable rules. The application supports various file types including images, audio, documents, and videos, with a modern GUI interface for ease of use.

## ✨ Features
- **🗂️ Smart File Categorization:** Automatically organizes files based on type and metadata
  - Images by resolution (e.g., `Images/1920x1080/`)
  - Audio files by duration (e.g., `Audio/180s/`)
  - Documents by type (PDF, DOCX, TXT)
  - Videos by duration
- **🔍 Duplicate Detection:** Intelligent duplicate handling with hash comparison
  - Keep original
  - Overwrite existing
  - Rename with incremental suffix
- **📊 Advanced Metadata Extraction:** 
  - Image dimensions and format
  - Audio/Video duration and codec info
  - Document word count and page count
  - File size and creation date
- **🔄 Flexible Processing Options:**
  - Recursive subdirectory processing
  - Preview mode for safe operation
  - Batch processing support
- **🖥️ Modern GUI Interface:**
  - User-friendly PyQt5 interface
  - Drag-and-drop folder support
  - Real-time progress tracking
  - Preview pane for changes
- **⚡ Performance Features:**
  - Multi-threaded processing
  - Efficient file handling
  - Progress callbacks
  - Comprehensive error handling

## 🛠️ Components
- `file_handler/`: Core file processing logic
  - `file_utils.py`: Main organization engine
  - `metadata_handlers.py`: Metadata extraction for all file types
  - `file_operations.py`: Safe file operations with rollback support
- `config/`: Configuration management
  - `config_handler.py`: JSON configuration loader
  - `config.json`: Customizable rules and settings
- `event/`: File system monitoring
  - `file_organizer_event.py`: Real-time folder monitoring
- `gui/`: Graphical user interface
  - `main_window.py`: Main application window
  - `processing_thread.py`: Background processing

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Install
```bash
# Clone the repository
git clone https://github.com/merknu/FileOrganizer.git
cd FileOrganizer

# Install in development mode
pip install -e .

# Or install with all dependencies
pip install -r requirements.txt
```

### Install from Source
```bash
# Clone and install
git clone https://github.com/merknu/FileOrganizer.git
cd FileOrganizer
python setup.py install
```

## 🚀 Usage

### GUI Mode (Recommended)
```bash
# Run the graphical interface
python main.py
```

### Command Line Mode
```python
# Example usage in Python
from file_handler.file_utils import organize_files
from config.config_handler import ConfigHandler

# Load configuration
config = ConfigHandler('config/config.json').config

# Organize files in preview mode first
summary = organize_files('/path/to/folder', config, preview_mode=True)
print(f"Preview summary: {summary}")

# If satisfied, run actual organization
summary = organize_files('/path/to/folder', config, preview_mode=False)
print(f"Files organized: {summary}")
```

## ⚙️ Configuration
The `config.json` file allows customization of:

```json
{
    "file_categories": {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
        "Audio": [".mp3", ".wav", ".flac", ".m4a", ".ogg"],
        "Documents": [".pdf", ".doc", ".docx", ".txt"],
        "Video": [".mp4", ".avi", ".mov", ".mkv", ".wmv"]
    },
    "subfolders": {
        ".pdf": "PDFs",
        ".doc": "Word_Documents",
        ".docx": "Word_Documents",
        ".txt": "Text_Files"
    },
    "default_duplicate_action": "k"  // k=keep, o=overwrite, r=rename
}
```

## 🔧 Development

### Setting up Development Environment
```bash
# Clone repository
git clone https://github.com/merknu/FileOrganizer.git
cd FileOrganizer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

### Running Tests
```bash
# Run tests
pytest

# Run with coverage
pytest --cov=file_handler --cov=config --cov=event
```

### Code Quality
```bash
# Format code
black .

# Check style
flake8 .
```

## 📋 Requirements
- Python 3.8+
- PyQt5 for GUI
- Pillow for image processing
- mutagen for audio metadata
- pypdf for PDF handling
- python-docx for Word documents
- moviepy for video processing
- watchdog for file monitoring

## 🤝 Contributing
Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments
- PyQt5 for the excellent GUI framework
- The Python community for amazing libraries
- All contributors and users of FileOrganizer
