# FileOrganizer System Tray & Scenarios Guide

## Overview
FileOrganizer now includes a system tray interface with predefined scenarios for common file management tasks. This makes complex file operations as simple as right-clicking and selecting a scenario.

## System Tray Features

### 🖱️ **Always Available**
- Runs in the system tray (notification area)
- Right-click for instant access to all features
- Double-click tray icon to open scenario selection
- Background operation with minimal resource usage

### 🎯 **Quick Scenarios Menu**
Access the most common scenarios directly from the tray menu:
- 💻 Transfer All Files (Old PC → New PC)
- 🎬 Transcode Videos to Save Space  
- 📸 Sort Photos by Date
- 🔍 Find and Remove Duplicates

### 🔧 **Integrated Tools**
All your specialized tools available from one place:
- Photo Transfer with date filtering
- Audio Transfer with transcoding
- Video Transfer with format conversion
- Batch processing capabilities

## Predefined Scenarios

### 1. 💻 **PC Migration** (`pc_migration`)
**Purpose**: Transfer all personal files from old computer to new computer
**What it does**:
- Scans common folders (Documents, Pictures, Videos, Music, Desktop)
- Analyzes for duplicates and organization opportunities
- Transfers files while preserving folder structure
- Verifies transfer integrity with checksums
- Creates organized backup structure

**Settings**:
- Auto-organize files during transfer
- Skip system/temporary files
- Create backup before transfer
- Verify with checksums

### 2. 🎬 **Video Space Saver** (`video_space_saver`)
**Purpose**: Convert large video files to save disk space
**What it does**:
- Scans for large video files (>100MB)
- Analyzes codecs and estimates space savings
- Converts to efficient H.265 format
- Preserves quality while reducing size
- Can save 30-70% disk space

**Settings**:
- Target codec (H.265 recommended)
- Quality level (high/balanced/fast)
- Keep original files (safety option)
- Hardware acceleration support

### 3. 🎵 **Music Library Organizer** (`audio_library_organize`)
**Purpose**: Sort and organize music files by metadata
**What it does**:
- Scans for audio files (MP3, FLAC, M4A, etc.)
- Reads metadata (artist, album, genre, year)
- Organizes into folder structure: `Artist/Album/Track - Title`
- Removes duplicates based on audio fingerprinting
- Fixes missing or incorrect metadata

**Settings**:
- Folder structure pattern
- Fix metadata automatically
- Remove duplicate songs
- Normalize file/folder names

### 4. 📸 **Photo Date Sorter** (`photo_date_sort`)
**Purpose**: Organize photos into folders by date taken
**What it does**:
- Scans for image files (JPG, PNG, RAW, etc.)
- Reads EXIF date information
- Creates folder structure: `Year/Month/Date`
- Handles photos without EXIF data
- Identifies and handles duplicates

**Settings**:
- Date format (YYYY/MM or YYYY/MM/DD)
- Use EXIF date vs file date
- Handle duplicates (rename/skip/move)
- Process RAW files

### 5. 🔍 **Duplicate Cleanup** (`duplicate_cleanup`)
**Purpose**: Find and safely remove duplicate files
**What it does**:
- Scans entire system or selected folders
- Compares files by content hash (not just name)
- Groups identical files together
- Safely moves duplicates to review folder
- Provides detailed duplicate report

**Settings**:
- Comparison method (hash vs size+name)
- Minimum file size to check
- Safety mode (move vs delete)
- Backup before deletion

### 6. ☁️ **Cloud Backup** (`cloud_backup`)
**Purpose**: Backup important files to cloud storage
**What it does**:
- Scans Documents and Pictures folders
- Compresses files for efficient upload
- Encrypts sensitive backups
- Supports incremental backups
- Verifies upload integrity

**Settings**:
- Cloud provider (auto-detect)
- Compression level
- Encryption enabled
- Incremental vs full backup

### 7. 📥 **Downloads Organizer** (`downloads_organizer`)
**Purpose**: Move downloads to appropriate system folders (Documents, Pictures, Videos, Music)
**What it does**:
- Scans Downloads folder for all file types
- Automatically categorizes files by extension
- Moves files to correct system folders:
  - Documents → Documents folder
  - Images → Pictures folder  
  - Videos → Videos folder
  - Music → Music folder
  - Archives → Documents/Archives
  - Code files → Documents/Code
  - eBooks → Documents/eBooks
  - Fonts → Documents/Fonts
- Handles filename conflicts by renaming
- Creates subfolders as needed

**File Categories & Destinations**:
- **📄 Documents** (PDF, DOC, XLS, PPT, TXT) → Documents/
- **🖼️ Images** (JPG, PNG, GIF, SVG, RAW) → Pictures/
- **🎬 Videos** (MP4, AVI, MKV, MOV, WebM) → Videos/
- **🎵 Music** (MP3, FLAC, WAV, AAC, OGG) → Music/
- **📦 Archives** (ZIP, RAR, 7Z, TAR.GZ) → Documents/Archives/
- **💻 Code** (PY, JS, HTML, CSS, JSON) → Documents/Code/
- **📚 eBooks** (EPUB, MOBI, AZW) → Documents/eBooks/
- **🔤 Fonts** (TTF, OTF, WOFF) → Documents/Fonts/
- **⚙️ Software** (EXE, MSI, DMG, APP) → Downloads/Software/ (stays in Downloads)

**Settings**:
- Recent files only (organize just recent downloads)
- Dry run mode (preview what will be moved)
- Handle duplicates (rename, skip, or replace)
- Enable/disable specific categories
- Exclude file patterns (temporary files, etc.)

### 8. 💾 **Disk Space Analyzer** (`disk_space_analyzer`)
**Purpose**: Find what's consuming your disk space
**What it does**:
- Scans all drives or selected folders
- Identifies largest files and folders
- Creates interactive size report
- Provides cleanup recommendations
- Highlights space-wasting files

**Settings**:
- Minimum file size to report
- Include system files
- Include hidden files
- Sort by size vs count

## How to Use

### From System Tray
1. **Right-click** the FileOrganizer tray icon
2. **Quick Scenarios** → Select your scenario
3. **Automatic execution** with default settings
4. **Progress notifications** in system tray
5. **Completion notification** with results

### Custom Configuration
1. **Right-click** tray icon
2. **Custom Scenario...** → Opens scenario dialog
3. **Choose scenario** from categorized list
4. **Configure settings** for your specific needs
5. **Run Scenario** → Execute with custom settings

### Advanced Usage
- **Double-click** tray icon for full scenario selection dialog
- **Middle-click** tray icon to open main FileOrganizer window
- **Tools menu** for individual transfer tools
- **Settings** for tray behavior and scenario defaults

## Installation & Setup

### System Requirements
- Windows 10/11, macOS 10.14+, or Linux
- 2GB RAM (4GB recommended)
- 500MB free disk space
- System tray/notification area support

### Installation Steps
1. Download `FileOrganizer_SystemTray.exe`
2. Run installer or extract portable version
3. Launch will automatically start in system tray
4. Right-click tray icon to access scenarios

### Auto-start Configuration
- **Windows**: Automatically added to startup folder
- **macOS**: Login items configuration
- **Linux**: Desktop environment autostart

### First Run Setup
1. **Welcome dialog** explains tray functionality
2. **Permission check** for file access
3. **FFmpeg detection** for video transcoding
4. **Quick scenario test** (optional)

## Scenario Execution

### Execution Flow
1. **Scenario Selection** → Choose predefined or custom
2. **Settings Review** → Verify or modify settings
3. **File Scanning** → Find files matching criteria
4. **Analysis Phase** → Analyze files and estimate actions
5. **User Confirmation** → Review what will be done
6. **Execution** → Perform file operations
7. **Progress Updates** → Real-time status in tray
8. **Completion Report** → Summary of actions taken

### Progress Tracking
- **System tray tooltip** shows current step
- **Progress notifications** for major milestones
- **Detailed log** available on demand
- **Pause/Cancel** available during execution
- **Error handling** with user-friendly messages

### Safety Features
- **Backup before modification** (configurable)
- **Undo capability** for organization changes
- **Dry run mode** to preview actions
- **Safety confirmations** for destructive operations
- **Detailed logging** for troubleshooting

## Custom Scenarios

### Creating Custom Scenarios
1. **Base Template** → Start with similar predefined scenario
2. **Modify Steps** → Add, remove, or modify steps
3. **Configure Settings** → Set default parameters
4. **Test Execution** → Run on small sample
5. **Save & Share** → Export for reuse

### Scenario Structure
```json
{
  "name": "My Custom Scenario",
  "description": "Description of what this does",
  "icon": "🔧",
  "category": "custom",
  "steps": [
    {"type": "scan", "source": "~/Documents", "recursive": true},
    {"type": "analyze", "duplicates": true},
    {"type": "organize", "pattern": "{FileType}/{Year}"}
  ],
  "settings": {
    "backup_before": true,
    "confirm_actions": true
  }
}
```

### Step Types
- **scan**: Find files matching criteria
- **analyze**: Examine files for patterns
- **transfer**: Move/copy files
- **transcode**: Convert media files
- **organize**: Restructure file layout
- **cleanup**: Remove unnecessary files
- **backup**: Create safety copies
- **report**: Generate analysis reports

## Command Line Interface

### CLI Access
Even with system tray focus, CLI access is available:

```bash
# Run specific scenario
FileOrganizer.exe --scenario=pc_migration --auto

# List available scenarios
FileOrganizer.exe --list-scenarios

# Run with custom settings
FileOrganizer.exe --scenario=video_space_saver --settings=config.json

# Tray mode (default)
FileOrganizer.exe --tray
```

## Troubleshooting

### Common Issues

#### System Tray Not Visible
- Check system tray settings
- Enable "Show all icons" in tray settings
- Restart FileOrganizer

#### Scenario Fails to Start
- Check file permissions
- Verify source/destination paths exist
- Review scenario settings
- Check available disk space

#### Video Transcoding Not Working
- Install ffmpeg (download instructions provided)
- Check ffmpeg PATH environment variable
- Verify video file not in use
- Try different video format

#### Performance Issues
- Close other applications during large operations
- Use SSD for better performance
- Increase virtual memory if needed
- Run scenarios during off-hours

### Getting Help
- **Built-in Help**: Right-click tray → About
- **Logs Location**: `%APPDATA%/FileOrganizer/logs/`
- **Settings Reset**: Delete `%APPDATA%/FileOrganizer/config/`
- **Debug Mode**: Launch with `--debug` flag

## Performance & Resource Usage

### System Impact
- **Idle**: <10MB RAM, 0% CPU
- **Scanning**: Moderate I/O, low CPU
- **Processing**: High I/O, moderate CPU
- **Transcoding**: High CPU, moderate I/O

### Optimization Tips
- **Run overnight** for large operations
- **Use SSD** for source and destination
- **Close other applications** during processing
- **Enable hardware acceleration** for video
- **Exclude antivirus scanning** on work folders

## Future Enhancements

### Planned Features
- **Cloud integration** (Google Drive, OneDrive, Dropbox)
- **Network scenarios** (sync between computers)
- **Scheduled execution** (run scenarios on schedule)
- **AI-powered organization** (smart file categorization)
- **Collaborative scenarios** (shared team workflows)

### Community Features
- **Scenario sharing** (import/export community scenarios)
- **Plugin system** (custom step types)
- **Template marketplace** (download pre-made scenarios)
- **Usage analytics** (improve scenarios based on usage)

This system tray approach transforms FileOrganizer from a manual tool into an intelligent, always-available assistant that can handle complex file management tasks with just a few clicks.