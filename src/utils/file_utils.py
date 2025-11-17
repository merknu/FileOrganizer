"""
File utility functions

Common utilities for file operations, formatting, and path handling.
"""

from typing import Union, Optional, Tuple
from pathlib import Path
import hashlib


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


def get_file_hash(file_path: Union[str, Path], algorithm: str = 'sha256', chunk_size: int = 8192) -> Optional[str]:
    """
    Calculate hash of a file using specified algorithm.

    Args:
        file_path: Path to file
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256', 'sha512')
        chunk_size: Size of chunks to read (default 8KB)

    Returns:
        Hex digest of file hash, or None if error

    Examples:
        >>> get_file_hash('file.txt', 'md5')
        'd41d8cd98f00b204e9800998ecf8427e'
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists() or not file_path.is_file():
            return None

        hash_obj = hashlib.new(algorithm)

        with open(file_path, 'rb') as f:
            while chunk := f.read(chunk_size):
                hash_obj.update(chunk)

        return hash_obj.hexdigest()

    except (OSError, ValueError) as e:
        return None


def is_binary_file(file_path: Union[str, Path], sample_size: int = 8192) -> bool:
    """
    Check if a file is binary by examining a sample of bytes.

    Args:
        file_path: Path to file
        sample_size: Number of bytes to sample (default 8KB)

    Returns:
        True if file appears to be binary, False otherwise

    Examples:
        >>> is_binary_file('image.png')
        True
        >>> is_binary_file('text.txt')
        False
    """
    try:
        file_path = Path(file_path)
        if not file_path.exists() or not file_path.is_file():
            return False

        with open(file_path, 'rb') as f:
            chunk = f.read(sample_size)

        # Check for null bytes (common in binary files)
        if b'\x00' in chunk:
            return True

        # Check for high ratio of non-text characters
        text_characters = bytes(range(32, 127)) + b'\n\r\t\b'
        non_text = sum(1 for byte in chunk if byte not in text_characters)

        # If more than 30% non-text, likely binary
        return (non_text / len(chunk)) > 0.3 if chunk else False

    except (OSError, UnicodeDecodeError):
        return True


def safe_copy(src: Union[str, Path], dest: Union[str, Path], overwrite: bool = False) -> Tuple[bool, str]:
    """
    Safely copy a file with verification.

    Args:
        src: Source file path
        dest: Destination file path
        overwrite: Whether to overwrite existing file

    Returns:
        Tuple of (success: bool, message: str)

    Examples:
        >>> safe_copy('source.txt', 'dest.txt')
        (True, 'File copied successfully')
    """
    import shutil

    try:
        src_path = Path(src)
        dest_path = Path(dest)

        # Validate source
        if not src_path.exists():
            return False, f"Source file does not exist: {src_path}"

        if not src_path.is_file():
            return False, f"Source is not a file: {src_path}"

        # Check destination
        if dest_path.exists() and not overwrite:
            return False, f"Destination already exists: {dest_path}"

        # Create parent directory if needed
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Get source size and hash
        src_size = src_path.stat().st_size
        src_hash = get_file_hash(src_path)

        # Copy file
        shutil.copy2(src_path, dest_path)

        # Verify copy
        if not dest_path.exists():
            return False, "Destination file was not created"

        dest_size = dest_path.stat().st_size
        if src_size != dest_size:
            return False, f"Size mismatch: {src_size} != {dest_size}"

        dest_hash = get_file_hash(dest_path)
        if src_hash != dest_hash:
            return False, "Hash mismatch after copy"

        return True, "File copied successfully"

    except Exception as e:
        return False, f"Copy failed: {str(e)}"


def get_file_age_days(file_path: Union[str, Path]) -> Optional[int]:
    """
    Get the age of a file in days based on modification time.

    Args:
        file_path: Path to file

    Returns:
        Age in days, or None if error

    Examples:
        >>> get_file_age_days('old_file.txt')
        365
    """
    from datetime import datetime

    try:
        file_path = Path(file_path)
        if not file_path.exists():
            return None

        mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        age = datetime.now() - mtime
        return age.days

    except (OSError, ValueError):
        return None
