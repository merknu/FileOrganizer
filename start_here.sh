#!/bin/bash
# FileOrganizer Easy Setup and Launcher for Linux/macOS
# Run: chmod +x start_here.sh && ./start_here.sh

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
    echo -e "\n${BLUE}===========================================${NC}"
    echo -e "${BOLD}   FileOrganizer - Easy Setup & Launch${NC}"
    echo -e "${BLUE}===========================================${NC}\n"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Main setup function
main() {
    print_header
    
    # Check Python installation
    if ! command_exists python3; then
        print_status $RED "Python 3 is not installed!"
        echo "Please install Python 3.8+ and try again."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "macOS: brew install python3 or download from https://www.python.org"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            echo "Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip python3-venv"
            echo "CentOS/RHEL: sudo yum install python3 python3-pip"
            echo "Arch: sudo pacman -S python python-pip"
        fi
        exit 1
    fi
    
    print_status $GREEN "Python 3 is installed"
    python3 --version
    
    # Check pip
    if ! command_exists pip3; then
        print_status $YELLOW "pip3 not found, trying to install..."
        if [[ "$OSTYPE" == "darwin"* ]]; then
            python3 -m ensurepip --upgrade
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Try different package managers
            if command_exists apt; then
                sudo apt update && sudo apt install python3-pip -y
            elif command_exists yum; then
                sudo yum install python3-pip -y
            elif command_exists pacman; then
                sudo pacman -S python-pip
            fi
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
    
    # Install requirements
    print_status $BLUE "Installing dependencies..."
    echo "This may take a few minutes..."
    
    if [ -f "requirements.txt" ]; then
        if ! python -m pip install -r requirements.txt; then
            print_status $YELLOW "Some dependencies failed, trying alternative installation..."
            
            # Core dependencies
            python -m pip install "PyQt5>=5.15.0" || print_status $YELLOW "PyQt5 failed (GUI may not work)"
            python -m pip install "watchdog>=2.1.0"
            python -m pip install "Pillow>=10.0.0"
            python -m pip install "mutagen>=1.46.0"
            python -m pip install "pypdf>=3.17.0"
            python -m pip install "python-docx>=0.8.11"
            python -m pip install "moviepy>=1.0.3" || print_status $YELLOW "moviepy failed (video support limited)"
            
            # Optional dependencies
            python -m pip install "python-magic>=0.4.27" || print_status $YELLOW "python-magic failed (file detection may be limited)"
            python -m pip install "pyopencl" || print_status $YELLOW "pyopencl failed (GPU acceleration disabled)"
            python -m pip install "numpy" || print_status $YELLOW "numpy failed (some features disabled)"
        fi
    else
        print_status $RED "requirements.txt not found!"
        exit 1
    fi
    
    print_status $GREEN "Dependencies installed successfully!"
    
    # Create configuration if it doesn't exist
    if [ ! -f "config/config.json" ]; then
        print_status $BLUE "Creating default configuration..."
        mkdir -p config
        cat > config/config.json << 'EOF'
{
    "file_categories": {
        "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"],
        "Audio": [".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac"],
        "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt"],
        "Video": [".mp4", ".avi", ".mov", ".mkv", ".wmv", ".flv", ".webm"],
        "Archives": [".zip", ".rar", ".7z", ".tar", ".gz"]
    },
    "subfolders": {
        ".pdf": "PDFs",
        ".doc": "Word_Documents",
        ".docx": "Word_Documents",
        ".txt": "Text_Files"
    },
    "default_duplicate_action": "k",
    "enable_gpu": true,
    "max_workers": 4
}
EOF
        print_status $GREEN "Default configuration created"
    fi
    
    # Create desktop shortcut (Linux only)
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
EOF
                chmod +x "$desktop_dir/FileOrganizer.desktop"
                print_status $GREEN "Desktop shortcut created"
            fi
        fi
    fi
    
    # Launch application
    echo ""
    print_status $BLUE "Launching FileOrganizer..."
    echo ""
    
    if python main.py; then
        print_status $GREEN "Application launched successfully!"
    else
        print_status $RED "Failed to launch GUI application"
        echo ""
        echo "TROUBLESHOOTING:"
        echo "================"
        echo "1. Make sure you have Python 3.8+ installed"
        echo "2. For GUI issues on Linux, try: sudo apt install python3-pyqt5"
        echo "3. Alternative launch: python photo_transfer.py"
        echo "4. Check logs for more details"
        echo ""
        
        # Try alternative launches
        read -p "Try photo transfer tool instead? (y/N): " try_photo
        if [[ $try_photo =~ ^[Yy]$ ]]; then
            python photo_transfer.py
        fi
    fi
}

# Make script executable and run
if [ ! -x "$0" ]; then
    chmod +x "$0"
fi

# Run main function
main "$@"