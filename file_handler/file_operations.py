# file_handler/file_operations.py
import os
import shutil
import logging
from hashlib import sha256, md5
from typing import Union, Dict, List, Optional
from pathlib import Path

# GPU acceleration imports
try:
    from .gpu_hasher import hash_file_fast, GPUHasher
    from .gpu_acceleration import get_gpu_accelerator
    HAS_GPU_SUPPORT = True
except ImportError:
    HAS_GPU_SUPPORT = False

logger = logging.getLogger(__name__)


# Move files from the source folder to the destination folder
def move_file(src, dest):
    """Move a file while preserving timestamps"""
    # Get timestamps before moving the file
    stat_info = os.stat(src)
    shutil.move(src, dest)
    # Preserve timestamps after move
    os.utime(dest, (stat_info.st_atime, stat_info.st_mtime))


# Preserve the timestamps of the files from the source folder to the destination folder
def preserve_timestamps(src, dest):
    """Preserve file timestamps from source to destination"""
    stat_info = os.stat(src)
    os.utime(dest, (stat_info.st_atime, stat_info.st_mtime))


# Calculate the SHA256 hash of a file (legacy function - maintained for compatibility)
def calculate_file_hash(file_path):
    """
    Calculate SHA256 hash of a file (legacy function)
    
    Note: This function is maintained for backward compatibility.
    For new code, use calculate_file_hash_advanced() for GPU acceleration.
    """
    try:
        with open(file_path, "rb") as file:
            file_hash = sha256(file.read()).hexdigest()
        return file_hash
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        raise


def calculate_file_hash_advanced(file_path: Union[str, Path], 
                                algorithm: str = 'sha256',
                                use_gpu: bool = True,
                                chunk_size_mb: int = 64) -> str:
    """
    Calculate file hash with GPU acceleration support
    
    Args:
        file_path: Path to the file
        algorithm: Hash algorithm ('sha256', 'md5', 'both')
        use_gpu: Whether to use GPU acceleration if available
        chunk_size_mb: Chunk size for processing large files
    
    Returns:
        Hash string (or dict if algorithm='both')
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If unsupported algorithm specified
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if algorithm not in ['sha256', 'md5', 'both']:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    # Use GPU acceleration if available and enabled
    if use_gpu and HAS_GPU_SUPPORT:
        try:
            algorithms = ['sha256', 'md5'] if algorithm == 'both' else [algorithm]
            result = hash_file_fast(file_path, algorithms, use_gpu=True)
            
            if result.error:
                logger.warning(f"GPU hashing failed: {result.error}, falling back to CPU")
                return _calculate_hash_cpu(file_path, algorithm, chunk_size_mb)
            
            if algorithm == 'both':
                return {'sha256': result.sha256, 'md5': result.md5}
            elif algorithm == 'sha256':
                return result.sha256
            else:  # md5
                return result.md5
                
        except Exception as e:
            logger.warning(f"GPU hashing error: {e}, falling back to CPU")
            return _calculate_hash_cpu(file_path, algorithm, chunk_size_mb)
    
    # CPU fallback
    return _calculate_hash_cpu(file_path, algorithm, chunk_size_mb)


def _calculate_hash_cpu(file_path: Path, algorithm: str, chunk_size_mb: int) -> Union[str, Dict[str, str]]:
    """Calculate file hash using CPU processing"""
    chunk_size = chunk_size_mb * 1024 * 1024
    
    try:
        hashers = {}
        if algorithm in ['sha256', 'both']:
            hashers['sha256'] = sha256()
        if algorithm in ['md5', 'both']:
            hashers['md5'] = md5()
        
        with open(file_path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                
                for hasher in hashers.values():
                    hasher.update(chunk)
        
        results = {name: hasher.hexdigest() for name, hasher in hashers.items()}
        
        if algorithm == 'both':
            return results
        else:
            return results[algorithm]
            
    except Exception as e:
        logger.error(f"CPU hash calculation failed for {file_path}: {e}")
        raise


def calculate_hashes_batch(file_paths: List[Union[str, Path]], 
                          algorithms: List[str] = None,
                          use_gpu: bool = True,
                          progress_callback: Optional[callable] = None) -> List[Dict]:
    """
    Calculate hashes for multiple files with GPU acceleration
    
    Args:
        file_paths: List of file paths to process
        algorithms: Hash algorithms to compute (['sha256'], ['md5'], or ['sha256', 'md5'])
        use_gpu: Whether to use GPU acceleration
        progress_callback: Optional callback for progress updates
    
    Returns:
        List of dictionaries with file paths and hash results
    """
    if algorithms is None:
        algorithms = ['sha256']
    
    results = []
    
    # Use GPU batch processing if available
    if use_gpu and HAS_GPU_SUPPORT:
        try:
            hasher = GPUHasher()
            gpu_results = hasher.hash_files_batch(file_paths, algorithms, progress_callback)
            
            # Convert to standardized format
            for result in gpu_results:
                result_dict = {
                    'file_path': result.file_path,
                    'file_size': result.file_size,
                    'gpu_accelerated': result.gpu_accelerated,
                    'processing_time': result.compute_time,
                    'error': result.error
                }
                
                # Add hash results
                for alg in algorithms:
                    hash_value = getattr(result, alg, None)
                    result_dict[alg] = hash_value
                
                results.append(result_dict)
                
            return results
            
        except Exception as e:
            logger.warning(f"Batch GPU hashing failed: {e}, falling back to CPU")
    
    # CPU fallback - process files sequentially
    total_files = len(file_paths)
    for i, file_path in enumerate(file_paths):
        try:
            file_path = Path(file_path)
            file_size = file_path.stat().st_size if file_path.exists() else 0
            
            if len(algorithms) > 1:
                hash_result = calculate_file_hash_advanced(file_path, 'both', use_gpu=False)
            else:
                hash_result = calculate_file_hash_advanced(file_path, algorithms[0], use_gpu=False)
            
            result_dict = {
                'file_path': str(file_path),
                'file_size': file_size,
                'gpu_accelerated': False,
                'processing_time': 0.0,  # Not measured in CPU fallback
                'error': None
            }
            
            # Add hash results
            if isinstance(hash_result, dict):
                result_dict.update(hash_result)
            else:
                result_dict[algorithms[0]] = hash_result
            
            results.append(result_dict)
            
            # Progress callback
            if progress_callback:
                progress_callback(i + 1, total_files, result_dict)
                
        except Exception as e:
            error_result = {
                'file_path': str(file_path),
                'file_size': 0,
                'gpu_accelerated': False,
                'processing_time': 0.0,
                'error': str(e)
            }
            for alg in algorithms:
                error_result[alg] = None
            
            results.append(error_result)
            logger.error(f"Error processing {file_path}: {e}")
    
    return results


def find_duplicate_files_advanced(directory: Union[str, Path],
                                 recursive: bool = True,
                                 algorithm: str = 'sha256',
                                 use_gpu: bool = True,
                                 progress_callback: Optional[callable] = None) -> Dict[str, List[str]]:
    """
    Find duplicate files using GPU-accelerated hashing
    
    Args:
        directory: Directory to scan
        recursive: Whether to scan subdirectories
        algorithm: Hash algorithm to use
        use_gpu: Whether to use GPU acceleration
        progress_callback: Optional progress callback
    
    Returns:
        Dictionary mapping hash -> list of file paths with that hash
    """
    if HAS_GPU_SUPPORT and use_gpu:
        try:
            from .gpu_hasher import find_duplicate_files
            return find_duplicate_files(directory, recursive, [algorithm], progress_callback)
        except Exception as e:
            logger.warning(f"GPU duplicate detection failed: {e}, falling back to CPU")
    
    # CPU fallback
    directory = Path(directory)
    
    # Find all files
    if recursive:
        files = list(directory.rglob('*'))
    else:
        files = list(directory.glob('*'))
    
    files = [f for f in files if f.is_file()]
    
    # Calculate hashes
    hash_results = calculate_hashes_batch(files, [algorithm], use_gpu=False, progress_callback=progress_callback)
    
    # Group by hash
    hash_to_files = {}
    for result in hash_results:
        if result['error']:
            continue
        
        file_hash = result.get(algorithm)
        if file_hash:
            if file_hash not in hash_to_files:
                hash_to_files[file_hash] = []
            hash_to_files[file_hash].append(result['file_path'])
    
    # Return only duplicates
    duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}
    return duplicates


def get_gpu_status() -> Dict[str, any]:
    """Get current GPU acceleration status"""
    status = {
        'gpu_support_available': HAS_GPU_SUPPORT,
        'gpu_initialized': False,
        'backend': 'none',
        'device_name': 'none',
        'memory_usage': (0, 0)
    }
    
    if HAS_GPU_SUPPORT:
        try:
            gpu_accelerator = get_gpu_accelerator()
            status['gpu_initialized'] = gpu_accelerator.is_available()
            
            if gpu_accelerator.is_available():
                device = gpu_accelerator.get_device_info()
                status['backend'] = device.backend.value
                status['device_name'] = device.name
                status['memory_usage'] = gpu_accelerator.get_memory_usage()
                
        except Exception as e:
            logger.warning(f"Error getting GPU status: {e}")
    
    return status


# Backward compatibility aliases
def sha256_hash(file_path):
    """Backward compatibility wrapper for SHA256 hashing"""
    return calculate_file_hash(file_path)


def hash_file(file_path, algorithm='sha256'):
    """Backward compatibility wrapper with algorithm selection"""
    return calculate_file_hash_advanced(file_path, algorithm, use_gpu=True)
