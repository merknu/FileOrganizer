# file_handler/metadata_handlers.py
import os
import logging
from typing import Tuple, Optional, Dict, Any, Union
from pathlib import Path

# Image handling
try:
    from PIL import Image
except ImportError:
    Image = None
    logging.warning("Pillow not installed. Image metadata extraction disabled.")

# Audio handling
try:
    from mutagen import File as MutagenFile
except ImportError:
    MutagenFile = None
    logging.warning("Mutagen not installed. Audio metadata extraction disabled.")

# Document handling
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None
    logging.warning("pypdf not installed. PDF metadata extraction disabled.")

try:
    from docx import Document
except ImportError:
    Document = None
    logging.warning("python-docx not installed. DOCX metadata extraction disabled.")

# Video handling
try:
    from moviepy.editor import VideoFileClip
except ImportError:
    VideoFileClip = None
    logging.warning("moviepy not installed. Video metadata extraction disabled.")

# GPU acceleration imports
try:
    from .gpu_image_processor import extract_image_metadata_fast, GPUImageProcessor
    from .gpu_acceleration import get_gpu_accelerator
    HAS_GPU_IMAGE_SUPPORT = True
except ImportError:
    HAS_GPU_IMAGE_SUPPORT = False


def get_image_size(file_path: str, use_gpu: bool = True) -> Tuple[int, int]:
    """
    Get the dimensions of an image file with optional GPU acceleration.
    
    Args:
        file_path: Path to the image file
        use_gpu: Whether to use GPU acceleration if available
    
    Returns:
        Tuple of (width, height)
    """
    # Try GPU acceleration first if available
    if use_gpu and HAS_GPU_IMAGE_SUPPORT:
        try:
            metadata = extract_image_metadata_fast(file_path, use_gpu=True)
            if not metadata.error and metadata.width > 0 and metadata.height > 0:
                return (metadata.width, metadata.height)
        except Exception as e:
            logging.warning(f"GPU image size extraction failed: {e}, falling back to CPU")
    
    # CPU fallback
    if Image is None:
        raise ImportError("Pillow is required for image processing")
    
    try:
        with Image.open(file_path) as img:
            return img.size
    except Exception as e:
        logging.error(f"Error getting image size for {file_path}: {e}")
        raise


def get_audio_duration(file_path: str) -> Optional[float]:
    """Get the duration of an audio file in seconds."""
    if MutagenFile is None:
        raise ImportError("Mutagen is required for audio processing")
    
    try:
        audio = MutagenFile(file_path)
        if audio is not None and audio.info:
            return audio.info.length
        return None
    except Exception as e:
        logging.error(f"Error getting audio duration for {file_path}: {e}")
        return None


def get_document_word_count(file_path: str) -> int:
    """Get the word count of a document."""
    ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if ext == '.pdf' and PdfReader:
            return _get_pdf_word_count(file_path)
        elif ext in ['.docx', '.doc'] and Document:
            return _get_docx_word_count(file_path)
        elif ext == '.txt':
            return _get_txt_word_count(file_path)
        else:
            logging.warning(f"Unsupported document format: {ext}")
            return 0
    except Exception as e:
        logging.error(f"Error getting word count for {file_path}: {e}")
        return 0


def _get_pdf_word_count(file_path: str) -> int:
    """Extract word count from PDF files."""
    word_count = 0
    try:
        with open(file_path, 'rb') as file:
            reader = PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    word_count += len(text.split())
    except Exception as e:
        logging.error(f"Error reading PDF {file_path}: {e}")
    return word_count


def _get_docx_word_count(file_path: str) -> int:
    """Extract word count from DOCX files."""
    word_count = 0
    try:
        doc = Document(file_path)
        for paragraph in doc.paragraphs:
            word_count += len(paragraph.text.split())
    except Exception as e:
        logging.error(f"Error reading DOCX {file_path}: {e}")
    return word_count


def _get_txt_word_count(file_path: str) -> int:
    """Extract word count from text files."""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            text = file.read()
            return len(text.split())
    except Exception as e:
        logging.error(f"Error reading text file {file_path}: {e}")
        return 0


def get_video_duration(file_path: str) -> Optional[float]:
    """Get the duration of a video file in seconds."""
    if VideoFileClip is None:
        raise ImportError("moviepy is required for video processing")
    
    try:
        with VideoFileClip(file_path) as video:
            return video.duration
    except Exception as e:
        logging.error(f"Error getting video duration for {file_path}: {e}")
        return None


def get_file_metadata(file_path: str, use_gpu: bool = True) -> dict:
    """
    Get comprehensive metadata for a file with optional GPU acceleration.
    
    Args:
        file_path: Path to the file
        use_gpu: Whether to use GPU acceleration for supported file types
    
    Returns:
        Dictionary with metadata information
    """
    metadata = {
        'size': 0,
        'type': 'unknown',
        'additional': {},
        'gpu_accelerated': False
    }
    
    try:
        # Get file size
        metadata['size'] = os.path.getsize(file_path)
        
        # Get file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        # Determine file type and extract specific metadata
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic', '.heif']:
            metadata['type'] = 'image'
            
            # Try GPU-accelerated image metadata extraction
            if use_gpu and HAS_GPU_IMAGE_SUPPORT:
                try:
                    gpu_metadata = extract_image_metadata_fast(file_path, use_gpu=True)
                    if not gpu_metadata.error:
                        metadata['gpu_accelerated'] = gpu_metadata.gpu_accelerated
                        metadata['additional'] = {
                            'width': gpu_metadata.width,
                            'height': gpu_metadata.height,
                            'resolution': f"{gpu_metadata.width}x{gpu_metadata.height}",
                            'format': gpu_metadata.format,
                            'mode': gpu_metadata.mode,
                            'has_exif': gpu_metadata.has_exif,
                            'orientation': gpu_metadata.orientation,
                            'processing_time': gpu_metadata.processing_time
                        }
                        
                        # Add EXIF data if available
                        if gpu_metadata.creation_date:
                            metadata['additional']['creation_date'] = gpu_metadata.creation_date
                        if gpu_metadata.camera_make:
                            metadata['additional']['camera_make'] = gpu_metadata.camera_make
                        if gpu_metadata.camera_model:
                            metadata['additional']['camera_model'] = gpu_metadata.camera_model
                        if gpu_metadata.gps_coords:
                            metadata['additional']['gps_coords'] = gpu_metadata.gps_coords
                        
                        return metadata  # Early return if GPU processing succeeded
                        
                except Exception as e:
                    logging.warning(f"GPU image metadata extraction failed: {e}, falling back to CPU")
            
            # CPU fallback for images
            try:
                width, height = get_image_size(file_path, use_gpu=False)
                metadata['additional'] = {
                    'width': width,
                    'height': height,
                    'resolution': f"{width}x{height}"
                }
            except Exception:
                pass
                
        elif ext in ['.mp3', '.wav', '.flac', '.m4a', '.ogg']:
            metadata['type'] = 'audio'
            try:
                duration = get_audio_duration(file_path)
                if duration:
                    metadata['additional'] = {
                        'duration': duration,
                        'duration_formatted': f"{int(duration//60)}:{int(duration%60):02d}"
                    }
            except Exception:
                pass
                
        elif ext in ['.pdf', '.doc', '.docx', '.txt']:
            metadata['type'] = 'document'
            try:
                word_count = get_document_word_count(file_path)
                metadata['additional'] = {'word_count': word_count}
            except Exception:
                pass
                
        elif ext in ['.mp4', '.avi', '.mov', '.mkv', '.wmv']:
            metadata['type'] = 'video'
            try:
                duration = get_video_duration(file_path)
                if duration:
                    metadata['additional'] = {
                        'duration': duration,
                        'duration_formatted': f"{int(duration//60)}:{int(duration%60):02d}"
                    }
            except Exception:
                pass
                
    except Exception as e:
        logging.error(f"Error getting metadata for {file_path}: {e}")
    
    return metadata


def extract_batch_metadata(file_paths: list, 
                          use_gpu: bool = True,
                          progress_callback: Optional[callable] = None) -> Dict[str, Dict]:
    """
    Extract metadata for multiple files with GPU acceleration
    
    Args:
        file_paths: List of file paths to process
        use_gpu: Whether to use GPU acceleration
        progress_callback: Optional progress callback function
    
    Returns:
        Dictionary mapping file paths to their metadata
    """
    results = {}
    image_files = []
    other_files = []
    
    # Separate image files for batch GPU processing
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.heic', '.heif'}
    
    for file_path in file_paths:
        ext = Path(file_path).suffix.lower()
        if ext in image_extensions:
            image_files.append(file_path)
        else:
            other_files.append(file_path)
    
    # Process images with GPU batch processing if available
    if image_files and use_gpu and HAS_GPU_IMAGE_SUPPORT:
        try:
            processor = GPUImageProcessor()
            batch_results = processor.process_images_batch(
                image_files, 
                extract_metadata=True,
                generate_thumbnails=False,
                progress_callback=progress_callback
            )
            
            # Convert GPU results to standard metadata format
            for result in batch_results:
                if hasattr(result, 'file_path'):
                    # Single metadata result
                    metadata = _convert_gpu_metadata_to_standard(result)
                    results[result.file_path] = metadata
                else:
                    # Batch result with metadata key
                    gpu_meta = result.get('metadata')
                    if gpu_meta:
                        metadata = _convert_gpu_metadata_to_standard(gpu_meta)
                        results[gpu_meta.file_path] = metadata
                        
        except Exception as e:
            logging.warning(f"GPU batch metadata extraction failed: {e}, falling back to individual processing")
            # Fallback to individual processing for images
            for file_path in image_files:
                results[str(file_path)] = get_file_metadata(str(file_path), use_gpu=False)
    else:
        # Process images individually
        for file_path in image_files:
            results[str(file_path)] = get_file_metadata(str(file_path), use_gpu=False)
    
    # Process non-image files individually
    for file_path in other_files:
        results[str(file_path)] = get_file_metadata(str(file_path), use_gpu=False)
        
        if progress_callback:
            progress_callback(len(results), len(file_paths), None)
    
    return results


def _convert_gpu_metadata_to_standard(gpu_metadata) -> Dict[str, Any]:
    """Convert GPU metadata result to standard metadata format"""
    metadata = {
        'size': gpu_metadata.size_bytes,
        'type': 'image',
        'gpu_accelerated': gpu_metadata.gpu_accelerated,
        'additional': {
            'width': gpu_metadata.width,
            'height': gpu_metadata.height,
            'resolution': f"{gpu_metadata.width}x{gpu_metadata.height}",
            'format': gpu_metadata.format,
            'mode': gpu_metadata.mode,
            'has_exif': gpu_metadata.has_exif,
            'orientation': gpu_metadata.orientation,
            'processing_time': gpu_metadata.processing_time
        }
    }
    
    # Add optional EXIF data
    if gpu_metadata.creation_date:
        metadata['additional']['creation_date'] = gpu_metadata.creation_date
    if gpu_metadata.camera_make:
        metadata['additional']['camera_make'] = gpu_metadata.camera_make
    if gpu_metadata.camera_model:
        metadata['additional']['camera_model'] = gpu_metadata.camera_model
    if gpu_metadata.gps_coords:
        metadata['additional']['gps_coords'] = gpu_metadata.gps_coords
    
    return metadata


def get_gpu_metadata_status() -> Dict[str, Any]:
    """Get GPU metadata processing status"""
    status = {
        'gpu_image_support': HAS_GPU_IMAGE_SUPPORT,
        'gpu_available': False,
        'backend': 'none',
        'device_name': 'none'
    }
    
    if HAS_GPU_IMAGE_SUPPORT:
        try:
            gpu_accelerator = get_gpu_accelerator()
            status['gpu_available'] = gpu_accelerator.is_available()
            
            if gpu_accelerator.is_available():
                device = gpu_accelerator.get_device_info()
                status['backend'] = device.backend.value
                status['device_name'] = device.name
                
        except Exception as e:
            logging.warning(f"Error getting GPU metadata status: {e}")
    
    return status
