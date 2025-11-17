"""
File utility functions

Common utilities for file operations, formatting, and path handling.
"""

from typing import Union


def format_file_size(size_bytes: Union[int, float]) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string like "1.23 MB"

    Examples:
        >>> format_file_size(1024)
        '1.00 KB'
        >>> format_file_size(1048576)
        '1.00 MB'
        >>> format_file_size(1073741824)
        '1.00 GB'
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def validate_path(path: str) -> bool:
    """
    Validate if a path string is safe and well-formed.

    Args:
        path: Path string to validate

    Returns:
        True if path is valid, False otherwise
    """
    import os
    from pathlib import Path

    if not path or not isinstance(path, str):
        return False

    try:
        # Check for path traversal attempts
        resolved = Path(path).resolve()
        return True
    except (ValueError, OSError):
        return False


def sanitize_filename(filename: str, replacement: str = '_') -> str:
    """
    Sanitize filename by removing/replacing invalid characters.

    Args:
        filename: Original filename
        replacement: Character to replace invalid chars with

    Returns:
        Sanitized filename

    Examples:
        >>> sanitize_filename('my:file?.txt')
        'my_file_.txt'
    """
    import re

    # Remove or replace invalid filename characters
    # Invalid: < > : " / \ | ? *
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, replacement, filename)

    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')

    # Ensure filename is not empty
    if not sanitized:
        sanitized = 'unnamed'

    return sanitized


def get_unique_path(base_path, max_attempts: int = 1000):
    """
    Get a unique file path by appending numbers if file exists.

    Args:
        base_path: Base path (Path object or string)
        max_attempts: Maximum number of attempts

    Returns:
        Unique Path object

    Examples:
        If 'file.txt' exists, returns 'file (1).txt'
        If 'file (1).txt' exists, returns 'file (2).txt'
    """
    from pathlib import Path

    base_path = Path(base_path)

    if not base_path.exists():
        return base_path

    stem = base_path.stem
    suffix = base_path.suffix
    parent = base_path.parent

    for i in range(1, max_attempts + 1):
        new_path = parent / f"{stem} ({i}){suffix}"
        if not new_path.exists():
            return new_path

    # If we exhausted all attempts, append timestamp
    import time
    timestamp = int(time.time())
    return parent / f"{stem}_{timestamp}{suffix}"
