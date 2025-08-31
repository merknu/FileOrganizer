# Path: main.py
import sys
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QAction, QVBoxLayout, QHBoxLayout, 
    QWidget, QPushButton, QLabel, QFileDialog, QMessageBox,
    QSystemTrayIcon, QMenu, QGroupBox, QGridLayout, QProgressBar,
    QTextEdit, QTabWidget
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QFont
from config.config_handler import ConfigHandler
from gui.main_window import FileOrganizerMainWindow
from gui.photo_transfer_window import PhotoTransferWindow

logging.basicConfig(filename='file_organizer.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s')


CONFIG_FILE = 'config/config.json'
config_handler = ConfigHandler(CONFIG_FILE)
global_app_config = config_handler.config


class MainApplication(QMainWindow):
    """Main FileOrganizer application with system tray support"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FileOrganizer")
        self.setGeometry(100, 100, 900, 700)
        
        # Initialize system tray
        self.init_system_tray()
        
        # Create main interface
        self.init_ui()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def init_system_tray(self):
        """Initialize system tray icon and menu"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create tray menu
        tray_menu = QMenu()
        
        # Show/Hide action
        show_action = QAction("Show FileOrganizer", self)
        show_action.triggered.connect(self.show_window)
        tray_menu.addAction(show_action)
        
        # Quick actions
        tray_menu.addSeparator()
        
        organize_action = QAction("Quick Organize Files", self)
        organize_action.triggered.connect(self.quick_organize_files)
        tray_menu.addAction(organize_action)
        
        video_action = QAction("Process Videos", self)
        video_action.triggered.connect(self.process_videos)
        tray_menu.addAction(video_action)
        
        audio_action = QAction("Process Audio", self)
        audio_action.triggered.connect(self.process_audio)
        tray_menu.addAction(audio_action)
        
        tray_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(QApplication.instance().quit)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        
        # Set tray icon (use default for now)
        self.tray_icon.setToolTip("FileOrganizer")
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Show tray icon
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon.show()
    
    def init_ui(self):
        """Create the main user interface"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Title
        title_label = QLabel("FileOrganizer")
        title_label.setFont(QFont("Arial", 18, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # Create tabs for different functions
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)
        
        # File Organization Tab
        self.create_file_org_tab()
        
        # Video Processing Tab
        self.create_video_tab()
        
        # Audio Processing Tab
        self.create_audio_tab()
        
        # Status area
        self.status_text = QTextEdit()
        self.status_text.setMaximumHeight(100)
        self.status_text.setPlaceholderText("Activity log will appear here...")
        main_layout.addWidget(QLabel("Activity Log:"))
        main_layout.addWidget(self.status_text)
    
    def create_file_org_tab(self):
        """Create file organization tab"""
        file_tab = QWidget()
        layout = QVBoxLayout(file_tab)
        
        # Quick actions group
        quick_group = QGroupBox("Quick File Organization")
        quick_layout = QGridLayout(quick_group)
        
        # Select files button
        select_files_btn = QPushButton("Select Files to Organize")
        select_files_btn.clicked.connect(self.select_files_to_organize)
        quick_layout.addWidget(select_files_btn, 0, 0)
        
        # Select folder button
        select_folder_btn = QPushButton("Select Folder to Organize")
        select_folder_btn.clicked.connect(self.select_folder_to_organize)
        quick_layout.addWidget(select_folder_btn, 0, 1)
        
        # Downloads organizer
        downloads_btn = QPushButton("Organize Downloads Folder")
        downloads_btn.clicked.connect(self.organize_downloads)
        quick_layout.addWidget(downloads_btn, 1, 0)
        
        # Desktop organizer
        desktop_btn = QPushButton("Organize Desktop")
        desktop_btn.clicked.connect(self.organize_desktop)
        quick_layout.addWidget(desktop_btn, 1, 1)
        
        layout.addWidget(quick_group)
        
        # Advanced options
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QVBoxLayout(advanced_group)
        
        advanced_btn = QPushButton("Open Advanced File Organizer")
        advanced_btn.clicked.connect(self.open_advanced_organizer)
        advanced_layout.addWidget(advanced_btn)
        
        layout.addWidget(advanced_group)
        
        self.tab_widget.addTab(file_tab, "File Organization")
    
    def create_video_tab(self):
        """Create video processing tab"""
        video_tab = QWidget()
        layout = QVBoxLayout(video_tab)
        
        # Video actions group
        video_group = QGroupBox("Video Processing")
        video_layout = QGridLayout(video_group)
        
        select_videos_btn = QPushButton("Select Video Files")
        select_videos_btn.clicked.connect(self.select_videos)
        video_layout.addWidget(select_videos_btn, 0, 0)
        
        convert_videos_btn = QPushButton("Convert/Compress Videos")
        convert_videos_btn.clicked.connect(self.convert_videos)
        video_layout.addWidget(convert_videos_btn, 0, 1)
        
        organize_videos_btn = QPushButton("Organize Video Library")
        organize_videos_btn.clicked.connect(self.organize_videos)
        video_layout.addWidget(organize_videos_btn, 1, 0)
        
        transfer_videos_btn = QPushButton("Transfer Videos")
        transfer_videos_btn.clicked.connect(self.transfer_videos)
        video_layout.addWidget(transfer_videos_btn, 1, 1)
        
        layout.addWidget(video_group)
        self.tab_widget.addTab(video_tab, "Video Processing")
    
    def create_audio_tab(self):
        """Create audio processing tab"""
        audio_tab = QWidget()
        layout = QVBoxLayout(audio_tab)
        
        # Audio actions group
        audio_group = QGroupBox("Audio Processing")
        audio_layout = QGridLayout(audio_group)
        
        select_audio_btn = QPushButton("Select Audio Files")
        select_audio_btn.clicked.connect(self.select_audio)
        audio_layout.addWidget(select_audio_btn, 0, 0)
        
        convert_audio_btn = QPushButton("Convert Audio Format")
        convert_audio_btn.clicked.connect(self.convert_audio)
        audio_layout.addWidget(convert_audio_btn, 0, 1)
        
        organize_audio_btn = QPushButton("Organize Music Library")
        organize_audio_btn.clicked.connect(self.organize_audio)
        audio_layout.addWidget(organize_audio_btn, 1, 0)
        
        transfer_audio_btn = QPushButton("Transfer Audio Files")
        transfer_audio_btn.clicked.connect(self.transfer_audio)
        audio_layout.addWidget(transfer_audio_btn, 1, 1)
        
        layout.addWidget(audio_group)
        self.tab_widget.addTab(audio_tab, "Audio Processing")
    
    def create_menu_bar(self):
        """Create application menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu("Tools")
        
        advanced_action = QAction("Advanced File Organizer", self)
        advanced_action.triggered.connect(self.open_advanced_organizer)
        tools_menu.addAction(advanced_action)
        
        photo_action = QAction("Photo Transfer Tool", self)
        photo_action.triggered.connect(self.open_photo_transfer)
        tools_menu.addAction(photo_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        minimize_to_tray_action = QAction("Minimize to Tray", self)
        minimize_to_tray_action.triggered.connect(self.hide)
        view_menu.addAction(minimize_to_tray_action)
    
    def log_activity(self, message):
        """Add message to activity log"""
        self.status_text.append(f"• {message}")
        self.statusBar().showMessage(message)
    
    # System tray methods
    def show_window(self):
        """Show the main window"""
        self.show()
        self.raise_()
        self.activateWindow()
    
    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            if self.isVisible():
                self.hide()
            else:
                self.show_window()
    
    def closeEvent(self, event):
        """Handle window close event"""
        if self.tray_icon.isVisible():
            QMessageBox.information(self, "FileOrganizer",
                                  "Application was minimized to tray. "
                                  "Right-click the tray icon to access functions or exit.")
            self.hide()
            event.ignore()
        else:
            event.accept()
    
    def changeEvent(self, event):
        """Handle window state changes"""
        if event.type() == event.WindowStateChange:
            if self.windowState() & Qt.WindowMinimized:
                # Hide to tray when minimized
                QTimer.singleShot(0, self.hide)
        super().changeEvent(event)
    
    # File operation methods (implement the actual functionality)
    def select_files_to_organize(self):
        """Select individual files to organize"""
        files, _ = QFileDialog.getOpenFileNames(self, "Select Files to Organize", 
                                               "", "All Files (*.*)")
        if files:
            self.log_activity(f"Selected {len(files)} files for organization")
            # TODO: Implement file organization logic
            QMessageBox.information(self, "Files Selected", 
                                  f"Selected {len(files)} files. Organization feature coming soon!")
    
    def select_folder_to_organize(self):
        """Select folder to organize"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Organize")
        if folder:
            self.log_activity(f"Selected folder for organization: {folder}")
            # TODO: Implement folder organization logic
            QMessageBox.information(self, "Folder Selected", 
                                  f"Selected folder: {folder}\nOrganization feature coming soon!")
    
    def organize_downloads(self):
        """Organize downloads folder"""
        self.log_activity("Organizing Downloads folder...")
        # TODO: Implement downloads organization
        QMessageBox.information(self, "Downloads Organization", "Downloads organization feature coming soon!")
    
    def organize_desktop(self):
        """Organize desktop"""
        self.log_activity("Organizing Desktop...")
        # TODO: Implement desktop organization
        QMessageBox.information(self, "Desktop Organization", "Desktop organization feature coming soon!")
    
    def quick_organize_files(self):
        """Quick organize from tray"""
        self.show_window()
        self.tab_widget.setCurrentIndex(0)  # Switch to file organization tab
    
    def process_videos(self):
        """Process videos from tray"""
        self.show_window()
        self.tab_widget.setCurrentIndex(1)  # Switch to video tab
    
    def process_audio(self):
        """Process audio from tray"""
        self.show_window()
        self.tab_widget.setCurrentIndex(2)  # Switch to audio tab
    
    def select_videos(self):
        """Select video files"""
        files, _ = QFileDialog.getOpenFileNames(self, "Select Video Files", 
                                               "", "Video Files (*.mp4 *.avi *.mkv *.mov *.wmv *.flv)")
        if files:
            self.log_activity(f"Selected {len(files)} video files")
            QMessageBox.information(self, "Videos Selected", 
                                  f"Selected {len(files)} video files. Processing feature coming soon!")
    
    def convert_videos(self):
        """Convert/compress videos"""
        self.log_activity("Starting video conversion...")
        QMessageBox.information(self, "Video Conversion", "Video conversion feature coming soon!")
    
    def organize_videos(self):
        """Organize video library"""
        self.log_activity("Organizing video library...")
        QMessageBox.information(self, "Video Organization", "Video organization feature coming soon!")
    
    def transfer_videos(self):
        """Transfer videos"""
        self.log_activity("Starting video transfer...")
        QMessageBox.information(self, "Video Transfer", "Video transfer feature coming soon!")
    
    def select_audio(self):
        """Select audio files"""
        files, _ = QFileDialog.getOpenFileNames(self, "Select Audio Files", 
                                               "", "Audio Files (*.mp3 *.wav *.flac *.aac *.ogg *.wma)")
        if files:
            self.log_activity(f"Selected {len(files)} audio files")
            QMessageBox.information(self, "Audio Selected", 
                                  f"Selected {len(files)} audio files. Processing feature coming soon!")
    
    def convert_audio(self):
        """Convert audio format"""
        self.log_activity("Starting audio conversion...")
        QMessageBox.information(self, "Audio Conversion", "Audio conversion feature coming soon!")
    
    def organize_audio(self):
        """Organize music library"""
        self.log_activity("Organizing music library...")
        QMessageBox.information(self, "Audio Organization", "Audio organization feature coming soon!")
    
    def transfer_audio(self):
        """Transfer audio files"""
        self.log_activity("Starting audio transfer...")
        QMessageBox.information(self, "Audio Transfer", "Audio transfer feature coming soon!")
    
    def open_advanced_organizer(self):
        """Open the advanced file organizer"""
        self.file_organizer = FileOrganizerMainWindow(global_app_config)
        self.file_organizer.show()
    
    def open_photo_transfer(self):
        """Open the photo transfer window"""
        self.photo_transfer = PhotoTransferWindow()
        self.photo_transfer.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("FileOrganizer")
    
    # Import and use enhanced version if available
    try:
        from main_enhanced import EnhancedMainApplication
        window = EnhancedMainApplication()
    except ImportError:
        # Fall back to basic version
        window = MainApplication()
    
    window.show()
    sys.exit(app.exec_())
