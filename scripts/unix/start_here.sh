#!/bin/bash
# FileOrganizer - Complete One-Stop Launcher for Linux/macOS
# This script handles EVERYTHING: installation, fixes, and launching
# No other files needed - just run this one script!

set -e  # Exit on any error

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}[FileOrganizer]${NC} ${message}"
}

print_header() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BOLD}   FileOrganizer - Complete Setup & Launch${NC}"
    echo -e "${BLUE}============================================${NC}\n"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install Python on various systems
install_python() {
    print_status $YELLOW "Installing Python..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            brew install python3
        else
            print_status $RED "Please install Homebrew first: https://brew.sh"
            print_status $YELLOW "Or download Python from: https://www.python.org/downloads/"
            exit 1
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command_exists apt; then
            sudo apt update && sudo apt install python3 python3-pip python3-venv python3-tk -y
        elif command_exists yum; then
            sudo yum install python3 python3-pip python3-tkinter -y
        elif command_exists pacman; then
            sudo pacman -S python python-pip tk
        elif command_exists dnf; then
            sudo dnf install python3 python3-pip python3-tkinter -y
        else
            print_status $RED "Unsupported Linux distribution. Please install Python 3.8+ manually."
            exit 1
        fi
    else
        print_status $RED "Unsupported operating system: $OSTYPE"
        exit 1
    fi
}

# Setup virtual environment and dependencies
setup_environment() {
    print_status $BLUE "Setting up Python environment..."
    
    # Remove old venv if it exists and has issues
    if [ -d "venv" ]; then
        if ! source venv/bin/activate 2>/dev/null; then
            print_status $YELLOW "Removing corrupted virtual environment..."
            rm -rf venv
        else
            deactivate 2>/dev/null || true
        fi
    fi
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status $BLUE "Creating virtual environment..."
        python3 -m venv venv
        print_status $GREEN "Virtual environment created"
    fi
    
    # Activate virtual environment
    print_status $BLUE "Activating virtual environment..."
    source venv/bin/activate
    
    # Upgrade pip
    print_status $BLUE "Upgrading pip..."
    python -m pip install --upgrade pip
    
    # Install core dependencies one by one with error handling
    print_status $BLUE "Installing core dependencies..."
    
    # Core GUI dependency
    if ! python -c "import PyQt5" 2>/dev/null; then
        print_status $BLUE "Installing PyQt5 (GUI framework)..."
        if ! pip install "PyQt5>=5.15.0"; then
            print_status $YELLOW "PyQt5 failed, trying alternative GUI..."
            # Try tkinter fallback (usually pre-installed)
            python -c "import tkinter" 2>/dev/null || {
                print_status $RED "No GUI framework available. Installing tkinter support..."
                if [[ "$OSTYPE" == "linux-gnu"* ]]; then
                    if command_exists apt; then
                        sudo apt install python3-tk -y
                    fi
                fi
            }
        fi
    fi
    
    # Essential file processing libraries
    local core_deps=("watchdog>=2.1.0" "Pillow>=10.0.0" "mutagen>=1.46.0")
    for dep in "${core_deps[@]}"; do
        pkg_name=$(echo $dep | cut -d'>' -f1)
        if ! python -c "import ${pkg_name,,}" 2>/dev/null; then
            print_status $BLUE "Installing $pkg_name..."
            pip install "$dep" || print_status $YELLOW "$pkg_name failed (optional)"
        fi
    done
    
    # Optional but useful dependencies
    local optional_deps=("pypdf>=3.17.0" "python-docx>=0.8.11" "python-magic>=0.4.27")
    for dep in "${optional_deps[@]}"; do
        pkg_name=$(echo $dep | cut -d'>' -f1)
        print_status $BLUE "Installing $pkg_name (optional)..."
        pip install "$dep" 2>/dev/null || print_status $YELLOW "$pkg_name skipped (optional)"
    done
    
    # Try to install moviepy for video support
    print_status $BLUE "Installing video support (moviepy)..."
    pip install "moviepy>=1.0.3" 2>/dev/null || print_status $YELLOW "Video support skipped (optional)"
    
    print_status $GREEN "Dependencies installed successfully!"
}

# Create default configuration
create_config() {
    if [ ! -f "config/config.json" ]; then
        print_status $BLUE "Creating default configuration..."
        mkdir -p config
        cat > config/config.json << 'EOF'
{
    "file_categories": {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp", ".raw", ".cr2", ".nef", ".arw"],
        "Audio": [".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac", ".wma"],
        "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".pages", ".epub"],
        "Video": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm", ".m4v", ".3gp"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"],
        "Code": [".py", ".js", ".html", ".css", ".json", ".xml", ".sql", ".sh", ".bat"]
    },
    "subfolders": {
        ".pdf": "PDFs",
        ".doc": "Word_Documents", 
        ".docx": "Word_Documents",
        ".txt": "Text_Files",
        ".py": "Python_Scripts",
        ".js": "JavaScript_Files"
    },
    "default_duplicate_action": "k",
    "enable_gpu": false,
    "max_workers": 4,
    "create_year_subfolders": true,
    "organize_by_date": false
}
EOF
        print_status $GREEN "Configuration created"
    fi
}

# Create a working GUI launcher
create_working_gui() {
    cat > working_gui.py << 'EOF'
#!/usr/bin/env python3
"""
FileOrganizer - Bulletproof GUI Launcher
This GUI works with any available GUI framework and handles all errors gracefully.
"""

import os
import sys
import json
from pathlib import Path

# Try different GUI frameworks
GUI_AVAILABLE = False
GUI_TYPE = None

# Try PyQt5 first
try:
    from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                                QLabel, QPushButton, QFileDialog, QTextEdit, 
                                QMessageBox, QProgressBar, QHBoxLayout, QGroupBox)
    from PyQt5.QtCore import Qt, QThread, pyqtSignal
    from PyQt5.QtGui import QFont
    GUI_AVAILABLE = True
    GUI_TYPE = "PyQt5"
except ImportError:
    pass

# Fallback to tkinter
if not GUI_AVAILABLE:
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox, scrolledtext
        GUI_AVAILABLE = True
        GUI_TYPE = "tkinter"
    except ImportError:
        pass

class FileOrganizerGUI:
    def __init__(self):
        self.selected_folder = None
        self.setup_gui()
        
    def setup_gui(self):
        if GUI_TYPE == "PyQt5":
            self.setup_pyqt5_gui()
        elif GUI_TYPE == "tkinter":
            self.setup_tkinter_gui()
        else:
            print("No GUI framework available. Please install PyQt5 or ensure tkinter is available.")
            return False
        return True
            
    def setup_pyqt5_gui(self):
        """Setup PyQt5 interface"""
        self.app = QApplication(sys.argv)
        self.window = QMainWindow()
        self.window.setWindowTitle("FileOrganizer - Smart File Organization")
        self.window.setGeometry(100, 100, 900, 700)
        
        central_widget = QWidget()
        self.window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Header
        header = QLabel("🗂️ FileOrganizer - Smart File Organization")
        header.setStyleSheet("font-size: 20px; font-weight: bold; margin: 15px; color: #2c3e50;")
        header.setAlignment(Qt.AlignCenter)
        layout.addWidget(header)
        
        # Folder selection group
        folder_group = QGroupBox("Select Folder to Organize")
        folder_layout = QVBoxLayout()
        
        self.folder_label = QLabel("No folder selected")
        self.folder_label.setStyleSheet("padding: 10px; background: #ecf0f1; border-radius: 5px; margin: 5px;")
        folder_layout.addWidget(self.folder_label)
        
        browse_btn = QPushButton("📁 Browse for Folder")
        browse_btn.setStyleSheet("padding: 10px; font-size: 14px; background: #3498db; color: white; border-radius: 5px;")
        browse_btn.clicked.connect(self.browse_folder_pyqt)
        folder_layout.addWidget(browse_btn)
        
        folder_group.setLayout(folder_layout)
        layout.addWidget(folder_group)
        
        # Action buttons group
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()
        
        preview_btn = QPushButton("🔍 Preview Organization (Safe)")
        preview_btn.setStyleSheet("padding: 12px; font-size: 14px; background: #f39c12; color: white; border-radius: 5px; margin: 3px;")
        preview_btn.clicked.connect(self.preview_organization_pyqt)
        actions_layout.addWidget(preview_btn)
        
        organize_btn = QPushButton("🗂️ Organize Files")
        organize_btn.setStyleSheet("padding: 12px; font-size: 14px; background: #27ae60; color: white; border-radius: 5px; margin: 3px;")
        organize_btn.clicked.connect(self.organize_files_pyqt)
        actions_layout.addWidget(organize_btn)
        
        photo_btn = QPushButton("📸 Launch Photo Transfer Tool")
        photo_btn.setStyleSheet("padding: 12px; font-size: 14px; background: #9b59b6; color: white; border-radius: 5px; margin: 3px;")
        photo_btn.clicked.connect(self.launch_photo_transfer_pyqt)
        actions_layout.addWidget(photo_btn)
        
        audio_btn = QPushButton("🎵 Launch Audio Transfer Tool")
        audio_btn.setStyleSheet("padding: 12px; font-size: 14px; background: #e67e22; color: white; border-radius: 5px; margin: 3px;")
        audio_btn.clicked.connect(self.launch_audio_transfer_pyqt)
        actions_layout.addWidget(audio_btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)
        
        # Log area
        log_group = QGroupBox("Activity Log")
        log_layout = QVBoxLayout()
        
        self.log_area = QTextEdit()
        self.log_area.setMaximumHeight(200)
        self.log_area.setStyleSheet("background: #2c3e50; color: #ecf0f1; font-family: monospace;")
        log_layout.addWidget(self.log_area)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Status
        self.status_label = QLabel("Ready to organize files")
        self.status_label.setStyleSheet("padding: 8px; background: #34495e; color: white; border-radius: 3px;")
        layout.addWidget(self.status_label)
        
        self.log("FileOrganizer started successfully!")
        self.log("Select a folder and preview changes before organizing.")
        
    def setup_tkinter_gui(self):
        """Setup tkinter interface as fallback"""
        self.root = tk.Tk()
        self.root.title("FileOrganizer - Smart File Organization")
        self.root.geometry("800x600")
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Header
        header_label = ttk.Label(main_frame, text="🗂️ FileOrganizer - Smart File Organization", 
                               font=("Arial", 16, "bold"))
        header_label.grid(row=0, column=0, columnspan=3, pady=20)
        
        # Folder selection
        ttk.Label(main_frame, text="Select Folder to Organize:", font=("Arial", 12)).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.folder_var = tk.StringVar(value="No folder selected")
        self.folder_label = ttk.Label(main_frame, textvariable=self.folder_var, 
                                    relief="sunken", padding="10")
        self.folder_label.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)
        
        browse_btn = ttk.Button(main_frame, text="📁 Browse for Folder", 
                              command=self.browse_folder_tk)
        browse_btn.grid(row=3, column=0, pady=10)
        
        # Action buttons
        ttk.Label(main_frame, text="Actions:", font=("Arial", 12)).grid(row=4, column=0, sticky=tk.W, pady=(20,5))
        
        preview_btn = ttk.Button(main_frame, text="🔍 Preview Organization (Safe)", 
                               command=self.preview_organization_tk)
        preview_btn.grid(row=5, column=0, pady=5, sticky=(tk.W, tk.E))
        
        organize_btn = ttk.Button(main_frame, text="🗂️ Organize Files", 
                                command=self.organize_files_tk)
        organize_btn.grid(row=6, column=0, pady=5, sticky=(tk.W, tk.E))
        
        photo_btn = ttk.Button(main_frame, text="📸 Launch Photo Transfer Tool", 
                             command=self.launch_photo_transfer_tk)
        photo_btn.grid(row=7, column=0, pady=5, sticky=(tk.W, tk.E))
        
        audio_btn = ttk.Button(main_frame, text="🎵 Launch Audio Transfer Tool", 
                             command=self.launch_audio_transfer_tk)
        audio_btn.grid(row=8, column=0, pady=5, sticky=(tk.W, tk.E))
        
        # Log area
        ttk.Label(main_frame, text="Activity Log:", font=("Arial", 12)).grid(row=9, column=0, sticky=tk.W, pady=(20,5))
        
        self.log_text = scrolledtext.ScrolledText(main_frame, height=12, width=80)
        self.log_text.grid(row=10, column=0, columnspan=3, pady=5, sticky=(tk.W, tk.E))
        
        # Status
        self.status_var = tk.StringVar(value="Ready to organize files")
        status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                               relief="sunken", padding="5")
        status_label.grid(row=10, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(9, weight=1)
        
        self.log("FileOrganizer started successfully!")
        self.log("Select a folder and preview changes before organizing.")
        
    def log(self, message):
        """Add message to log"""
        timestamp = self.get_timestamp()
        log_entry = f"[{timestamp}] {message}"
        
        if GUI_TYPE == "PyQt5":
            self.log_area.append(log_entry)
        elif GUI_TYPE == "tkinter":
            self.log_text.insert(tk.END, log_entry + "\n")
            self.log_text.see(tk.END)
        else:
            print(log_entry)
            
    def get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().strftime("%H:%M:%S")
    
    def get_config(self):
        """Load configuration with fallback defaults"""
        config_path = Path("config/config.json")
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.log(f"Config file error: {e}, using defaults")
        
        # Default config
        return {
            "file_categories": {
                "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"],
                "Audio": [".mp3", ".wav", ".flac", ".m4a", ".ogg"],
                "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf"],
                "Video": [".mp4", ".avi", ".mov", ".mkv", ".wmv"]
            },
            "default_duplicate_action": "k"
        }
    
    # PyQt5 event handlers
    def browse_folder_pyqt(self):
        folder = QFileDialog.getExistingDirectory(self.window, "Select Folder to Organize")
        if folder:
            self.selected_folder = folder
            self.folder_label.setText(f"Selected: {folder}")
            self.log(f"Selected folder: {folder}")
            
    def preview_organization_pyqt(self):
        self.run_organization(preview=True, gui_type="PyQt5")
        
    def organize_files_pyqt(self):
        reply = QMessageBox.question(self.window, 'Confirm', 
                                   'This will move files. Continue?',
                                   QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.run_organization(preview=False, gui_type="PyQt5")
            
    def launch_photo_transfer_pyqt(self):
        self.launch_photo_transfer()
        
    def launch_audio_transfer_pyqt(self):
        self.launch_audio_transfer()
    
    # Tkinter event handlers
    def browse_folder_tk(self):
        folder = filedialog.askdirectory(title="Select Folder to Organize")
        if folder:
            self.selected_folder = folder
            self.folder_var.set(f"Selected: {folder}")
            self.log(f"Selected folder: {folder}")
            
    def preview_organization_tk(self):
        self.run_organization(preview=True, gui_type="tkinter")
        
    def organize_files_tk(self):
        if messagebox.askyesno("Confirm", "This will move files. Continue?"):
            self.run_organization(preview=False, gui_type="tkinter")
            
    def launch_photo_transfer_tk(self):
        self.launch_photo_transfer()
        
    def launch_audio_transfer_tk(self):
        self.launch_audio_transfer()
    
    def run_organization(self, preview=True, gui_type=None):
        """Run file organization with error handling"""
        if not self.selected_folder:
            if gui_type == "PyQt5":
                QMessageBox.warning(self.window, "Warning", "Please select a folder first")
            elif gui_type == "tkinter":
                messagebox.showwarning("Warning", "Please select a folder first")
            return
            
        try:
            action = "Previewing" if preview else "Organizing"
            self.log(f"{action} files...")
            
            if GUI_TYPE == "PyQt5":
                self.status_label.setText(f"{action}...")
                self.progress.setVisible(True)
                self.progress.setRange(0, 0)  # Indeterminate progress
            elif GUI_TYPE == "tkinter":
                self.status_var.set(f"{action}...")
                
            # Import file organization
            try:
                from file_handler.file_utils import organize_files
            except ImportError:
                # Fallback to basic file organization
                self.log("Using basic file organization...")
                result = self.basic_file_organization(self.selected_folder, preview)
            else:
                config = self.get_config()
                result = organize_files(self.selected_folder, config, preview_mode=preview)
            
            self.log(f"{action} completed: {result}")
            
            if GUI_TYPE == "PyQt5":
                self.status_label.setText(f"{action} completed")
                self.progress.setVisible(False)
                QMessageBox.information(self.window, "Success", f"{action} completed!\n\nResult: {result}")
            elif GUI_TYPE == "tkinter":
                self.status_var.set(f"{action} completed")
                messagebox.showinfo("Success", f"{action} completed!\n\nResult: {result}")
                
        except Exception as e:
            error_msg = f"{action} failed: {str(e)}"
            self.log(error_msg)
            
            if GUI_TYPE == "PyQt5":
                self.status_label.setText("Operation failed")
                self.progress.setVisible(False)
                QMessageBox.critical(self.window, "Error", error_msg)
            elif GUI_TYPE == "tkinter":
                self.status_var.set("Operation failed")
                messagebox.showerror("Error", error_msg)
    
    def basic_file_organization(self, folder, preview=True):
        """Basic file organization fallback"""
        import shutil
        from collections import defaultdict
        
        folder_path = Path(folder)
        if not folder_path.exists():
            raise Exception(f"Folder not found: {folder}")
        
        # Simple categorization
        categories = {
            'Images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
            'Documents': ['.pdf', '.doc', '.docx', '.txt'],
            'Audio': ['.mp3', '.wav', '.flac'],
            'Video': ['.mp4', '.avi', '.mov']
        }
        
        moves = defaultdict(list)
        
        for file_path in folder_path.rglob('*'):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                for category, extensions in categories.items():
                    if ext in extensions:
                        dest_dir = folder_path / category
                        moves[category].append((file_path, dest_dir / file_path.name))
                        break
        
        total_files = sum(len(files) for files in moves.values())
        
        if not preview:
            for category, file_moves in moves.items():
                category_dir = folder_path / category
                category_dir.mkdir(exist_ok=True)
                for src, dest in file_moves:
                    try:
                        shutil.move(str(src), str(dest))
                    except Exception as e:
                        self.log(f"Failed to move {src.name}: {e}")
        
        return f"{'Would move' if preview else 'Moved'} {total_files} files into {len(moves)} categories"
    
    def launch_photo_transfer(self):
        """Launch photo transfer tool"""
        try:
            import subprocess
            self.log("Launching photo transfer tool...")
            subprocess.Popen([sys.executable, "photo_transfer.py"])
        except Exception as e:
            error_msg = f"Failed to launch photo transfer: {e}"
            self.log(error_msg)
            if GUI_TYPE == "PyQt5":
                QMessageBox.critical(self.window, "Error", error_msg)
            elif GUI_TYPE == "tkinter":
                messagebox.showerror("Error", error_msg)
                
    def launch_audio_transfer(self):
        """Launch audio transfer tool"""
        try:
            import subprocess
            self.log("Launching audio transfer tool...")
            subprocess.Popen([sys.executable, "audio_transfer.py"])
        except Exception as e:
            error_msg = f"Failed to launch audio transfer: {e}"
            self.log(error_msg)
            if GUI_TYPE == "PyQt5":
                QMessageBox.critical(self.window, "Error", error_msg)
            elif GUI_TYPE == "tkinter":
                messagebox.showerror("Error", error_msg)
    
    def run(self):
        """Run the GUI application"""
        if GUI_TYPE == "PyQt5":
            self.window.show()
            return self.app.exec_()
        elif GUI_TYPE == "tkinter":
            self.root.mainloop()
            return 0
        else:
            print("No GUI framework available")
            return 1

def main():
    """Main entry point"""
    if not GUI_AVAILABLE:
        print("❌ No GUI framework available")
        print("Please install PyQt5: pip install PyQt5")
        print("Or ensure tkinter is available (usually pre-installed)")
        return 1
    
    print(f"🖥️ Launching GUI using {GUI_TYPE}")
    
    gui = FileOrganizerGUI()
    if not gui.setup_gui():
        return 1
        
    return gui.run()

if __name__ == "__main__":
    sys.exit(main())
EOF
    chmod +x working_gui.py
}

# Launch application with multiple fallbacks
launch_application() {
    print_status $BLUE "Launching FileOrganizer..."
    
    # Ensure we're in virtual environment
    source venv/bin/activate 2>/dev/null || true
    
    # Try different launch methods in order of preference
    local launch_methods=(
        "python working_gui.py"
        "python hotfix_main.py" 
        "python main.py"
        "python photo_transfer.py"
        "python audio_transfer.py"
        "python portable.py"
        "python run.py"
    )
    
    for method in "${launch_methods[@]}"; do
        print_status $BLUE "Trying: $method"
        
        if eval "$method" 2>/dev/null; then
            print_status $GREEN "Successfully launched with: $method"
            return 0
        else
            print_status $YELLOW "$method failed, trying next method..."
        fi
    done
    
    # If all GUI methods fail, show manual instructions
    print_status $RED "All launch methods failed. Manual troubleshooting:"
    echo ""
    echo "🔧 Try these commands manually:"
    echo "   source venv/bin/activate"
    echo "   python working_gui.py"
    echo "   python photo_transfer.py"
    echo "   python audio_transfer.py"
    echo ""
    echo "📋 Check what's available:"
    echo "   python -c 'import PyQt5; print(\"PyQt5: OK\")'"
    echo "   python -c 'import tkinter; print(\"tkinter: OK\")'"
    echo ""
    echo "🔄 If needed, reinstall PyQt5:"
    echo "   pip install --upgrade --force-reinstall PyQt5"
    
    return 1
}

# Create desktop shortcut (Linux only)
create_desktop_shortcut() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        read -p "Create desktop shortcut? (y/N): " create_shortcut
        if [[ $create_shortcut =~ ^[Yy]$ ]]; then
            desktop_dir="$HOME/Desktop"
            if [ -d "$desktop_dir" ]; then
                cat > "$desktop_dir/FileOrganizer.desktop" << EOF
[Desktop Entry]
Version=1.0
Name=FileOrganizer
Comment=Smart File Organization Tool  
Exec=$(pwd)/start_here.sh
Icon=$(pwd)/icon.png
Terminal=false
Type=Application
Categories=Utility;FileManager;
StartupWMClass=FileOrganizer
Path=$(pwd)
EOF
                chmod +x "$desktop_dir/FileOrganizer.desktop"
                print_status $GREEN "Desktop shortcut created"
            fi
        fi
    fi
}

# Main execution function
main() {
    print_header
    
    # Check Python installation
    if ! command_exists python3; then
        print_status $YELLOW "Python 3 not found. Installing..."
        install_python
    else
        python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
        if [[ "$(echo "$python_version < 3.8" | bc -l 2>/dev/null)" == "1" ]] 2>/dev/null; then
            print_status $RED "Python 3.8+ required. Current: $python_version"
            install_python
        else
            print_status $GREEN "Python $(python3 --version | cut -d' ' -f2) found"
        fi
    fi
    
    # Setup environment and dependencies
    setup_environment
    
    # Create configuration
    create_config
    
    # Create working GUI launcher
    create_working_gui
    
    # Create desktop shortcut
    create_desktop_shortcut
    
    print_status $GREEN "Setup completed successfully!"
    echo ""
    print_status $BLUE "🚀 Launching FileOrganizer..."
    
    # Launch application
    if launch_application; then
        print_status $GREEN "FileOrganizer is now running!"
        return 0
    else
        print_status $RED "Launch failed. Please check the manual instructions above."
        return 1
    fi
}

# Make script executable and run
if [ ! -x "$0" ]; then
    chmod +x "$0"
fi

# Run main function
main "$@"