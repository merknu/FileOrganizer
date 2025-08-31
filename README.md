# FileOrganizer

🎉 **STATUS: PRODUCTION READY** 🎉 
*Latest update: System tray integration, EXE releases, and automated build pipeline!*

## 📥 Quick Download (EXE Releases)

**For Windows Users** - No Python installation required!
- [📥 Download FileOrganizer.exe](https://github.com/merknu/FileOrganizer/releases/latest) - Main application
- [📥 Download FileOrganizer_SystemTray.exe](https://github.com/merknu/FileOrganizer/releases/latest) - Background system tray version

**For Linux/macOS Users** - Native binaries available in releases!

## Overview
FileOrganizer is a comprehensive file management solution with both a traditional GUI and modern system tray interface. It automates file organization, transfers, and transcoding with intelligent categorization and robust cross-platform support. Available as standalone executables or Python source code.

## ✨ Key Features

### 🖱️ System Tray Integration (NEW!)
- **Always-available**: Runs in system tray with minimal resource usage
- **Quick Scenarios**: Right-click for instant access to common tasks:
  - 💻 Transfer All Files (Old PC → New PC)
  - 🎬 Transcode Videos to Save Space
  - 📸 Sort Photos by Date
  - 🔍 Find and Remove Duplicates
  - 📥 **Organize Downloads Folder** - Automatically sorts downloads by file type
  - 🎵 Organize Music Library
  - ☁️ Cloud Backup
  - 💾 Disk Space Analyzer

### 📥 Downloads Organizer (NEW!)
- **Automatic File Sorting**: Moves downloads to correct system folders
  - 📄 Documents → Documents/
  - 🖼️ Images → Pictures/
  - 🎬 Videos → Videos/
  - 🎵 Music → Music/
  - 📦 Archives → Documents/Archives/
  - 💻 Code → Documents/Code/
  - 📚 eBooks → Documents/eBooks/
- **Smart Folder Creation**: Creates missing folders automatically
- **Multi-User Support**: Works for any logged-in user
- **Cross-Platform**: Windows, macOS, Linux support

### 🎬 Media Transfer & Transcoding
- **Audio Transfer**: Copy and transcode audio files with metadata preservation
- **Video Transfer**: Advanced video transcoding with H.265, hardware acceleration
- **Format Conversion**: Support for 50+ audio/video formats
- **Quality Presets**: Fast, balanced, high-quality encoding options

### 🗂️ Smart File Organization
- **Intelligent Categorization**: Organizes files by type, resolution, duration
  - Images by resolution (e.g., `Images/1920x1080/`)
  - Audio files by duration (e.g., `Audio/180s/`)
  - Documents by type (PDF, DOCX, TXT)
  - Videos by duration
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

## 🛠️ Repository Structure

```
FileOrganizer/
├── src/                          # Source code
│   ├── core/                     # Core FileOrganizer functionality
│   ├── gui/                      # GUI components
│   ├── file_handler/             # File handling logic
│   ├── transfers/                # Transfer modules
│   │   ├── audio_transfer.py     # Audio transfer & transcoding
│   │   ├── video_transfer.py     # Video transfer & transcoding
│   │   └── downloads_organizer.py # Downloads folder organization
│   └── system_tray/              # System tray functionality
├── build/                        # Build and compilation files
│   ├── FileOrganizer.spec        # PyInstaller spec for main app
│   ├── FileOrganizer_SystemTray.spec # PyInstaller spec for tray
│   ├── build_exe.py              # Build script
│   └── requirements-exe.txt       # Build dependencies
├── scripts/                      # Launcher scripts
│   ├── windows/                  # Windows BAT files
│   └── unix/                     # Linux/macOS shell scripts
├── releases/                     # Release binaries
│   └── latest/                   # Latest EXE releases
├── docs/                         # Documentation
│   ├── BUILD_EXE_GUIDE.md        # Build instructions
│   └── SYSTEM_TRAY_SCENARIOS.md  # System tray scenarios guide
├── tests/                        # Test suite
├── .github/workflows/            # GitHub Actions for automated builds
└── README.md                     # This file
```

## 🚀 Installation Options

### 📥 Option 1: EXE Downloads (Easiest - No Python Required!)

**Windows:**
1. Download [FileOrganizer_SystemTray.exe](https://github.com/merknu/FileOrganizer/releases/latest)
2. Run the EXE file - that's it! 
3. Right-click the system tray icon for instant access to scenarios

**Linux/macOS:**
1. Download the appropriate binary from [releases](https://github.com/merknu/FileOrganizer/releases/latest)
2. Make executable: `chmod +x FileOrganizer-linux`
3. Run: `./FileOrganizer-linux`

### 📦 Option 2: ONE-CLICK Python Install 

**Windows Users:** Double-click `scripts/windows/START_HERE.bat` ✨  
**Linux/Mac Users:** Double-click `scripts/unix/start_here.sh` or run `./scripts/unix/start_here.sh` ✨

The script automatically:
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

### System Tray Mode (Recommended)
```bash
# For EXE users - just run the executable
./FileOrganizer_SystemTray.exe

# For Python source users
python src/system_tray/system_tray_main.py
```

### Traditional GUI Mode
```bash
# For EXE users
./FileOrganizer.exe

# For Python source users
python src/core/main.py
```

### Specific Transfer Tools
```bash
# Audio Transfer Tool
python src/transfers/launch_audio_transfer.py

# Video Transfer Tool  
python src/transfers/launch_video_transfer.py

# Downloads Organizer (standalone)
python src/transfers/downloads_organizer.py --dry-run
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
