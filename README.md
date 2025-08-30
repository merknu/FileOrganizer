# FileOrganizer

🎉 **STATUS: FULLY FUNCTIONAL** 🎉 
*Latest update: All critical bugs fixed, comprehensive test suite added, application is now working perfectly!*

## Overview
FileOrganizer is a powerful Python-based application designed to automate the organization of files in directories. It intelligently categorizes and moves files into appropriate subdirectories based on their type, metadata, and configurable rules. The application supports various file types including images, audio, documents, and videos, with a modern GUI interface for ease of use.

## ✨ Features
- **🗂️ Smart File Categorization:** Automatically organizes files based on type and metadata
  - Images by resolution (e.g., `Images/1920x1080/`)
  - Audio files by duration (e.g., `Audio/180s/`)
  - Documents by type (PDF, DOCX, TXT)
  - Videos by duration
- **📸 Advanced Photo Transfer Tool:** NEW! Specialized tool for selective photo transfers
  - Transfer photos from phones/cameras to external drives
  - Date range filtering for selective transfers
  - File integrity checking with size verification
  - Resume capability after interruptions
  - Automatic retry for failed transfers
  - Progress tracking with persistent todo list
  - Support for multiple file types (JPEG, PNG, RAW, Videos)
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
  - Dual-mode interface (File Organizer & Photo Transfer)
- **⚡ Performance Features:**
  - Multi-threaded processing
  - **🚀 OpenCL GPU acceleration** for file hashing (10-100x speedup)
  - Advanced duplicate detection with GPU-accelerated hash computation
  - Efficient file handling with smart memory management
  - Progress callbacks and real-time monitoring
  - Comprehensive error handling with automatic fallback
  - Automatic resume on failure

## 🛠️ Components
- `file_handler/`: Core file processing logic
  - `file_utils.py`: Main organization engine
  - `metadata_handlers.py`: Metadata extraction for all file types
  - `file_operations.py`: Safe file operations with rollback support
  - `gpu_acceleration.py`: GPU acceleration framework
  - `gpu_hasher.py`: GPU-accelerated file hashing
  - `opencl_kernels.py`: OpenCL kernel implementations
- `config/`: Configuration management
  - `config_handler.py`: JSON configuration loader
  - `config.json`: Customizable rules and settings
  - `gpu_config.json`: GPU acceleration configuration
- `event/`: File system monitoring
  - `file_organizer_event.py`: Real-time folder monitoring
- `gui/`: Graphical user interface
  - `main_window.py`: Main application window with GPU status
  - `processing_thread.py`: Background processing
  - `system_tray.py`: Background system tray operation
- `benchmarks/`: Performance testing
  - `gpu_benchmark.py`: GPU performance testing
  - `opencl_hash_benchmark.py`: Hash performance comparison

## 🚀 SUPER EASY INSTALLATION

### ONE-CLICK INSTALL (Recommended)

**Windows Users:** Double-click `START_HERE.bat` ✨  
**Linux/Mac Users:** Double-click `start_here.sh` or run `./start_here.sh` ✨

That's it! The script automatically:
- ✅ Checks Python installation
- ✅ Creates virtual environment
- ✅ Installs all dependencies
- ✅ Creates desktop shortcuts
- ✅ Launches FileOrganizer

### Alternative Easy Methods

```bash
# Interactive installer
python install.py

# Smart launcher (auto-installs missing deps)
python run.py

# Portable mode (no installation needed)
python portable.py
```

### Traditional Installation (if preferred)

**Prerequisites:**
- Python 3.8 or higher
- pip package manager

**GPU Acceleration (Optional):**
For 10-100x speedup with large files:
- OpenCL-compatible GPU (NVIDIA, AMD, Intel)
- Latest GPU drivers with OpenCL support

**Manual Install:**
```bash
# Clone the repository
git clone https://github.com/merknu/FileOrganizer.git
cd FileOrganizer

# Create virtual environment (recommended)
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# Install dependencies (note the -r flag!)
python -m pip install -r requirements.txt

# Run FileOrganizer
python main.py
```

**📖 Need help?** See [EASY_INSTALL.md](EASY_INSTALL.md) for detailed instructions and troubleshooting.

## 🚀 Usage

### GUI Mode (Recommended)
```bash
# Run the full FileOrganizer Suite
python main.py

# Run only the Photo Transfer Tool
python photo_transfer.py
# or
python main.py --transfer
```

### Photo Transfer Tool Usage
The Photo Transfer Tool is perfect for:
- Transferring photos from phones/cameras to external drives
- Selective transfer by date range (e.g., "only photos from last vacation")
- Batch processing with resume capability
- Ensuring file integrity during transfers

**Features:**
1. **Source Selection**: Browse to your phone's DCIM folder or camera's memory card
2. **Destination**: Select external drive or backup location
3. **Date Filtering**: Optional date range selection
4. **File Type Filter**: Choose specific file types (JPEG, PNG, RAW, Videos)
5. **Progress Tracking**: See real-time transfer progress
6. **Resume Capability**: If interrupted, can resume from where it stopped
7. **Integrity Check**: Verifies file sizes match after transfer
8. **Retry Logic**: Automatically retries failed transfers up to 3 times

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
