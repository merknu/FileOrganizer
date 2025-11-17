"""
Utility functions for FileOrganizer

This package contains common utility functions and constants used throughout
the application.

Modules:
    file_utils: File operation utilities
    constants: Application-wide constants
"""

from .file_utils import (
    format_file_size,
    validate_path,
    sanitize_filename,
    get_unique_path,
    get_file_hash,
    is_binary_file,
    safe_copy,
    get_file_age_days,
)

from .constants import (
    KB, MB, GB, TB,
    MINUTE, HOUR, DAY,
    DEFAULT_NOTIFICATION_DURATION,
    MAX_FILENAME_LENGTH,
    INVALID_FILENAME_CHARS,
)

__all__ = [
    # File utilities
    'format_file_size',
    'validate_path',
    'sanitize_filename',
    'get_unique_path',
    'get_file_hash',
    'is_binary_file',
    'safe_copy',
    'get_file_age_days',
    # Constants
    'KB', 'MB', 'GB', 'TB',
    'MINUTE', 'HOUR', 'DAY',
    'DEFAULT_NOTIFICATION_DURATION',
    'MAX_FILENAME_LENGTH',
    'INVALID_FILENAME_CHARS',
]
