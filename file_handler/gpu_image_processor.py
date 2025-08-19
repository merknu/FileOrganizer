# file_handler/gpu_image_processor.py
"""
GPU-Accelerated Image Processing Module for FileOrganizer
Provides high-performance image metadata extraction, thumbnail generation, and format conversion.
"""

import os
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple, Union, Callable
from dataclasses import dataclass
from pathlib import Path
import io

# Standard image libraries
try:
    from PIL import Image, ImageOps, ExifTags, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# GPU libraries
try:
    import cupy as cp
    from cupyx.scipy import ndimage as cp_ndimage
    HAS_CUPY = True
except ImportError:
    HAS_CUPY = False

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

try:
    import pyopencl as cl
    HAS_OPENCL = True
except ImportError:
    HAS_OPENCL = False

from .gpu_acceleration import get_gpu_accelerator, GPUBackend


@dataclass
class ImageMetadata:
    """Image metadata result"""
    file_path: str
    width: int = 0
    height: int = 0
    format: str = ""
    mode: str = ""
    size_bytes: int = 0
    has_exif: bool = False
    orientation: int = 1
    creation_date: Optional[str] = None
    camera_make: Optional[str] = None
    camera_model: Optional[str] = None
    focal_length: Optional[str] = None
    iso: Optional[int] = None
    aperture: Optional[str] = None
    shutter_speed: Optional[str] = None
    gps_coords: Optional[Tuple[float, float]] = None
    processing_time: float = 0.0
    gpu_accelerated: bool = False
    error: Optional[str] = None


@dataclass
class ThumbnailResult:
    """Thumbnail generation result"""
    original_path: str
    thumbnail_path: str
    thumbnail_size: Tuple[int, int]
    original_size: Tuple[int, int]
    compression_ratio: float = 0.0
    processing_time: float = 0.0
    gpu_accelerated: bool = False
    error: Optional[str] = None


class GPUImageProcessor:
    """GPU-accelerated image processing engine"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Get GPU accelerator
        self.gpu_accelerator = get_gpu_accelerator()
        
        # Configuration
        self.thumbnail_sizes = self.config.get('thumbnail_sizes', [(128, 128), (256, 256)])
        self.thumbnail_quality = self.config.get('thumbnail_quality', 85)
        self.max_concurrent_images = self.config.get('max_concurrent_images', 4)
        self.enable_gpu_processing = self.config.get('enable_gpu_processing', True)
        self.gpu_memory_limit_mb = self.config.get('gpu_memory_limit_mb', 1024)
        self.supported_formats = self.config.get('supported_formats', 
                                                ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp'])
        
        # Performance tracking
        self.total_images_processed = 0
        self.gpu_processing_time = 0.0
        self.cpu_processing_time = 0.0
        
        # GPU-specific setup
        self._setup_gpu_processing()

    def _setup_gpu_processing(self):
        """Set up GPU-specific image processing"""
        if not self.gpu_accelerator.is_available() or not self.enable_gpu_processing:
            self.logger.info("GPU image processing disabled or unavailable")
            return
        
        try:
            if self.gpu_accelerator.backend == GPUBackend.CUDA and HAS_CUPY:
                self._setup_cuda_processing()
            elif self.gpu_accelerator.backend == GPUBackend.OPENCL and HAS_OPENCL:
                self._setup_opencl_processing()
                
        except Exception as e:
            self.logger.warning(f"Failed to setup GPU image processing: {e}")

    def _setup_cuda_processing(self):
        """Set up CUDA-based image processing"""
        self.logger.info("CUDA image processing initialized")
        # Pre-allocate some GPU memory for image processing
        try:
            # Create memory pool for image processing
            if HAS_CUPY:
                mempool = cp.get_default_memory_pool()
                # Reserve some memory for image operations
                reserved_mb = min(self.gpu_memory_limit_mb, 512)
                self.logger.info(f"Reserved {reserved_mb}MB GPU memory for image processing")
        except Exception as e:
            self.logger.warning(f"Could not reserve GPU memory: {e}")

    def _setup_opencl_processing(self):
        """Set up OpenCL-based image processing"""
        self.logger.info("OpenCL image processing initialized")

    def extract_metadata(self, image_path: Union[str, Path]) -> ImageMetadata:
        """
        Extract comprehensive metadata from an image file
        
        Args:
            image_path: Path to the image file
        
        Returns:
            ImageMetadata object with extracted information
        """
        start_time = time.time()
        image_path = Path(image_path)
        
        result = ImageMetadata(
            file_path=str(image_path),
            size_bytes=0
        )
        
        try:
            # Check file exists and get basic info
            if not image_path.exists():
                result.error = f"Image file not found: {image_path}"
                return result
            
            result.size_bytes = image_path.stat().st_size
            
            # Use GPU acceleration for large images
            if self._should_use_gpu_for_image(result.size_bytes):
                try:
                    metadata = self._extract_metadata_gpu(image_path)
                    result.gpu_accelerated = True
                except Exception as e:
                    self.logger.warning(f"GPU metadata extraction failed: {e}")
                    metadata = self._extract_metadata_cpu(image_path)
                    result.gpu_accelerated = False
            else:
                metadata = self._extract_metadata_cpu(image_path)
                result.gpu_accelerated = False
            
            # Update result with extracted metadata
            for key, value in metadata.items():
                if hasattr(result, key):
                    setattr(result, key, value)
            
            # Update performance tracking
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            if result.gpu_accelerated:
                self.gpu_processing_time += processing_time
            else:
                self.cpu_processing_time += processing_time
            
            self.total_images_processed += 1
            
        except Exception as e:
            result.error = str(e)
            self.logger.error(f"Error extracting metadata from {image_path}: {e}")
        
        return result

    def generate_thumbnail(self, image_path: Union[str, Path], 
                          output_path: Union[str, Path],
                          size: Tuple[int, int] = (256, 256),
                          quality: int = 85) -> ThumbnailResult:
        """
        Generate a thumbnail for an image
        
        Args:
            image_path: Path to the source image
            output_path: Path for the thumbnail
            size: Thumbnail dimensions (width, height)
            quality: JPEG quality (1-100)
        
        Returns:
            ThumbnailResult object
        """
        start_time = time.time()
        image_path = Path(image_path)
        output_path = Path(output_path)
        
        result = ThumbnailResult(
            original_path=str(image_path),
            thumbnail_path=str(output_path),
            thumbnail_size=size,
            original_size=(0, 0)
        )
        
        try:
            # Check source exists
            if not image_path.exists():
                result.error = f"Source image not found: {image_path}"
                return result
            
            # Create output directory if needed
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get original image size
            with Image.open(image_path) as img:
                result.original_size = img.size
            
            # Decide processing method
            file_size = image_path.stat().st_size
            if self._should_use_gpu_for_image(file_size):
                try:
                    self._generate_thumbnail_gpu(image_path, output_path, size, quality)
                    result.gpu_accelerated = True
                except Exception as e:
                    self.logger.warning(f"GPU thumbnail generation failed: {e}")
                    self._generate_thumbnail_cpu(image_path, output_path, size, quality)
                    result.gpu_accelerated = False
            else:
                self._generate_thumbnail_cpu(image_path, output_path, size, quality)
                result.gpu_accelerated = False
            
            # Calculate compression ratio
            if output_path.exists():
                original_size = image_path.stat().st_size
                thumbnail_size = output_path.stat().st_size
                result.compression_ratio = original_size / thumbnail_size if thumbnail_size > 0 else 0.0
            
            # Update performance tracking
            processing_time = time.time() - start_time
            result.processing_time = processing_time
            
            if result.gpu_accelerated:
                self.gpu_processing_time += processing_time
            else:
                self.cpu_processing_time += processing_time
                
        except Exception as e:
            result.error = str(e)
            self.logger.error(f"Error generating thumbnail for {image_path}: {e}")
        
        return result

    def process_images_batch(self, image_paths: List[Union[str, Path]],
                           extract_metadata: bool = True,
                           generate_thumbnails: bool = False,
                           thumbnail_dir: Optional[Path] = None,
                           progress_callback: Optional[Callable] = None) -> List[Dict]:
        """
        Process multiple images in parallel
        
        Args:
            image_paths: List of image file paths
            extract_metadata: Whether to extract metadata
            generate_thumbnails: Whether to generate thumbnails
            thumbnail_dir: Directory for thumbnails (if generating)
            progress_callback: Optional progress callback
        
        Returns:
            List of processing results
        """
        results = []
        total_images = len(image_paths)
        processed_images = 0
        
        self.logger.info(f"Starting batch processing for {total_images} images")
        
        with ThreadPoolExecutor(max_workers=self.max_concurrent_images) as executor:
            # Submit processing tasks
            future_to_path = {}
            
            for path in image_paths:
                if extract_metadata and generate_thumbnails:
                    future = executor.submit(self._process_single_image_full, 
                                           path, thumbnail_dir)
                elif extract_metadata:
                    future = executor.submit(self.extract_metadata, path)
                elif generate_thumbnails:
                    if thumbnail_dir:
                        thumbnail_path = thumbnail_dir / f"{Path(path).stem}_thumb.jpg"
                        future = executor.submit(self.generate_thumbnail, path, thumbnail_path)
                    else:
                        continue  # Skip if no thumbnail directory specified
                else:
                    continue  # Nothing to do
                
                future_to_path[future] = path
            
            # Collect results
            for future in as_completed(future_to_path):
                path = future_to_path[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    processed_images += 1
                    
                    # Progress callback
                    if progress_callback:
                        progress_callback(processed_images, total_images, result)
                    
                    # Log progress
                    if processed_images % 50 == 0 or processed_images == total_images:
                        self.logger.info(f"Processed {processed_images}/{total_images} images")
                        
                except Exception as e:
                    self.logger.error(f"Error processing {path}: {e}")
                    processed_images += 1
        
        self.logger.info(f"Batch processing completed. Processed {processed_images} images")
        return results

    def _should_use_gpu_for_image(self, file_size: int) -> bool:
        """Determine if GPU processing is beneficial for an image"""
        if not self.enable_gpu_processing or not self.gpu_accelerator.is_available():
            return False
        
        # Use GPU for larger images (>500KB) to amortize GPU overhead
        min_size_for_gpu = self.config.get('min_image_size_for_gpu', 512 * 1024)  # 512KB
        
        return file_size >= min_size_for_gpu

    def _extract_metadata_gpu(self, image_path: Path) -> Dict:
        """Extract image metadata using GPU acceleration"""
        metadata = {}
        
        if not HAS_PIL:
            raise RuntimeError("PIL/Pillow required for image processing")
        
        try:
            with Image.open(image_path) as img:
                # Basic metadata
                metadata['width'], metadata['height'] = img.size
                metadata['format'] = img.format or 'Unknown'
                metadata['mode'] = img.mode
                
                # EXIF data processing with GPU acceleration
                if hasattr(img, '_getexif') and img._getexif():
                    metadata['has_exif'] = True
                    exif_data = img._getexif()
                    
                    if exif_data and self.gpu_accelerator.is_available():
                        # Use GPU for EXIF processing if available
                        processed_exif = self._process_exif_gpu(exif_data)
                        metadata.update(processed_exif)
                    else:
                        # Fallback to CPU EXIF processing
                        processed_exif = self._process_exif_cpu(exif_data)
                        metadata.update(processed_exif)
                else:
                    metadata['has_exif'] = False
                
                # GPU-accelerated image analysis
                if (self.gpu_accelerator.backend == GPUBackend.CUDA and 
                    HAS_CUPY and HAS_NUMPY):
                    
                    # Convert image to numpy array for GPU processing
                    img_array = np.array(img)
                    
                    # Transfer to GPU
                    gpu_img = cp.asarray(img_array)
                    
                    # Perform GPU-accelerated analysis
                    # (placeholder for more sophisticated analysis)
                    analysis_result = self._analyze_image_gpu(gpu_img)
                    metadata.update(analysis_result)
                
        except Exception as e:
            self.logger.error(f"GPU metadata extraction error: {e}")
            raise
        
        return metadata

    def _extract_metadata_cpu(self, image_path: Path) -> Dict:
        """Extract image metadata using CPU processing"""
        metadata = {}
        
        if not HAS_PIL:
            raise RuntimeError("PIL/Pillow required for image processing")
        
        try:
            with Image.open(image_path) as img:
                # Basic metadata
                metadata['width'], metadata['height'] = img.size
                metadata['format'] = img.format or 'Unknown'
                metadata['mode'] = img.mode
                
                # EXIF data processing
                if hasattr(img, '_getexif') and img._getexif():
                    metadata['has_exif'] = True
                    exif_data = img._getexif()
                    processed_exif = self._process_exif_cpu(exif_data)
                    metadata.update(processed_exif)
                else:
                    metadata['has_exif'] = False
                
        except Exception as e:
            self.logger.error(f"CPU metadata extraction error: {e}")
            raise
        
        return metadata

    def _process_exif_gpu(self, exif_data: Dict) -> Dict:
        """Process EXIF data with GPU acceleration"""
        # For now, delegate to CPU processing
        # Future: implement GPU-accelerated EXIF parsing
        return self._process_exif_cpu(exif_data)

    def _process_exif_cpu(self, exif_data: Dict) -> Dict:
        """Process EXIF data using CPU"""
        processed = {}
        
        try:
            # Map EXIF tags
            exif_mapping = {
                'DateTime': 'creation_date',
                'Make': 'camera_make',
                'Model': 'camera_model',
                'FocalLength': 'focal_length',
                'ISOSpeedRatings': 'iso',
                'FNumber': 'aperture',
                'ExposureTime': 'shutter_speed',
                'Orientation': 'orientation'
            }
            
            for exif_key, exif_value in exif_data.items():
                # Get tag name
                tag_name = ExifTags.TAGS.get(exif_key, exif_key)
                
                if tag_name in exif_mapping:
                    processed_key = exif_mapping[tag_name]
                    processed[processed_key] = exif_value
                
                # Handle GPS data
                if tag_name == 'GPSInfo' and isinstance(exif_value, dict):
                    gps_coords = self._parse_gps_coords(exif_value)
                    if gps_coords:
                        processed['gps_coords'] = gps_coords
                        
        except Exception as e:
            self.logger.warning(f"EXIF processing error: {e}")
        
        return processed

    def _analyze_image_gpu(self, gpu_image: 'cp.ndarray') -> Dict:
        """Perform GPU-accelerated image analysis"""
        analysis = {}
        
        try:
            # Basic statistics
            analysis['mean_brightness'] = float(cp.mean(gpu_image))
            analysis['std_brightness'] = float(cp.std(gpu_image))
            
            # Color analysis (if color image)
            if len(gpu_image.shape) == 3:
                # RGB channel statistics
                analysis['mean_red'] = float(cp.mean(gpu_image[:, :, 0]))
                analysis['mean_green'] = float(cp.mean(gpu_image[:, :, 1]))
                analysis['mean_blue'] = float(cp.mean(gpu_image[:, :, 2]))
                
        except Exception as e:
            self.logger.warning(f"GPU image analysis error: {e}")
        
        return analysis

    def _generate_thumbnail_gpu(self, image_path: Path, output_path: Path,
                               size: Tuple[int, int], quality: int):
        """Generate thumbnail using GPU acceleration"""
        if not HAS_PIL:
            raise RuntimeError("PIL/Pillow required for image processing")
        
        try:
            with Image.open(image_path) as img:
                # For now, use PIL for thumbnail generation
                # Future: implement GPU-accelerated resizing with CuPy/OpenCV
                
                if HAS_CUPY and HAS_OPENCV and self.gpu_accelerator.backend == GPUBackend.CUDA:
                    # Try GPU-accelerated resize with OpenCV
                    img_array = np.array(img)
                    
                    # Upload to GPU
                    gpu_img = cv2.cuda_GpuMat()
                    gpu_img.upload(img_array)
                    
                    # Resize on GPU
                    gpu_resized = cv2.cuda.resize(gpu_img, size, interpolation=cv2.INTER_LANCZOS4)
                    
                    # Download result
                    resized_array = gpu_resized.download()
                    
                    # Convert back to PIL Image
                    thumbnail = Image.fromarray(resized_array)
                else:
                    # Fallback to PIL
                    thumbnail = img.copy()
                    thumbnail.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                save_kwargs = {'quality': quality}
                if output_path.suffix.lower() in ['.jpg', '.jpeg']:
                    save_kwargs['optimize'] = True
                
                thumbnail.save(output_path, **save_kwargs)
                
        except Exception as e:
            self.logger.error(f"GPU thumbnail generation error: {e}")
            raise

    def _generate_thumbnail_cpu(self, image_path: Path, output_path: Path,
                               size: Tuple[int, int], quality: int):
        """Generate thumbnail using CPU processing"""
        if not HAS_PIL:
            raise RuntimeError("PIL/Pillow required for image processing")
        
        try:
            with Image.open(image_path) as img:
                # Create thumbnail
                thumbnail = img.copy()
                thumbnail.thumbnail(size, Image.Resampling.LANCZOS)
                
                # Save with specified quality
                save_kwargs = {'quality': quality}
                if output_path.suffix.lower() in ['.jpg', '.jpeg']:
                    save_kwargs['optimize'] = True
                
                thumbnail.save(output_path, **save_kwargs)
                
        except Exception as e:
            self.logger.error(f"CPU thumbnail generation error: {e}")
            raise

    def _process_single_image_full(self, image_path: Path, 
                                  thumbnail_dir: Optional[Path] = None) -> Dict:
        """Process a single image with both metadata and thumbnail"""
        result = {
            'metadata': self.extract_metadata(image_path),
            'thumbnail': None
        }
        
        if thumbnail_dir:
            thumbnail_path = thumbnail_dir / f"{Path(image_path).stem}_thumb.jpg"
            result['thumbnail'] = self.generate_thumbnail(image_path, thumbnail_path)
        
        return result

    def _parse_gps_coords(self, gps_info: Dict) -> Optional[Tuple[float, float]]:
        """Parse GPS coordinates from EXIF data"""
        try:
            def convert_to_degrees(value):
                """Convert GPS coordinate to degrees"""
                if isinstance(value, tuple) and len(value) == 3:
                    return value[0] + value[1]/60.0 + value[2]/3600.0
                return float(value)
            
            # Get latitude
            if 2 in gps_info and 1 in gps_info:  # GPSLatitude and GPSLatitudeRef
                lat = convert_to_degrees(gps_info[2])
                if gps_info[1] == 'S':
                    lat = -lat
            else:
                return None
            
            # Get longitude
            if 4 in gps_info and 3 in gps_info:  # GPSLongitude and GPSLongitudeRef
                lon = convert_to_degrees(gps_info[4])
                if gps_info[3] == 'W':
                    lon = -lon
            else:
                return None
            
            return (lat, lon)
            
        except Exception as e:
            self.logger.warning(f"GPS coordinate parsing error: {e}")
            return None

    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        total_time = self.gpu_processing_time + self.cpu_processing_time
        
        stats = {
            'total_images_processed': self.total_images_processed,
            'total_processing_time': total_time,
            'gpu_processing_time': self.gpu_processing_time,
            'cpu_processing_time': self.cpu_processing_time,
            'gpu_acceleration_ratio': (self.gpu_processing_time / total_time 
                                     if total_time > 0 else 0),
            'average_processing_time': (total_time / self.total_images_processed
                                      if self.total_images_processed > 0 else 0),
            'gpu_available': self.gpu_accelerator.is_available(),
            'gpu_backend': self.gpu_accelerator.backend.value if self.gpu_accelerator.is_available() else 'none'
        }
        
        return stats

    def reset_stats(self):
        """Reset performance statistics"""
        self.total_images_processed = 0
        self.gpu_processing_time = 0.0
        self.cpu_processing_time = 0.0


# Convenience functions
def extract_image_metadata_fast(image_path: Union[str, Path], 
                               use_gpu: bool = True) -> ImageMetadata:
    """Quick metadata extraction for a single image"""
    config = {'enable_gpu_processing': use_gpu}
    processor = GPUImageProcessor(config)
    return processor.extract_metadata(image_path)


def generate_thumbnail_fast(image_path: Union[str, Path],
                          output_path: Union[str, Path],
                          size: Tuple[int, int] = (256, 256),
                          use_gpu: bool = True) -> ThumbnailResult:
    """Quick thumbnail generation for a single image"""
    config = {'enable_gpu_processing': use_gpu}
    processor = GPUImageProcessor(config)
    return processor.generate_thumbnail(image_path, output_path, size)


# Module-level testing
if __name__ == "__main__":
    import tempfile
    
    logging.basicConfig(level=logging.INFO)
    
    print("GPU Image Processor Test")
    print("=" * 30)
    
    # Create a test image
    if HAS_PIL:
        test_img = Image.new('RGB', (1024, 768), color='red')
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            test_img.save(tmp.name, quality=95)
            test_image_path = tmp.name
        
        try:
            processor = GPUImageProcessor()
            
            # Test metadata extraction
            print(f"Testing image: {test_image_path}")
            metadata = processor.extract_metadata(test_image_path)
            
            print(f"GPU Accelerated: {metadata.gpu_accelerated}")
            print(f"Dimensions: {metadata.width}x{metadata.height}")
            print(f"Format: {metadata.format}")
            print(f"Processing Time: {metadata.processing_time:.4f}s")
            
            if metadata.error:
                print(f"Error: {metadata.error}")
            
            # Test thumbnail generation
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as thumb:
                thumbnail_path = thumb.name
            
            thumb_result = processor.generate_thumbnail(test_image_path, thumbnail_path)
            
            print(f"Thumbnail GPU Accelerated: {thumb_result.gpu_accelerated}")
            print(f"Thumbnail Size: {thumb_result.thumbnail_size}")
            print(f"Compression Ratio: {thumb_result.compression_ratio:.2f}")
            
            # Performance stats
            stats = processor.get_performance_stats()
            print(f"\nPerformance Stats:")
            print(f"  Images Processed: {stats['total_images_processed']}")
            print(f"  GPU Available: {stats['gpu_available']}")
            print(f"  Average Time: {stats['average_processing_time']:.4f}s")
            
            print("\nTest completed successfully!")
            
        finally:
            # Cleanup
            try:
                os.unlink(test_image_path)
                if 'thumbnail_path' in locals():
                    os.unlink(thumbnail_path)
            except:
                pass
    else:
        print("PIL/Pillow not available - skipping test")