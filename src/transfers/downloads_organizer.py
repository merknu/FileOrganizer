#!/usr/bin/env python3
"""
Downloads Folder Organizer
Automatically organizes downloads by moving files to appropriate system folders
(Documents, Pictures, Videos, Music) based on file type
"""

import os
import sys
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

# File type categorization
FILE_CATEGORIES = {
    'documents': {
        'folder': 'Documents',
        'extensions': {
            '.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages',
            '.xls', '.xlsx', '.ods', '.numbers', '.csv',
            '.ppt', '.pptx', '.odp', '.key',
            '.epub', '.mobi', '.azw', '.azw3',
            '.tex', '.md', '.rst', '.html', '.htm',
            '.json', '.xml', '.yaml', '.yml', '.ini', '.cfg', '.conf'
        },
        'icon': '📄'
    },
    
    'images': {
        'folder': 'Pictures',
        'extensions': {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif',
            '.svg', '.webp', '.ico', '.psd', '.ai', '.eps',
            '.raw', '.cr2', '.cr3', '.nef', '.arw', '.orf', '.dng',
            '.heic', '.heif', '.avif'
        },
        'icon': '🖼️'
    },
    
    'videos': {
        'folder': 'Videos',
        'extensions': {
            '.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
            '.m4v', '.mpg', '.mpeg', '.3gp', '.3g2', '.mts', '.m2ts',
            '.vob', '.ogv', '.divx', '.xvid', '.asf', '.rm', '.rmvb',
            '.f4v', '.ts', '.mxf', '.h264', '.h265', '.hevc'
        },
        'icon': '🎬'
    },
    
    'music': {
        'folder': 'Music',
        'extensions': {
            '.mp3', '.flac', '.wav', '.aac', '.ogg', '.wma', '.m4a',
            '.opus', '.ape', '.alac', '.aiff', '.au', '.ra', '.ac3',
            '.dts', '.mka', '.oga', '.spx', '.tta', '.wv'
        },
        'icon': '🎵'
    },
    
    'archives': {
        'folder': 'Documents/Archives',  # Subfolder in Documents
        'extensions': {
            '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz',
            '.tar.gz', '.tar.bz2', '.tar.xz', '.tgz', '.tbz2',
            '.cab', '.iso', '.dmg', '.pkg', '.deb', '.rpm'
        },
        'icon': '📦'
    },
    
    'executables': {
        'folder': 'Downloads/Software',  # Keep in Downloads subfolder
        'extensions': {
            '.exe', '.msi', '.dmg', '.pkg', '.deb', '.rpm', '.appimage',
            '.app', '.run', '.bin', '.apk', '.ipa'
        },
        'icon': '⚙️'
    },
    
    'fonts': {
        'folder': 'Documents/Fonts',  # Subfolder in Documents
        'extensions': {
            '.ttf', '.otf', '.woff', '.woff2', '.eot', '.fon', '.bdf'
        },
        'icon': '🔤'
    },
    
    'code': {
        'folder': 'Documents/Code',  # Subfolder in Documents
        'extensions': {
            '.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h',
            '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.ts',
            '.jsx', '.tsx', '.vue', '.scss', '.sass', '.less', '.sql'
        },
        'icon': '💻'
    },
    
    'ebooks': {
        'folder': 'Documents/eBooks',  # Subfolder in Documents
        'extensions': {
            '.epub', '.mobi', '.azw', '.azw3', '.pdf', '.fb2', '.lit', '.prc'
        },
        'icon': '📚'
    }
}

class SystemFolderManager:
    """Manages system folder paths across different operating systems and users"""
    
    def __init__(self):
        self.current_user = self.get_current_user_info()
        self.system_folders = self.detect_system_folders()
        self.ensure_folders_exist()
        
    def get_current_user_info(self) -> Dict[str, str]:
        """Get information about the current user"""
        # Safe username detection
        username = 'Unknown'
        try:
            if hasattr(os, 'getlogin'):
                username = os.getlogin()
        except (OSError, AttributeError):
            # Fallback to environment variables
            username = os.environ.get('USER', os.environ.get('USERNAME', 'Unknown'))
        
        user_info = {
            'username': username,
            'home_path': str(Path.home()),
            'profile_path': os.environ.get('USERPROFILE', str(Path.home()))
        }
        
        # Add Windows-specific user info
        if sys.platform == 'win32':
            user_info.update({
                'appdata': os.environ.get('APPDATA', ''),
                'localappdata': os.environ.get('LOCALAPPDATA', ''),
                'public_profile': os.environ.get('PUBLIC', 'C:\\Users\\Public')
            })
            
        return user_info
        
    def detect_system_folders(self) -> Dict[str, Path]:
        """Detect system folders for current OS and user"""
        folders = {}
        
        if sys.platform == 'win32':
            # Windows - Try multiple detection methods
            folders = self._detect_windows_folders()
        elif sys.platform == 'darwin':
            # macOS
            folders = self._detect_macos_folders()
        else:
            # Linux/Unix
            folders = self._detect_linux_folders()
            
        # Validate and create missing folders
        folders = self._validate_and_fix_folders(folders)
        return folders
    
    def _detect_windows_folders(self) -> Dict[str, Path]:
        """Detect Windows system folders using multiple methods"""
        folders = {}
        
        # Method 1: Try winshell (if available)
        try:
            import winshell
            folders['Desktop'] = Path(winshell.desktop())
            folders['Documents'] = Path(winshell.my_documents())
            folders['Pictures'] = Path(winshell.pictures())
            folders['Videos'] = Path(winshell.videos())
            folders['Music'] = Path(winshell.music())
            
            # Downloads folder (winshell doesn't have direct support)
            downloads_candidates = [
                Path(winshell.desktop()).parent / 'Downloads',
                Path(self.current_user['home_path']) / 'Downloads',
                Path(self.current_user['profile_path']) / 'Downloads'
            ]
            
            for candidate in downloads_candidates:
                if candidate.exists():
                    folders['Downloads'] = candidate
                    break
            else:
                # Create Downloads in user profile
                folders['Downloads'] = Path(self.current_user['profile_path']) / 'Downloads'
                
        except ImportError:
            # Method 2: Use Windows environment variables
            folders = self._detect_windows_folders_env()
        except Exception as e:
            logging.warning(f"winshell detection failed: {e}, falling back to environment variables")
            folders = self._detect_windows_folders_env()
            
        # Method 3: Try Windows registry (if available)
        if not folders or len(folders) < 5:
            try:
                registry_folders = self._detect_windows_folders_registry()
                folders.update(registry_folders)
            except Exception as e:
                logging.warning(f"Registry detection failed: {e}")
        
        return folders
    
    def _detect_windows_folders_env(self) -> Dict[str, Path]:
        """Detect Windows folders using environment variables"""
        user_profile = Path(self.current_user['profile_path'])
        
        return {
            'Desktop': user_profile / 'Desktop',
            'Documents': user_profile / 'Documents',
            'Downloads': user_profile / 'Downloads', 
            'Pictures': user_profile / 'Pictures',
            'Videos': user_profile / 'Videos',
            'Music': user_profile / 'Music'
        }
    
    def _detect_windows_folders_registry(self) -> Dict[str, Path]:
        """Detect Windows folders using registry (requires winreg)"""
        folders = {}
        
        try:
            import winreg
            
            # Known folder GUIDs for Windows
            folder_guids = {
                'Desktop': '{B4BFCC3A-DB2C-424C-B029-7FE99A87C641}',
                'Documents': '{FDD39AD0-238F-46AF-ADB4-6C85480369C7}',
                'Downloads': '{374DE290-123F-4565-9164-39C4925E467B}',
                'Pictures': '{33E28130-4E1E-4676-835A-98395C3BC3BB}',
                'Videos': '{18989B1D-99B5-455B-841C-AB7C74E4DDFC}',
                'Music': '{4BD8D571-6D19-48D3-BE97-422220080E43}'
            }
            
            reg_key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            )
            
            for folder_name, guid in folder_guids.items():
                try:
                    folder_path, _ = winreg.QueryValueEx(reg_key, folder_name)
                    if folder_path and Path(folder_path).exists():
                        folders[folder_name] = Path(folder_path)
                except FileNotFoundError:
                    continue
                    
            winreg.CloseKey(reg_key)
            
        except ImportError:
            logging.info("winreg not available, skipping registry detection")
        except Exception as e:
            logging.warning(f"Registry detection error: {e}")
            
        return folders
    
    def _detect_macos_folders(self) -> Dict[str, Path]:
        """Detect macOS system folders"""
        home = Path.home()
        
        folders = {
            'Desktop': home / 'Desktop',
            'Documents': home / 'Documents', 
            'Downloads': home / 'Downloads',
            'Pictures': home / 'Pictures',
            'Movies': home / 'Movies',
            'Videos': home / 'Movies',  # Alias for compatibility
            'Music': home / 'Music'
        }
        
        return folders
    
    def _detect_linux_folders(self) -> Dict[str, Path]:
        """Detect Linux system folders using XDG and fallbacks"""
        home = Path.home()
        folders = {}
        
        # Try XDG user directories first
        xdg_folders = self._get_xdg_folders()
        if xdg_folders:
            folders.update(xdg_folders)
        
        # Ensure we have all required folders with fallbacks
        fallback_folders = {
            'Desktop': home / 'Desktop',
            'Documents': home / 'Documents',
            'Downloads': home / 'Downloads', 
            'Pictures': home / 'Pictures',
            'Videos': home / 'Videos',
            'Music': home / 'Music'
        }
        
        for name, path in fallback_folders.items():
            if name not in folders:
                folders[name] = path
                
        return folders
    
    def _get_xdg_folders(self) -> Dict[str, Path]:
        """Get XDG user directories on Linux"""
        folders = {}
        xdg_dirs = {
            'Desktop': 'DESKTOP',
            'Documents': 'DOCUMENTS',
            'Downloads': 'DOWNLOAD', 
            'Pictures': 'PICTURES',
            'Videos': 'VIDEOS',
            'Music': 'MUSIC'
        }
        
        try:
            import subprocess
            
            for folder_name, xdg_name in xdg_dirs.items():
                try:
                    result = subprocess.run(
                        ['xdg-user-dir', xdg_name],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    
                    if result.returncode == 0:
                        folder_path = Path(result.stdout.strip())
                        if folder_path.is_absolute():  # Valid path
                            folders[folder_name] = folder_path
                            
                except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
                    continue
                    
        except ImportError:
            pass  # subprocess not available
            
        return folders
    
    def _validate_and_fix_folders(self, folders: Dict[str, Path]) -> Dict[str, Path]:
        """Validate folder paths and fix any issues"""
        validated_folders = {}
        home = Path.home()
        
        # Required folders with fallback locations
        required_folders = {
            'Desktop': [home / 'Desktop'],
            'Documents': [home / 'Documents', home / 'My Documents'],
            'Downloads': [home / 'Downloads', home / 'Download'],
            'Pictures': [home / 'Pictures', home / 'Images', home / 'Photos'],
            'Videos': [home / 'Videos', home / 'Movies'],
            'Music': [home / 'Music', home / 'Audio']
        }
        
        for folder_name, fallback_paths in required_folders.items():
            folder_path = None
            
            # First try the detected path
            if folder_name in folders:
                detected_path = folders[folder_name]
                if self._is_valid_folder_path(detected_path):
                    folder_path = detected_path
            
            # If not found, try fallback paths
            if folder_path is None:
                for fallback in fallback_paths:
                    if self._is_valid_folder_path(fallback) or self._can_create_folder(fallback):
                        folder_path = fallback
                        break
            
            # If still not found, use first fallback as default
            if folder_path is None:
                folder_path = fallback_paths[0]
                
            validated_folders[folder_name] = folder_path
            
        return validated_folders
    
    def _is_valid_folder_path(self, path: Path) -> bool:
        """Check if a folder path is valid and accessible"""
        try:
            return path.exists() and path.is_dir() and os.access(path, os.W_OK)
        except (OSError, PermissionError):
            return False
    
    def _can_create_folder(self, path: Path) -> bool:
        """Check if we can create a folder at the given path"""
        try:
            # Check if parent exists and is writable
            parent = path.parent
            return parent.exists() and parent.is_dir() and os.access(parent, os.W_OK)
        except (OSError, PermissionError):
            return False
    
    def ensure_folders_exist(self):
        """Ensure all system folders exist, create them if they don't"""
        for folder_name, folder_path in self.system_folders.items():
            try:
                if not folder_path.exists():
                    folder_path.mkdir(parents=True, exist_ok=True)
                    logging.info(f"Created missing system folder: {folder_path}")
                    
                # Verify we can write to the folder
                if not os.access(folder_path, os.W_OK):
                    logging.warning(f"No write access to {folder_name}: {folder_path}")
                    
            except (OSError, PermissionError) as e:
                logging.error(f"Could not create/access {folder_name} at {folder_path}: {e}")
                
                # Try to find an alternative location
                alternative = self._find_alternative_folder(folder_name, folder_path)
                if alternative:
                    logging.info(f"Using alternative location for {folder_name}: {alternative}")
                    self.system_folders[folder_name] = alternative
    
    def _find_alternative_folder(self, folder_name: str, original_path: Path) -> Optional[Path]:
        """Find an alternative location for a system folder"""
        home = Path.home()
        
        alternatives = {
            'Desktop': [home / 'Desktop', home / f'FileOrganizer_{folder_name}'],
            'Documents': [home / 'Documents', home / 'My Documents', home / f'FileOrganizer_{folder_name}'],
            'Downloads': [home / 'Downloads', home / 'Download', home / f'FileOrganizer_{folder_name}'],
            'Pictures': [home / 'Pictures', home / 'Images', home / f'FileOrganizer_{folder_name}'],
            'Videos': [home / 'Videos', home / 'Movies', home / f'FileOrganizer_{folder_name}'],
            'Music': [home / 'Music', home / 'Audio', home / f'FileOrganizer_{folder_name}']
        }
        
        for alt_path in alternatives.get(folder_name, []):
            if alt_path != original_path:
                try:
                    if alt_path.exists() or self._can_create_folder(alt_path):
                        alt_path.mkdir(parents=True, exist_ok=True)
                        if os.access(alt_path, os.W_OK):
                            return alt_path
                except (OSError, PermissionError):
                    continue
                    
        return None
    
    def get_destination_folder(self, category: str) -> Path:
        """Get the destination folder for a file category"""
        category_info = FILE_CATEGORIES.get(category, {})
        folder_spec = category_info.get('folder', 'Downloads')
        
        # Handle nested folder specifications
        if '/' in folder_spec:
            parts = folder_spec.split('/')
            base_folder = parts[0]
            subfolder = '/'.join(parts[1:])
            
            if base_folder in self.system_folders:
                destination = self.system_folders[base_folder] / subfolder
            else:
                # Fallback to Downloads
                destination = self.system_folders['Downloads'] / folder_spec
        else:
            destination = self.system_folders.get(folder_spec, self.system_folders['Downloads'])
        
        # Create destination folder if it doesn't exist
        destination.mkdir(parents=True, exist_ok=True)
        return destination

class DownloadsOrganizer:
    """Organizes downloads folder by moving files to appropriate system folders"""
    
    def __init__(self):
        self.folder_manager = SystemFolderManager()
        self.downloads_path = self.folder_manager.system_folders['Downloads']
        self.organized_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.results = []
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
    def categorize_file(self, file_path: Path) -> Tuple[str, str]:
        """Categorize a file based on its extension"""
        extension = file_path.suffix.lower()
        
        # Special handling for common compound extensions
        if file_path.name.lower().endswith(('.tar.gz', '.tar.bz2', '.tar.xz')):
            extension = '.' + file_path.name.lower().split('.', 1)[1]
        
        for category, info in FILE_CATEGORIES.items():
            if extension in info['extensions']:
                return category, info['icon']
        
        # Default category for unknown files
        return 'unknown', '❓'
    
    def is_recently_downloaded(self, file_path: Path, hours: int = 24) -> bool:
        """Check if file was downloaded recently"""
        try:
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            time_diff = datetime.now() - file_time
            return time_diff.total_seconds() < (hours * 3600)
        except:
            return True  # If we can't determine, assume it's recent
    
    def get_unique_filename(self, destination: Path, filename: str) -> Path:
        """Generate a unique filename if the destination already exists"""
        base_path = destination / filename
        
        if not base_path.exists():
            return base_path
        
        name_part = Path(filename).stem
        ext_part = Path(filename).suffix
        counter = 1
        
        while True:
            new_name = f"{name_part} ({counter}){ext_part}"
            new_path = destination / new_name
            
            if not new_path.exists():
                return new_path
                
            counter += 1
            
            # Prevent infinite loops
            if counter > 1000:
                break
        
        return base_path
    
    def verify_file_move(self, source_path: Path, destination_path: Path) -> bool:
        """Verify that a file was successfully moved from source to destination"""
        try:
            # Check 1: Destination file exists
            if not destination_path.exists():
                print(f"DEBUG: Verification failed - destination file does not exist: {destination_path}")
                return False
            
            # Check 2: Source file no longer exists
            if source_path.exists():
                print(f"DEBUG: Verification failed - source file still exists: {source_path}")
                return False
            
            # Check 3: Destination file is actually a file (not directory)
            if not destination_path.is_file():
                print(f"DEBUG: Verification failed - destination is not a file: {destination_path}")
                return False
            
            # Check 4: Destination file has reasonable size (> 0 bytes)
            try:
                file_size = destination_path.stat().st_size
                if file_size == 0:
                    print(f"DEBUG: Warning - destination file has 0 bytes: {destination_path}")
                    # Don't fail for 0-byte files as they might be legitimate
                
                print(f"DEBUG: Verification passed - file moved successfully, size: {file_size} bytes")
                return True
                
            except OSError as e:
                print(f"DEBUG: Verification failed - cannot stat destination file: {e}")
                return False
            
        except Exception as e:
            print(f"DEBUG: Verification failed with exception: {e}")
            return False
    
    def diagnose_move_failure(self, source_path: Path, destination_path: Path) -> str:
        """Diagnose why a file move verification failed"""
        diagnostics = []
        
        try:
            # Check source file status
            if source_path.exists():
                diagnostics.append(f"source file still exists at {source_path}")
            else:
                diagnostics.append("source file was removed")
            
            # Check destination file status
            if destination_path.exists():
                if destination_path.is_file():
                    file_size = destination_path.stat().st_size
                    diagnostics.append(f"destination file exists with size {file_size} bytes")
                else:
                    diagnostics.append("destination exists but is not a file")
            else:
                diagnostics.append(f"destination file missing at {destination_path}")
            
            # Check destination directory
            dest_dir = destination_path.parent
            if dest_dir.exists():
                if os.access(dest_dir, os.W_OK):
                    diagnostics.append("destination directory is writable")
                else:
                    diagnostics.append("destination directory is not writable")
            else:
                diagnostics.append("destination directory does not exist")
            
        except Exception as e:
            diagnostics.append(f"diagnostic error: {e}")
        
        return "; ".join(diagnostics)
    
    def organize_downloads(self, 
                         recent_only: bool = False,
                         dry_run: bool = False,
                         exclude_patterns: List[str] = None) -> Dict:
        """Organize files in downloads folder"""
        
        if exclude_patterns is None:
            # Only exclude files that are clearly temporary/incomplete downloads
            exclude_patterns = ['.tmp', '.crdownload', '.download']
            # Note: Removed '.part' as it might be part of legitimate filenames
        
        results = {
            'moved_files': [],
            'skipped_files': [],
            'error_files': [],
            'categories_used': set(),
            'dry_run': dry_run
        }
        
        if not self.downloads_path.exists():
            self.logger.error(f"Downloads folder not found: {self.downloads_path}")
            return results
        
        # Get all files in downloads folder (non-recursive by default)
        try:
            all_items = list(self.downloads_path.iterdir())
            files = [f for f in all_items if f.is_file() and not f.name.startswith('.')]
            folders = [f for f in all_items if f.is_dir() and not f.name.startswith('.')]
            
            print(f"DEBUG: Downloads folder contains {len(all_items)} total items")
            print(f"DEBUG: Found {len(files)} files and {len(folders)} folders")
            print(f"DEBUG: First 10 files: {[f.name for f in files[:10]]}")
            
        except PermissionError as e:
            self.logger.error(f"Permission denied accessing downloads: {e}")
            return results
        
        print(f"DEBUG: Processing {len(files)} files from downloads")
        
        for file_path in files:
            try:
                print(f"DEBUG: Processing file: {file_path}")
                
                # Skip files that match exclude patterns (check file endings, not just contains)
                should_skip = False
                for pattern in exclude_patterns:
                    if file_path.name.lower().endswith(pattern.lower()):
                        print(f"DEBUG: Skipping {file_path.name} - ends with exclude pattern '{pattern}'")
                        should_skip = True
                        break
                
                if should_skip:
                    results['skipped_files'].append({
                        'file': str(file_path),
                        'reason': f'Excluded pattern (temp/incomplete file)'
                    })
                    continue
                
                # Skip recently modified files if recent_only is True
                if recent_only and not self.is_recently_downloaded(file_path):
                    results['skipped_files'].append({
                        'file': str(file_path),
                        'reason': 'Not recent'
                    })
                    continue
                
                # Categorize the file
                category, icon = self.categorize_file(file_path)
                print(f"DEBUG: File {file_path.name} categorized as: {category}")
                
                if category == 'unknown':
                    print(f"DEBUG: Skipping {file_path.name} - unknown file type")
                    results['skipped_files'].append({
                        'file': str(file_path),
                        'reason': 'Unknown file type'
                    })
                    continue
                
                # Get destination folder
                destination_folder = self.folder_manager.get_destination_folder(category)
                destination_path = self.get_unique_filename(destination_folder, file_path.name)
                print(f"DEBUG: Destination for {category}: {destination_folder}")
                
                # Record the planned move
                move_info = {
                    'source': str(file_path),
                    'destination': str(destination_path),
                    'category': category,
                    'icon': icon,
                    'size': file_path.stat().st_size
                }
                
                if dry_run:
                    # Just record what would be done
                    results['moved_files'].append(move_info)
                    results['categories_used'].add(category)
                else:
                    # Actually move the file
                    print(f"DEBUG: Moving {file_path} to {destination_path}")
                    
                    try:
                        # Perform the move
                        shutil.move(str(file_path), str(destination_path))
                        
                        # Small delay to ensure file system operations complete
                        import time
                        time.sleep(0.1)
                        
                        # Verify the move was successful
                        move_successful = self.verify_file_move(file_path, destination_path)
                        
                        if move_successful:
                            self.logger.info(f"Moved {file_path.name} to {destination_folder}")
                            print(f"DEBUG: Successfully moved and verified {file_path.name}")
                            
                            results['moved_files'].append(move_info)
                            results['categories_used'].add(category)
                            self.organized_count += 1
                        else:
                            # Move failed verification - try to diagnose the issue
                            diagnostic_info = self.diagnose_move_failure(file_path, destination_path)
                            
                            error_info = {
                                'file': str(file_path),
                                'error': f'File move verification failed - {diagnostic_info}'
                            }
                            results['error_files'].append(error_info)
                            self.logger.error(f"Move verification failed for {file_path.name}: {diagnostic_info}")
                            print(f"DEBUG: VERIFICATION FAILED for {file_path.name}: {diagnostic_info}")
                            self.error_count += 1
                            
                    except Exception as move_error:
                        # Move operation itself failed
                        error_info = {
                            'file': str(file_path),
                            'error': f'Move operation failed: {str(move_error)}'
                        }
                        results['error_files'].append(error_info)
                        self.logger.error(f"Failed to move {file_path.name}: {move_error}")
                        print(f"DEBUG: MOVE FAILED for {file_path.name}: {move_error}")
                        self.error_count += 1
                
            except Exception as e:
                error_info = {
                    'file': str(file_path),
                    'error': str(e)
                }
                results['error_files'].append(error_info)
                self.logger.error(f"Error processing {file_path}: {e}")
                self.error_count += 1
        
        return results
    
    def create_report(self, results: Dict) -> str:
        """Create a human-readable report of the organization results"""
        report_lines = []
        
        if results['dry_run']:
            report_lines.append("📋 DOWNLOADS ORGANIZATION PREVIEW")
            report_lines.append("=" * 50)
            report_lines.append("(This is a dry run - no files were actually moved)")
        else:
            report_lines.append("📁 DOWNLOADS ORGANIZATION REPORT")
            report_lines.append("=" * 50)
        
        moved_files = results['moved_files']
        if moved_files:
            report_lines.append(f"\n✅ Successfully organized {len(moved_files)} files:")
            
            # Group by category
            by_category = {}
            for file_info in moved_files:
                category = file_info['category']
                if category not in by_category:
                    by_category[category] = []
                by_category[category].append(file_info)
            
            for category, files in by_category.items():
                category_info = FILE_CATEGORIES.get(category, {})
                icon = category_info.get('icon', '📁')
                folder_name = category_info.get('folder', 'Unknown')
                
                report_lines.append(f"\n{icon} {category.title()} → {folder_name} ({len(files)} files):")
                
                for file_info in files[:5]:  # Show first 5 files
                    filename = Path(file_info['source']).name
                    size_mb = file_info['size'] / (1024 * 1024)
                    report_lines.append(f"   • {filename} ({size_mb:.1f} MB)")
                
                if len(files) > 5:
                    report_lines.append(f"   ... and {len(files) - 5} more files")
        
        skipped_files = results['skipped_files']
        if skipped_files:
            report_lines.append(f"\n⏭️ Skipped {len(skipped_files)} files:")
            
            # Group by reason
            by_reason = {}
            for file_info in skipped_files:
                reason = file_info['reason']
                if reason not in by_reason:
                    by_reason[reason] = []
                by_reason[reason].append(file_info)
            
            for reason, files in by_reason.items():
                report_lines.append(f"   • {reason}: {len(files)} files")
        
        error_files = results['error_files']
        if error_files:
            report_lines.append(f"\n❌ Errors with {len(error_files)} files:")
            for error_info in error_files[:3]:  # Show first 3 errors
                filename = Path(error_info['file']).name
                report_lines.append(f"   • {filename}: {error_info['error']}")
            
            if len(error_files) > 3:
                report_lines.append(f"   ... and {len(error_files) - 3} more errors")
        
        # Summary
        total_processed = len(moved_files) + len(skipped_files) + len(error_files)
        report_lines.append(f"\n📊 Summary:")
        report_lines.append(f"   Total files processed: {total_processed}")
        report_lines.append(f"   Successfully organized: {len(moved_files)}")
        report_lines.append(f"   Skipped: {len(skipped_files)}")
        report_lines.append(f"   Errors: {len(error_files)}")
        
        if results['categories_used']:
            categories = ', '.join(results['categories_used'])
            report_lines.append(f"   Categories used: {categories}")
        
        return '\n'.join(report_lines)

def main():
    """Main function for testing the downloads organizer"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Organize Downloads folder by file type')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview what would be done without actually moving files')
    parser.add_argument('--recent-only', action='store_true',
                       help='Only organize recently downloaded files (last 24 hours)')
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create organizer and run
    organizer = DownloadsOrganizer()
    
    print("🗂️ Downloads Folder Organizer")
    print("=" * 40)
    print(f"Downloads path: {organizer.downloads_path}")
    
    if args.dry_run:
        print("Running in DRY RUN mode - no files will be moved")
    
    print("\nScanning downloads folder...")
    
    try:
        results = organizer.organize_downloads(
            recent_only=args.recent_only,
            dry_run=args.dry_run
        )
        
        # Print report
        report = organizer.create_report(results)
        print("\n" + report)
        
        if args.dry_run and results['moved_files']:
            print("\n💡 Run without --dry-run to actually organize the files")
        
    except Exception as e:
        print(f"❌ Error organizing downloads: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())