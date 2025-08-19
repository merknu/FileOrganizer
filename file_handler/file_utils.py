# Path: file_handler/file_utils.py
# This file handles file organization with improved error handling and GPU acceleration
import os
import logging
import json
import time
from collections import defaultdict
from typing import Dict, Any, Optional, Callable, List, Union
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# Standard imports
from .metadata_handlers import (get_image_size, get_audio_duration, get_document_word_count, 
                               get_video_duration, get_file_metadata, extract_batch_metadata)
from .file_operations import (move_file, calculate_file_hash, calculate_file_hash_advanced,
                             calculate_hashes_batch, find_duplicate_files_advanced)

# GPU acceleration imports
try:
    from .gpu_acceleration import get_gpu_accelerator, initialize_gpu_acceleration
    from .gpu_hasher import GPUHasher
    from .gpu_image_processor import GPUImageProcessor
    HAS_GPU_SUPPORT = True
except ImportError:
    HAS_GPU_SUPPORT = False


def load_config(config_file: str) -> Optional[Dict[str, Any]]:
    """Load configuration from a JSON file with improved error handling."""
    try:
        with open(config_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"Configuration file {config_file} not found.")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Configuration file {config_file} is not valid JSON: {e}")
        return None
    except Exception as e:
        logging.error(f"Unexpected error loading config {config_file}: {e}")
        return None


def handle_duplicate(src: str, dest: str, default_action: str, gui_mode: bool = True) -> str:
    """Handle duplicate files with user interaction."""
    try:
        if gui_mode:
            # In GUI mode, use default action to avoid blocking
            logging.info(f"Duplicate file detected in GUI mode: {src} -> {dest}, using default: {default_action}")
            return default_action
        else:
            # Console mode with user input
            action = input(f"Duplicate file detected: {src}\n"
                          f"Destination: {dest}\n"
                          f"Options: (k)eep, (o)verwrite, (r)ename [default: {default_action}]: ")
            return action.lower() if action else default_action
    except (EOFError, KeyboardInterrupt):
        logging.info("User interrupted duplicate handling, using default action")
        return default_action


def organize_by_metadata(file_path: str, ext: str, app_config: Dict[str, Any], 
                        use_gpu: bool = True, metadata_cache: Optional[Dict] = None) -> str:
    """
    Organize files by metadata with GPU acceleration support.
    
    Args:
        file_path: Path to the file
        ext: File extension
        app_config: Application configuration
        use_gpu: Whether to use GPU acceleration
        metadata_cache: Optional metadata cache to avoid recomputation
    
    Returns:
        Subfolder name for organization
    """
    file_categories = app_config.get("file_categories", {})
    document_subfolders = app_config.get("subfolders", {})

    try:
        for category, extensions in file_categories.items():
            if ext in extensions:
                return handle_category(file_path, category, ext, document_subfolders, 
                                     use_gpu, metadata_cache)
    except Exception as e:
        logging.warning(f"Error organizing by metadata for {file_path}: {e}")
    
    return "Others"


def handle_category(file_path: str, category: str, ext: str, document_subfolders: Dict[str, str],
                   use_gpu: bool = True, metadata_cache: Optional[Dict] = None) -> str:
    """
    Handle each file category with GPU acceleration support.
    
    Args:
        file_path: Path to the file
        category: File category (Images, Audio, etc.)
        ext: File extension  
        document_subfolders: Document subfolder mapping
        use_gpu: Whether to use GPU acceleration
        metadata_cache: Optional metadata cache
    
    Returns:
        Subfolder path for organization
    """
    try:
        # Check cache first
        if metadata_cache and file_path in metadata_cache:
            cached_metadata = metadata_cache[file_path]
            return _extract_subfolder_from_metadata(category, cached_metadata, ext, document_subfolders)
        
        if category == "Images":
            try:
                # Use GPU-accelerated image processing if available
                if use_gpu and HAS_GPU_SUPPORT:
                    metadata = get_file_metadata(file_path, use_gpu=True)
                    if metadata.get('gpu_accelerated') and metadata.get('additional'):
                        width = metadata['additional'].get('width', 0)
                        height = metadata['additional'].get('height', 0)
                        if width > 0 and height > 0:
                            return f"Images/{width}x{height}"
                
                # CPU fallback
                width, height = get_image_size(file_path, use_gpu=False)
                return f"Images/{width}x{height}"
            except Exception as e:
                logging.warning(f"Could not get image size for {file_path}: {e}")
                return "Images/Unknown_Size"
                
        elif category == "Audio":
            try:
                duration = int(get_audio_duration(file_path) or 0)
                return f"Audio/{duration}s"
            except Exception as e:
                logging.warning(f"Could not get audio duration for {file_path}: {e}")
                return "Audio/Unknown_Duration"
                
        elif category == "Documents":
            subfolder = document_subfolders.get(ext.lower(), "Other_Documents")
            return f"Documents/{subfolder}"
            
        elif category == "Video":
            try:
                duration = int(get_video_duration(file_path) or 0)
                return f"Video/{duration}s"
            except Exception as e:
                logging.warning(f"Could not get video duration for {file_path}: {e}")
                return "Video/Unknown_Duration"
                
    except Exception as e:
        logging.error(f"Error handling category {category} for {file_path}: {e}")
    
    return category


def _extract_subfolder_from_metadata(category: str, metadata: Dict, ext: str, 
                                    document_subfolders: Dict[str, str]) -> str:
    """Extract subfolder name from cached metadata"""
    try:
        if category == "Images" and metadata.get('additional'):
            width = metadata['additional'].get('width', 0)
            height = metadata['additional'].get('height', 0)
            if width > 0 and height > 0:
                return f"Images/{width}x{height}"
            return "Images/Unknown_Size"
            
        elif category == "Audio" and metadata.get('additional'):
            duration = metadata['additional'].get('duration', 0)
            if duration > 0:
                return f"Audio/{int(duration)}s"
            return "Audio/Unknown_Duration"
            
        elif category == "Documents":
            subfolder = document_subfolders.get(ext.lower(), "Other_Documents")
            return f"Documents/{subfolder}"
            
        elif category == "Video" and metadata.get('additional'):
            duration = metadata['additional'].get('duration', 0)
            if duration > 0:
                return f"Video/{int(duration)}s"
            return "Video/Unknown_Duration"
            
    except Exception:
        pass
    
    return category


def organize_files(folder: str, app_config: Dict[str, Any], recursive: bool = False, 
                  preview_mode: bool = False, callback: Optional[Callable] = None,
                  use_gpu: bool = True, batch_size: int = 100) -> Dict[str, int]:
    """
    Organize files in a given folder with GPU acceleration and improved error handling.
    
    Args:
        folder: Path to the folder to organize
        app_config: Configuration dictionary
        recursive: Whether to process subdirectories
        preview_mode: If True, only preview changes without moving files
        callback: Optional callback function to call after processing each file
        use_gpu: Whether to use GPU acceleration for metadata extraction
        batch_size: Number of files to process in each GPU batch
    
    Returns:
        Dictionary with summary statistics
    """
    if not os.path.exists(folder):
        logging.error(f"Folder does not exist: {folder}")
        return {"error": 1}
    
    if not os.path.isdir(folder):
        logging.error(f"Path is not a directory: {folder}")
        return {"error": 1}
    
    summary = defaultdict(int)
    
    try:
        files = os.listdir(folder)
    except PermissionError:
        logging.error(f"Permission denied accessing folder: {folder}")
        return {"permission_denied": 1}
    except Exception as e:
        logging.error(f"Error listing files in {folder}: {e}")
        return {"error": 1}
    
    for file in files:
        src = os.path.join(folder, file)
        
        try:
            # Handle subdirectories if recursive
            if os.path.isdir(src) and recursive:
                sub_summary = organize_files(src, app_config, recursive, preview_mode, callback)
                for key, value in sub_summary.items():
                    summary[key] += value
                continue
            
            # Skip if not a file
            if not os.path.isfile(src):
                continue
            
            name, ext = os.path.splitext(file)
            ext = ext.lower()
            
            # Skip files without extensions
            if not ext:
                summary['no_extension'] += 1
                continue
            
            # Determine target subfolder
            subfolder = organize_by_metadata(src, ext, app_config, use_gpu=use_gpu)
            target_folder = os.path.join(folder, subfolder)
            
            # Create target directory
            try:
                os.makedirs(target_folder, exist_ok=True)
            except Exception as e:
                logging.error(f"Could not create directory {target_folder}: {e}")
                summary['mkdir_failed'] += 1
                continue
            
            dest = os.path.join(target_folder, file)
            
            # Handle duplicates
            if os.path.exists(dest):
                try:
                    if calculate_file_hash(src) == calculate_file_hash(dest):
                        default_action = app_config.get("default_duplicate_action", "k")
                        # Always use GUI mode when called from GUI
                        action = handle_duplicate(src, dest, default_action, gui_mode=True)
                        
                        if action == "r":
                            base_name, ext = os.path.splitext(file)
                            counter = 1
                            while os.path.exists(dest):
                                new_name = f"{base_name}_copy{counter}{ext}"
                                dest = os.path.join(target_folder, new_name)
                                counter += 1
                        elif action == "k":
                            summary['duplicate_kept'] += 1
                            continue
                except Exception as e:
                    logging.warning(f"Error checking duplicate for {src}: {e}")
                    summary['duplicate_check_failed'] += 1
                    continue
            
            # Move or preview file
            if not preview_mode:
                try:
                    move_file(src, dest)
                    summary['moved'] += 1
                    logging.info(f"Moved {src} to {dest}")
                except Exception as e:
                    summary['move_failed'] += 1
                    logging.error(f"Error moving file {src} to {dest}: {e}")
            else:
                summary['preview'] += 1
                logging.info(f"Preview: {src} would be moved to {dest}")
            
            # Call callback if provided
            if callback:
                try:
                    callback()
                except Exception as e:
                    logging.warning(f"Error in callback: {e}")
                    
        except Exception as e:
            logging.error(f"Error processing file {src}: {e}")
            summary['processing_error'] += 1
    
    return dict(summary)


def organize_files_gpu_accelerated(folder: str, app_config: Dict[str, Any], 
                                   recursive: bool = False, preview_mode: bool = False,
                                   callback: Optional[Callable] = None,
                                   batch_size: int = 100) -> Dict[str, int]:
    """
    GPU-accelerated batch file organization with metadata caching.
    
    This function provides significant performance improvements for large file collections
    by processing files in GPU-accelerated batches and caching metadata.
    
    Args:
        folder: Path to the folder to organize
        app_config: Configuration dictionary
        recursive: Whether to process subdirectories
        preview_mode: If True, only preview changes without moving files
        callback: Optional callback function
        batch_size: Files per GPU batch
    
    Returns:
        Dictionary with summary statistics including GPU performance metrics
    """
    if not os.path.exists(folder):
        logging.error(f"Folder does not exist: {folder}")
        return {"error": 1}
    
    if not os.path.isdir(folder):
        logging.error(f"Path is not a directory: {folder}")
        return {"error": 1}
    
    start_time = time.time()
    summary = defaultdict(int)
    metadata_cache = {}
    
    # Initialize GPU acceleration if available
    gpu_available = False
    if HAS_GPU_SUPPORT:
        try:
            gpu_available = initialize_gpu_acceleration()
            if gpu_available:
                summary['gpu_acceleration_enabled'] = 1
                logging.info("GPU acceleration enabled for file organization")
            else:
                logging.info("GPU acceleration not available, using CPU processing")
        except Exception as e:
            logging.warning(f"GPU initialization failed: {e}")
    
    try:
        # Collect all files first
        all_files = []
        if recursive:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.isfile(file_path):
                        all_files.append(file_path)
        else:
            files = os.listdir(folder)
            for file in files:
                file_path = os.path.join(folder, file)
                if os.path.isfile(file_path):
                    all_files.append(file_path)
        
        summary['total_files_found'] = len(all_files)
        logging.info(f"Found {len(all_files)} files to process")
        
        # Filter files and separate by type for optimal GPU processing
        image_files = []
        other_files = []
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic', '.heif'}
        
        for file_path in all_files:
            name, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            if not ext:
                summary['no_extension'] += 1
                continue
            
            if ext in image_extensions:
                image_files.append(file_path)
            else:
                other_files.append(file_path)
        
        summary['image_files'] = len(image_files)
        summary['other_files'] = len(other_files)
        
        # Process image files in GPU batches if available
        if image_files and gpu_available:
            logging.info(f"Processing {len(image_files)} images with GPU acceleration...")
            try:
                # Extract metadata in batches
                batch_metadata = extract_batch_metadata(
                    image_files, 
                    use_gpu=True,
                    progress_callback=lambda p, t, r: callback() if callback else None
                )
                metadata_cache.update(batch_metadata)
                summary['gpu_metadata_extractions'] = len(batch_metadata)
                
            except Exception as e:
                logging.warning(f"GPU batch processing failed: {e}")
                summary['gpu_batch_failures'] = 1
        
        # Process all files for organization
        processed_count = 0
        for file_path in all_files:
            try:
                # Get relative path for organization
                rel_path = os.path.relpath(file_path, folder)
                if os.path.sep in rel_path:
                    # File is in subdirectory - skip for now in non-recursive mode
                    if not recursive:
                        continue
                    
                    # For recursive mode, organize in the file's current directory
                    current_dir = os.path.dirname(file_path)
                    file_name = os.path.basename(file_path)
                else:
                    current_dir = folder
                    file_name = rel_path
                
                name, ext = os.path.splitext(file_name)
                ext = ext.lower()
                
                if not ext:
                    continue
                
                # Determine target subfolder using cached metadata
                subfolder = organize_by_metadata(
                    file_path, ext, app_config, 
                    use_gpu=False,  # Already processed in batch
                    metadata_cache=metadata_cache
                )
                
                target_folder = os.path.join(current_dir, subfolder)
                
                # Create target directory
                try:
                    os.makedirs(target_folder, exist_ok=True)
                except Exception as e:
                    logging.error(f"Could not create directory {target_folder}: {e}")
                    summary['mkdir_failed'] += 1
                    continue
                
                dest = os.path.join(target_folder, file_name)
                
                # Handle duplicates using GPU-accelerated hashing
                if os.path.exists(dest):
                    try:
                        # Use GPU hashing for duplicate detection if available
                        if gpu_available and os.path.getsize(file_path) > 1024 * 1024:  # > 1MB
                            src_hash = calculate_file_hash_advanced(file_path, use_gpu=True)
                            dest_hash = calculate_file_hash_advanced(dest, use_gpu=True)
                            summary['gpu_hash_comparisons'] += 1
                        else:
                            src_hash = calculate_file_hash(file_path)
                            dest_hash = calculate_file_hash(dest)
                            summary['cpu_hash_comparisons'] += 1
                        
                        if src_hash == dest_hash:
                            default_action = app_config.get("default_duplicate_action", "k")
                            action = handle_duplicate(file_path, dest, default_action, gui_mode=True)
                            
                            if action == "r":
                                base_name, ext = os.path.splitext(file_name)
                                counter = 1
                                while os.path.exists(dest):
                                    new_name = f"{base_name}_copy{counter}{ext}"
                                    dest = os.path.join(target_folder, new_name)
                                    counter += 1
                            elif action == "k":
                                summary['duplicate_kept'] += 1
                                continue
                    except Exception as e:
                        logging.warning(f"Error checking duplicate for {file_path}: {e}")
                        summary['duplicate_check_failed'] += 1
                        continue
                
                # Move or preview file
                if not preview_mode:
                    try:
                        move_file(file_path, dest)
                        summary['moved'] += 1
                        logging.debug(f"Moved {file_path} to {dest}")
                    except Exception as e:
                        summary['move_failed'] += 1
                        logging.error(f"Error moving file {file_path} to {dest}: {e}")
                else:
                    summary['preview'] += 1
                    logging.debug(f"Preview: {file_path} would be moved to {dest}")
                
                processed_count += 1
                
                # Call callback for progress updates
                if callback:
                    try:
                        callback()
                    except Exception as e:
                        logging.warning(f"Error in callback: {e}")
                
                # Progress logging
                if processed_count % 100 == 0:
                    elapsed = time.time() - start_time
                    rate = processed_count / elapsed if elapsed > 0 else 0
                    logging.info(f"Processed {processed_count}/{len(all_files)} files "
                               f"({rate:.1f} files/sec)")
                        
            except Exception as e:
                logging.error(f"Error processing file {file_path}: {e}")
                summary['processing_error'] += 1
        
        # Final statistics
        total_time = time.time() - start_time
        summary['total_processing_time'] = total_time
        summary['processing_rate'] = processed_count / total_time if total_time > 0 else 0
        
        # GPU performance statistics
        if gpu_available and HAS_GPU_SUPPORT:
            try:
                gpu_accelerator = get_gpu_accelerator()
                gpu_stats = gpu_accelerator.get_performance_stats()
                summary['gpu_operations'] = gpu_stats.get('operations_count', 0)
                summary['gpu_processing_time'] = gpu_stats.get('total_processing_time', 0.0)
            except Exception as e:
                logging.warning(f"Could not get GPU statistics: {e}")
        
        logging.info(f"File organization completed in {total_time:.2f} seconds")
        logging.info(f"Processed {processed_count} files at {summary['processing_rate']:.1f} files/sec")
        
    except Exception as e:
        logging.error(f"Error during file organization: {e}")
        summary['fatal_error'] = 1
    
    return dict(summary)


def find_and_organize_duplicates_gpu(directory: Union[str, Path],
                                   recursive: bool = True,
                                   action: str = 'move_to_duplicates',
                                   progress_callback: Optional[Callable] = None) -> Dict[str, Any]:
    """
    Find and organize duplicate files using GPU acceleration.
    
    Args:
        directory: Directory to scan for duplicates
        recursive: Whether to scan subdirectories
        action: What to do with duplicates ('move_to_duplicates', 'delete', 'report_only')
        progress_callback: Optional progress callback
    
    Returns:
        Dictionary with duplicate detection results and statistics
    """
    directory = Path(directory)
    start_time = time.time()
    
    results = {
        'duplicates_found': 0,
        'files_processed': 0,
        'space_wasted': 0,
        'gpu_accelerated': False,
        'processing_time': 0.0,
        'duplicate_groups': {}
    }
    
    try:
        logging.info(f"Scanning {directory} for duplicate files...")
        
        # Use GPU-accelerated duplicate detection
        if HAS_GPU_SUPPORT:
            try:
                duplicates = find_duplicate_files_advanced(
                    directory, recursive=recursive, use_gpu=True, 
                    progress_callback=progress_callback
                )
                results['gpu_accelerated'] = True
                logging.info("Using GPU acceleration for duplicate detection")
            except Exception as e:
                logging.warning(f"GPU duplicate detection failed: {e}")
                duplicates = {}
        else:
            duplicates = {}
        
        # Process duplicate groups
        for file_hash, file_list in duplicates.items():
            if len(file_list) > 1:
                results['duplicates_found'] += len(file_list) - 1
                results['duplicate_groups'][file_hash] = file_list
                
                # Calculate wasted space (size of duplicates)
                try:
                    file_size = os.path.getsize(file_list[0])
                    results['space_wasted'] += file_size * (len(file_list) - 1)
                except:
                    pass
                
                # Perform action on duplicates
                if action == 'move_to_duplicates':
                    duplicates_folder = directory / 'Duplicates'
                    duplicates_folder.mkdir(exist_ok=True)
                    
                    # Keep first file, move others
                    for duplicate_file in file_list[1:]:
                        try:
                            dest_name = f"{Path(duplicate_file).stem}_{file_hash[:8]}{Path(duplicate_file).suffix}"
                            dest_path = duplicates_folder / dest_name
                            shutil.move(duplicate_file, dest_path)
                            logging.info(f"Moved duplicate: {duplicate_file} -> {dest_path}")
                        except Exception as e:
                            logging.error(f"Error moving duplicate {duplicate_file}: {e}")
                
                elif action == 'delete':
                    # Delete all but first file
                    for duplicate_file in file_list[1:]:
                        try:
                            os.remove(duplicate_file)
                            logging.info(f"Deleted duplicate: {duplicate_file}")
                        except Exception as e:
                            logging.error(f"Error deleting duplicate {duplicate_file}: {e}")
        
        results['files_processed'] = sum(len(files) for files in duplicates.values())
        results['processing_time'] = time.time() - start_time
        
        logging.info(f"Duplicate detection completed in {results['processing_time']:.2f} seconds")
        logging.info(f"Found {results['duplicates_found']} duplicate files wasting "
                   f"{results['space_wasted'] / (1024*1024):.1f} MB")
        
    except Exception as e:
        logging.error(f"Error during duplicate detection: {e}")
        results['error'] = str(e)
    
    return results


def get_folder_analysis_gpu(folder: Union[str, Path], 
                           recursive: bool = True) -> Dict[str, Any]:
    """
    Perform GPU-accelerated analysis of a folder's contents.
    
    Args:
        folder: Path to analyze
        recursive: Whether to analyze subdirectories
    
    Returns:
        Dictionary with analysis results
    """
    folder = Path(folder)
    start_time = time.time()
    
    analysis = {
        'total_files': 0,
        'total_size': 0,
        'file_types': defaultdict(int),
        'file_type_sizes': defaultdict(int),
        'largest_files': [],
        'gpu_processed_images': 0,
        'gpu_processing_time': 0.0,
        'analysis_time': 0.0
    }
    
    try:
        # Collect all files
        all_files = []
        if recursive:
            all_files = list(folder.rglob('*'))
        else:
            all_files = list(folder.glob('*'))
        
        all_files = [f for f in all_files if f.is_file()]
        analysis['total_files'] = len(all_files)
        
        # Separate images for GPU batch processing
        image_files = []
        other_files = []
        
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic', '.heif'}
        
        for file_path in all_files:
            ext = file_path.suffix.lower()
            file_size = file_path.stat().st_size
            
            analysis['total_size'] += file_size
            analysis['file_types'][ext] += 1
            analysis['file_type_sizes'][ext] += file_size
            
            # Track largest files
            analysis['largest_files'].append((str(file_path), file_size))
            analysis['largest_files'].sort(key=lambda x: x[1], reverse=True)
            analysis['largest_files'] = analysis['largest_files'][:10]  # Keep top 10
            
            if ext in image_extensions:
                image_files.append(file_path)
            else:
                other_files.append(file_path)
        
        # GPU-accelerated image analysis
        if image_files and HAS_GPU_SUPPORT:
            try:
                gpu_start = time.time()
                
                # Batch process images for metadata
                metadata_results = extract_batch_metadata(image_files, use_gpu=True)
                analysis['gpu_processed_images'] = len(metadata_results)
                
                # Aggregate image statistics
                total_pixels = 0
                total_megapixels = 0
                formats = defaultdict(int)
                
                for file_path, metadata in metadata_results.items():
                    if metadata.get('additional'):
                        width = metadata['additional'].get('width', 0)
                        height = metadata['additional'].get('height', 0)
                        if width > 0 and height > 0:
                            pixels = width * height
                            total_pixels += pixels
                            total_megapixels += pixels / 1_000_000
                        
                        img_format = metadata['additional'].get('format', 'Unknown')
                        formats[img_format] += 1
                
                analysis['image_statistics'] = {
                    'total_images': len(image_files),
                    'total_pixels': total_pixels,
                    'total_megapixels': total_megapixels,
                    'average_megapixels': total_megapixels / len(image_files) if image_files else 0,
                    'formats': dict(formats)
                }
                
                analysis['gpu_processing_time'] = time.time() - gpu_start
                logging.info(f"GPU processed {len(image_files)} images in "
                           f"{analysis['gpu_processing_time']:.2f} seconds")
                
            except Exception as e:
                logging.warning(f"GPU image analysis failed: {e}")
        
        analysis['analysis_time'] = time.time() - start_time
        analysis['file_types'] = dict(analysis['file_types'])
        analysis['file_type_sizes'] = dict(analysis['file_type_sizes'])
        
        logging.info(f"Folder analysis completed in {analysis['analysis_time']:.2f} seconds")
        
    except Exception as e:
        logging.error(f"Error during folder analysis: {e}")
        analysis['error'] = str(e)
    
    return analysis


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration structure."""
    required_keys = ["file_categories", "subfolders", "default_duplicate_action"]
    
    for key in required_keys:
        if key not in config:
            logging.error(f"Missing required config key: {key}")
            return False
    
    return True


# Main execution for testing
if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Load and validate config
    app_config = load_config("../config/config.json")
    if not app_config:
        logging.error("Failed to load configuration")
        exit(1)
    
    if not validate_config(app_config):
        logging.error("Invalid configuration")
        exit(1)
    
    # Test organization (preview mode)
    test_folder = input("Enter folder path to organize (or press Enter to skip): ").strip()
    if test_folder and os.path.exists(test_folder):
        print("Running in preview mode...")
        summary = organize_files(test_folder, app_config, recursive=True, preview_mode=True)
        print("Preview Summary:", dict(summary))
        
        if input("Proceed with actual organization? (y/N): ").lower() == 'y':
            summary = organize_files(test_folder, app_config, recursive=True, preview_mode=False)
            print("Final Summary:", dict(summary))
    else:
        print("Test skipped - no valid folder provided")
