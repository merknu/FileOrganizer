#!/bin/bash

# Media Transfer Hub - FileOrganizer
# Advanced file transfer tools with transcoding capabilities

# Colors for terminal output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to check dependencies
check_dependencies() {
    echo -e "${CYAN}Checking dependencies...${NC}"
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: Python 3 is not installed${NC}"
        echo "Please install Python 3.7+ from python.org or your package manager"
        exit 1
    fi
    
    # Check PyQt5
    python3 -c "import PyQt5" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}PyQt5 not found. Installing...${NC}"
        pip3 install PyQt5
    fi
    
    # Check ffmpeg
    if ! command -v ffmpeg &> /dev/null; then
        echo -e "${YELLOW}Warning: ffmpeg not found${NC}"
        echo "Audio/Video transcoding features will not be available"
        echo "Install ffmpeg with: sudo apt install ffmpeg (Ubuntu/Debian)"
        echo "                     brew install ffmpeg (macOS)"
        echo ""
    fi
    
    # Check mutagen for audio metadata
    python3 -c "import mutagen" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Installing mutagen for audio metadata...${NC}"
        pip3 install mutagen
    fi
}

# Function to display menu
show_menu() {
    clear
    echo -e "${BLUE}============================================${NC}"
    echo -e "${GREEN}        MEDIA TRANSFER HUB${NC}"
    echo -e "${CYAN}    Advanced File Transfer with Transcoding${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    echo "Select a transfer tool to launch:"
    echo ""
    echo "  [1] Photo Transfer Tool"
    echo "      - Advanced photo selection by date"
    echo "      - Metadata preservation"
    echo "      - Duplicate detection"
    echo ""
    echo "  [2] Audio Transfer Tool"
    echo "      - Audio transcoding (MP3, AAC, FLAC, etc.)"
    echo "      - Metadata-based filtering"
    echo "      - Audio normalization"
    echo "      - Batch processing"
    echo ""
    echo "  [3] Video Transfer Tool"
    echo "      - Video transcoding with ffmpeg"
    echo "      - Resolution scaling"
    echo "      - Format conversion"
    echo "      - Hardware acceleration"
    echo ""
    echo "  [4] Launch Main FileOrganizer"
    echo ""
    echo "  [0] Exit"
    echo ""
    echo -e "${BLUE}============================================${NC}"
}

# Main loop
while true; do
    show_menu
    read -p "Enter your choice (0-4): " choice
    
    case $choice in
        1)
            echo -e "\n${GREEN}Launching Photo Transfer Tool...${NC}"
            python3 photo_transfer.py
            if [ $? -ne 0 ]; then
                echo -e "${RED}Error launching Photo Transfer Tool${NC}"
                read -p "Press Enter to continue..."
            fi
            ;;
        2)
            echo -e "\n${GREEN}Launching Audio Transfer Tool...${NC}"
            python3 audio_transfer.py
            if [ $? -ne 0 ]; then
                echo -e "${RED}Error launching Audio Transfer Tool${NC}"
                read -p "Press Enter to continue..."
            fi
            ;;
        3)
            echo -e "\n${GREEN}Launching Video Transfer Tool...${NC}"
            python3 video_transfer.py
            if [ $? -ne 0 ]; then
                echo -e "${RED}Error launching Video Transfer Tool${NC}"
                read -p "Press Enter to continue..."
            fi
            ;;
        4)
            echo -e "\n${GREEN}Launching Main FileOrganizer...${NC}"
            python3 main.py
            if [ $? -ne 0 ]; then
                echo -e "${RED}Error launching FileOrganizer${NC}"
                read -p "Press Enter to continue..."
            fi
            ;;
        0)
            echo -e "\n${GREEN}Thank you for using Media Transfer Hub!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please try again.${NC}"
            sleep 2
            ;;
    esac
done