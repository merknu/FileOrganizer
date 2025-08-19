# FileOrganizer Background System

## 🚀 Overview

FileOrganizer now supports running in the background with system tray integration and Windows service capability. This allows for automated file organization without user intervention.

## 📋 Features

### System Tray Mode
- 🖥️ **System Tray Icon**: Runs minimized in system tray
- 🔔 **Real-time Notifications**: Shows processing status and results
- 🎛️ **Quick Controls**: Right-click menu for easy access
- 🎨 **Theme Support**: Dark/Light themes even in background mode
- 📊 **Performance Monitoring**: View real-time processing statistics

### Background Processing
- 📁 **Folder Monitoring**: Automatically watch specified folders
- ⚡ **Auto-organization**: Process new files as they appear
- 🧠 **Smart Detection**: Configurable file age before processing
- 🔧 **GPU Acceleration**: Full GPU support in background mode

### Windows Integration
- 🏁 **Startup Integration**: Auto-start with Windows
- 🛠️ **Windows Service**: True background service mode
- 🔐 **Registry Management**: Proper Windows startup handling
- 📝 **Event Logging**: Windows Event Log integration

## 🎯 Quick Start

### Option 1: System Tray (Recommended for Desktop Users)

```bash
# Start FileOrganizer in system tray mode
python tray_launcher.py

# Or use the Windows batch manager
fileorganizer_manager.bat
```

### Option 2: Windows Service (For Server/Always-On Systems)

```bash
# Install as Windows service (requires admin)
python service_wrapper.py install

# Start the service
python service_wrapper.py start

# Check service status
python service_wrapper.py status
```

### Option 3: Easy GUI Manager

```bash
# Launch the interactive manager
fileorganizer_manager.bat
```

## 📖 Detailed Usage

### System Tray Mode

1. **Launch**: Run `python tray_launcher.py`
2. **Configure**: Right-click tray icon → "Background Processing..."
3. **Set Folders**: Add folders to monitor for new files
4. **Start Monitoring**: Click "Start Monitoring" in settings dialog

**Tray Icon Controls:**
- **Left Click**: Toggle main window visibility
- **Double Click**: Open main FileOrganizer window
- **Right Click**: Show context menu with options

### Background Processing Settings

| Setting | Description | Default |
|---------|-------------|---------|
| **Watch Folders** | Folders to monitor for new files | None |
| **Check Interval** | How often to scan for new files (minutes) | 5 |
| **Minimum File Age** | Wait time before processing new files (seconds) | 30 |
| **Auto Process** | Automatically organize detected files | True |
| **Show Notifications** | Display system tray notifications | True |

### Windows Service Mode

**Installation:**
```bash
# Install service (requires administrator)
python service_wrapper.py install

# Create configuration file
python service_wrapper.py config

# Edit service_config.json as needed

# Start service
python service_wrapper.py start
```

**Management:**
```bash
python service_wrapper.py status      # Check status
python service_wrapper.py restart     # Restart service
python service_wrapper.py stop        # Stop service
python service_wrapper.py remove      # Uninstall service
```

### Startup Integration

**Enable startup with Windows:**
```bash
python startup_manager.py enable      # Registry method
python startup_manager.py shortcut-add # Startup folder shortcut
```

**Check startup status:**
```bash
python startup_manager.py status
```

## ⚙️ Configuration

### Service Configuration (`service_config.json`)

```json
{
  "background": {
    "watch_folders": [
      "C:/Users/Username/Downloads",
      "C:/Users/Username/Desktop"
    ],
    "check_interval": 5,
    "min_age": 30,
    "auto_process": true,
    "show_notifications": false
  },
  "gpu_config": {
    "enable_gpu": true,
    "backend": "auto",
    "memory_limit_mb": 1024,
    "fallback_to_cpu": true
  },
  "processing": {
    "max_workers": 2,
    "chunk_size_mb": 16.0,
    "recursive": true,
    "handle_duplicates": true
  }
}
```

### Tray Settings (Automatically Saved)

Settings are stored in Windows registry under:
- `HKEY_CURRENT_USER\Software\FileOrganizer\SystemTray`
- `HKEY_CURRENT_USER\Software\FileOrganizer\BackgroundProcessor`

## 🔧 Advanced Usage

### Custom Notification Handling

The system supports both Windows native notifications and custom notification widgets:

```python
# In your custom integration
from gui.system_tray import SystemTrayApp

app = SystemTrayApp(sys.argv, config)
app.show_notification("Custom Title", "Custom message", duration=5000)
```

### Integration with Other Applications

You can integrate FileOrganizer background processing with other applications:

```python
# Example: Monitor specific application output folder
from gui.system_tray import FileWatcher

config = {
    'auto_process': True,
    'check_interval': 1,  # Check every minute
    'min_age': 5  # Process files after 5 seconds
}

watcher = FileWatcher(["/path/to/application/output"], config)
watcher.file_detected.connect(your_callback)
watcher.start()
```

## 🎨 Theming in Background Mode

Even in background mode, FileOrganizer supports theming:

- **System Tray**: Themes apply to all dialogs and windows
- **Notifications**: Custom notifications respect theme settings
- **Main Window**: When opened, uses selected theme

## 📊 Monitoring and Logging

### Log Files

| File | Description | Location |
|------|-------------|----------|
| `fileorganizer_tray.log` | System tray application log | `logs/` |
| `service.log` | Windows service log | `logs/` |

### Performance Monitoring

Access real-time performance data:

1. **System Tray**: Right-click → "Show FileOrganizer" → Performance tab
2. **Command Line**: `python test_enhanced_gui.py --monitor`

### Windows Event Logs

Service mode logs to Windows Event Log under "Application" with source "FileOrganizer Service".

## 🔒 Security Considerations

### Permissions

- **System Tray Mode**: Runs with user permissions
- **Service Mode**: Runs with SYSTEM permissions (requires admin to install)
- **Startup Integration**: Modifies user registry (HKCU)

### File Access

- **Watch Folders**: Requires read access to monitored folders
- **Organization**: Requires write access to destination folders
- **GPU Processing**: May require specific GPU driver permissions

## 🐛 Troubleshooting

### Common Issues

**System tray icon not visible:**
```bash
# Check if system tray is available
python -c "from PyQt5.QtWidgets import QApplication, QSystemTrayIcon; print('Available:', QSystemTrayIcon.isSystemTrayAvailable())"
```

**Service won't install:**
- Run Command Prompt as Administrator
- Ensure `pywin32` is installed: `pip install pywin32`

**Files not being processed:**
1. Check watch folder paths in configuration
2. Verify file age settings (files may be too new)
3. Check log files for error messages

**GPU not working in background:**
- Verify GPU drivers are installed
- Check service configuration for GPU settings
- Service mode may have limited GPU access

### Diagnostic Commands

```bash
# Test all components
python test_enhanced_gui.py

# Check startup configuration
python startup_manager.py status

# Test service installation (without installing)
python service_wrapper.py config

# View current background settings
# Check Windows Registry: HKEY_CURRENT_USER\Software\FileOrganizer
```

## 🔄 Migration and Updates

### Updating FileOrganizer

1. **Stop background processes:**
   ```bash
   # Stop service if running
   python service_wrapper.py stop
   
   # Close system tray (right-click → Exit)
   ```

2. **Update files** (your new version)

3. **Restart background processes:**
   ```bash
   # Restart service
   python service_wrapper.py start
   
   # Or restart system tray
   python tray_launcher.py
   ```

### Backup Configuration

```bash
# Export registry settings
reg export "HKEY_CURRENT_USER\Software\FileOrganizer" fileorganizer_settings.reg

# Backup configuration files
copy service_config.json service_config.json.backup
```

## 🤝 Integration Examples

### Batch Processing Integration

```batch
@echo off
REM Example: Process folder then start monitoring
python -c "from file_handler.file_utils import organize_files; organize_files('C:\Downloads')"
python tray_launcher.py
```

### PowerShell Integration

```powershell
# Example: Start FileOrganizer after system startup delay
Start-Sleep -Seconds 30
Start-Process python -ArgumentList "tray_launcher.py" -WorkingDirectory "C:\FileOrganizer"
```

## 📞 Support

For issues with background operation:

1. Check log files in `logs/` directory
2. Run diagnostic: `python test_enhanced_gui.py`
3. Verify configuration files
4. Check Windows Event Log for service issues

---

**FileOrganizer v3.0 - Enhanced Background Operation**  
*Powerful file organization with seamless background integration*