"""
Constants for FileOrganizer

Centralized configuration constants to avoid magic numbers and hardcoded values.
"""

# File size constants (in bytes)
KB = 1024
MB = 1024 * KB
GB = 1024 * MB
TB = 1024 * GB
PB = 1024 * TB

# Time constants (in seconds)
SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR
WEEK = 7 * DAY

# Default settings
DEFAULT_NOTIFICATION_DURATION = 5  # seconds
DEFAULT_AUTO_ORGANIZE_INTERVAL = 60  # minutes
DEFAULT_DUPLICATE_ACTION = 'k'  # keep, overwrite, rename

# File operation limits
MAX_FILENAME_LENGTH = 255
MAX_PATH_LENGTH = 4096
MAX_UNIQUE_ATTEMPTS = 1000
DEFAULT_CHUNK_SIZE = 8 * MB  # for file operations

# UI constants
MIN_DIALOG_WIDTH = 450
MIN_DIALOG_HEIGHT = 300
DEFAULT_WINDOW_WIDTH = 900
DEFAULT_WINDOW_HEIGHT = 700

# Progress reporting
PROGRESS_UPDATE_INTERVAL = 100  # milliseconds
TOOLTIP_UPDATE_INTERVAL = 2000  # milliseconds

# Validation patterns
INVALID_FILENAME_CHARS = r'[<>:"/\\|?*]'

# File categories
SUPPORTED_IMAGE_FORMATS = (
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
    '.svg', '.webp', '.ico', '.psd', '.ai', '.eps',
    '.raw', '.cr2', '.cr3', '.nef', '.arw', '.orf', '.dng',
    '.heic', '.heif', '.avif'
)

SUPPORTED_VIDEO_FORMATS = (
    '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
    '.m4v', '.mpg', '.mpeg', '.3gp', '.3g2', '.mts', '.m2ts',
    '.vob', '.ogv', '.divx', '.xvid', '.asf', '.rm', '.rmvb'
)

SUPPORTED_AUDIO_FORMATS = (
    '.mp3', '.flac', '.wav', '.aac', '.ogg', '.wma', '.m4a',
    '.opus', '.ape', '.alac', '.aiff', '.au', '.ra', '.ac3'
)

SUPPORTED_DOCUMENT_FORMATS = (
    '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages',
    '.xls', '.xlsx', '.ods', '.numbers', '.csv',
    '.ppt', '.pptx', '.odp', '.key'
)

SUPPORTED_ARCHIVE_FORMATS = (
    '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz',
    '.tar.gz', '.tar.bz2', '.tar.xz', '.tgz', '.tbz2'
)

# Temporary file patterns
TEMP_FILE_PATTERNS = ('*.tmp', '*.temp', '*~', '*.bak', '*.cache')

# Exclude patterns for file scanning
DEFAULT_EXCLUDE_PATTERNS = (
    '.crdownload',  # Chrome incomplete download
    '.part',        # Firefox incomplete download
    '.partial',     # Generic partial
    '.download',    # Generic download in progress
    '.tmp',         # Temporary files
)

# Logging
DEFAULT_LOG_LEVEL = 'INFO'
DEFAULT_LOG_FORMAT = '%(asctime)s - %(levelname)s - %(module)s - %(funcName)s - %(lineno)d - %(message)s'
DEFAULT_LOG_FILE = 'file_organizer.log'

# System folders (relative to user home)
SYSTEM_FOLDERS = {
    'downloads': 'Downloads',
    'desktop': 'Desktop',
    'documents': 'Documents',
    'pictures': 'Pictures',
    'videos': 'Videos',
    'music': 'Music',
}

# Application metadata
APP_NAME = 'FileOrganizer'
APP_ORG = 'FileOrganizer'
CONFIG_DIR_NAME = '.fileorganizer'
SCENARIOS_DIR_NAME = 'scenarios'
