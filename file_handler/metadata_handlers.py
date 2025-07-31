# filehandler/metadata_handlers.py
import os
import logging
from typing import Tuple, Optional

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


def get_image_size(file_path: str) -> Tuple[int, int]:
    """Get the dimensions of an image file."""
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


def get_file_metadata(file_path: str) -> dict:
    """Get comprehensive metadata for a file."""
    metadata = {
        'size': 0,
        'type': 'unknown',
        'additional': {}
    }
    
    try:
        # Get file size
        metadata['size'] = os.path.getsize(file_path)
        
        # Get file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        # Determine file type and extract specific metadata
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            metadata['type'] = 'image'
            try:
                width, height = get_image_size(file_path)
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
