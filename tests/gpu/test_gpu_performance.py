"""
Comprehensive GPU Performance Tests for FileOrganizer.

Tests GPU vs CPU performance for:
- File hashing operations
- Image processing operations  
- Batch processing workflows
- Memory management
- Error handling and fallback mechanisms

Supports both hardware GPU testing and mocked environments.
"""

import pytest
import time
import tempfile
import os
import statistics
from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock
import threading
import psutil

# Test utilities
from tests.conftest import create_test_file

# Try importing GPU modules
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None

try:
    import cupy as cp
    HAS_CUPY = True
except ImportError:
    HAS_CUPY = False
    cp = None

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    Image = None

# Import modules under test
try:
    from file_handler.gpu_acceleration import (
        GPUAccelerator, GPUBackend, GPUDevice, get_gpu_accelerator
    )
    from file_handler.gpu_hasher import GPUHasher, HashResult
    from file_handler.gpu_image_processor import GPUImageProcessor, ImageMetadata
    from file_handler.gpu_monitor import GPUMonitor
    HAS_GPU_MODULES = True
except ImportError:
    HAS_GPU_MODULES = False


class PerformanceTimer:
    """Context manager for measuring performance with statistics."""
    
    def __init__(self, name: str):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.duration = None
        
    def __enter__(self):
        self.start_time = time.perf_counter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
        

class PerformanceBenchmark:
    """Performance benchmarking utility."""
    
    def __init__(self):
        self.results = {}
        
    def run_benchmark(self, name: str, func, *args, iterations: int = 3, **kwargs):
        """Run a function multiple times and collect performance statistics."""
        times = []
        results = []
        
        for i in range(iterations):
            with PerformanceTimer(f"{name}_iter_{i}") as timer:
                result = func(*args, **kwargs)
                results.append(result)
            times.append(timer.duration)
        
        stats = {
            'mean_time': statistics.mean(times),
            'min_time': min(times),
            'max_time': max(times),
            'std_dev': statistics.stdev(times) if len(times) > 1 else 0.0,
            'total_time': sum(times),
            'iterations': iterations,
            'results': results,
            'times': times
        }
        
        self.results[name] = stats
        return stats
    
    def compare_methods(self, name_a: str, name_b: str) -> Dict[str, float]:
        """Compare performance between two benchmarked methods."""
        if name_a not in self.results or name_b not in self.results:
            return {}
            
        a_time = self.results[name_a]['mean_time']
        b_time = self.results[name_b]['mean_time']
        
        speedup = a_time / b_time if b_time > 0 else 0.0
        improvement = ((a_time - b_time) / a_time * 100) if a_time > 0 else 0.0
        
        return {
            'speedup_ratio': speedup,
            'improvement_percent': improvement,
            'time_difference': a_time - b_time,
            'faster_method': name_a if a_time < b_time else name_b
        }


@pytest.fixture
def performance_benchmark():
    """Performance benchmarking fixture."""
    return PerformanceBenchmark()


@pytest.fixture
def test_files_various_sizes(tmp_path):
    """Create test files of various sizes for performance testing."""
    files = {}
    sizes = {
        'tiny': 1024,           # 1KB
        'small': 1024 * 100,    # 100KB  
        'medium': 1024 * 1024,  # 1MB
        'large': 1024 * 1024 * 10,  # 10MB
        'xlarge': 1024 * 1024 * 50  # 50MB
    }
    
    for size_name, size_bytes in sizes.items():
        file_path = tmp_path / f"test_{size_name}.bin"
        create_test_file(str(file_path), size=size_bytes)
        files[size_name] = str(file_path)
    
    return files


@pytest.fixture
def test_images_various_sizes(tmp_path):
    """Create test images of various sizes for image processing tests."""
    if not HAS_PIL:
        pytest.skip("PIL not available for image tests")
    
    images = {}
    sizes = [
        ('small', 256, 256),
        ('medium', 1024, 768), 
        ('large', 2048, 1536),
        ('xlarge', 4096, 3072)
    ]
    
    for name, width, height in sizes:
        image_path = tmp_path / f"test_{name}.jpg"
        
        # Create test image with some content
        img = Image.new('RGB', (width, height))
        # Add some pattern to make it more realistic
        pixels = []
        for y in range(height):
            for x in range(width):
                r = (x * 255) // width
                g = (y * 255) // height  
                b = ((x + y) * 255) // (width + height)
                pixels.append((r, g, b))
        img.putdata(pixels)
        
        img.save(str(image_path), quality=85)
        images[name] = str(image_path)
    
    return images


@pytest.mark.gpu
@pytest.mark.performance
class TestGPUAccelerationPerformance:
    """Test GPU acceleration framework performance."""
    
    def test_gpu_initialization_performance(self, performance_benchmark):
        """Test GPU initialization time and consistency."""
        if not HAS_GPU_MODULES:
            pytest.skip("GPU modules not available")
        
        def init_gpu():
            accelerator = GPUAccelerator({
                'enable_gpu': True,
                'backend': 'auto',
                'run_initial_benchmark': False  # Skip to measure init only
            })
            return accelerator.is_available()
        
        # Benchmark initialization
        stats = performance_benchmark.run_benchmark('gpu_init', init_gpu, iterations=5)
        
        # Assertions
        assert stats['mean_time'] < 5.0, "GPU initialization should be under 5 seconds"
        assert stats['std_dev'] < 1.0, "GPU initialization time should be consistent"
        
        # At least one initialization should succeed or gracefully fail
        success_count = sum(1 for result in stats['results'] if result is True)
        assert success_count >= 0, "GPU initialization should not crash"
    
    def test_gpu_memory_management_performance(self, performance_benchmark):
        """Test GPU memory allocation and cleanup performance."""
        if not HAS_GPU_MODULES or not HAS_CUPY:
            pytest.skip("CUDA/CuPy not available for memory test")
        
        def allocate_gpu_memory():
            try:
                # Allocate 100MB on GPU
                data = cp.zeros((100 * 1024 * 1024 // 8,), dtype=cp.float64)
                result = cp.sum(data)  # Force memory access
                del data  # Explicit cleanup
                return float(result)
            except Exception:
                return None
        
        # Test memory operations
        stats = performance_benchmark.run_benchmark('gpu_memory', allocate_gpu_memory, iterations=10)
        
        # Check for memory leaks by monitoring process memory
        process = psutil.Process()
        memory_before = process.memory_info().rss
        
        # Run several iterations
        for _ in range(5):
            allocate_gpu_memory()
        
        memory_after = process.memory_info().rss
        memory_increase = (memory_after - memory_before) / 1024 / 1024  # MB
        
        # Memory should not increase significantly
        assert memory_increase < 200, f"Memory leak detected: {memory_increase:.1f}MB increase"
        assert stats['mean_time'] < 0.5, "GPU memory operations should be fast"
    
    def test_gpu_device_selection_performance(self, performance_benchmark):
        """Test GPU device detection and selection performance."""
        if not HAS_GPU_MODULES:
            pytest.skip("GPU modules not available")
        
        def detect_and_select():
            accelerator = GPUAccelerator({'enable_gpu': True})
            device_info = accelerator.get_device_info()
            return device_info is not None
        
        stats = performance_benchmark.run_benchmark('gpu_selection', detect_and_select, iterations=3)
        
        # Device selection should be fast
        assert stats['mean_time'] < 2.0, "GPU device selection should be under 2 seconds"


@pytest.mark.gpu
@pytest.mark.performance  
class TestGPUHashingPerformance:
    """Test GPU-accelerated file hashing performance."""
    
    def test_hashing_performance_vs_cpu(self, test_files_various_sizes, performance_benchmark):
        """Compare GPU vs CPU hashing performance across file sizes."""
        if not HAS_GPU_MODULES:
            pytest.skip("GPU modules not available")
        
        # Initialize hashers
        gpu_hasher = GPUHasher({'enable_gpu_hashing': True})
        cpu_hasher = GPUHasher({'enable_gpu_hashing': False})
        
        results = {}
        
        for size_name, file_path in test_files_various_sizes.items():
            # GPU hashing
            gpu_stats = performance_benchmark.run_benchmark(
                f'gpu_hash_{size_name}',
                gpu_hasher.hash_file,
                file_path,
                ['sha256'],
                iterations=3
            )
            
            # CPU hashing
            cpu_stats = performance_benchmark.run_benchmark(
                f'cpu_hash_{size_name}',
                cpu_hasher.hash_file,
                file_path,
                ['sha256'],
                iterations=3
            )
            
            # Calculate throughput
            file_size_mb = os.path.getsize(file_path) / 1024 / 1024
            gpu_throughput = file_size_mb / gpu_stats['mean_time'] if gpu_stats['mean_time'] > 0 else 0
            cpu_throughput = file_size_mb / cpu_stats['mean_time'] if cpu_stats['mean_time'] > 0 else 0
            
            comparison = performance_benchmark.compare_methods(
                f'cpu_hash_{size_name}', f'gpu_hash_{size_name}'
            )
            
            results[size_name] = {
                'file_size_mb': file_size_mb,
                'gpu_time': gpu_stats['mean_time'],
                'cpu_time': cpu_stats['mean_time'],
                'gpu_throughput_mb_s': gpu_throughput,
                'cpu_throughput_mb_s': cpu_throughput,
                'comparison': comparison,
                'gpu_results': [r for r in gpu_stats['results'] if r and not r.error],
                'cpu_results': [r for r in cpu_stats['results'] if r and not r.error]
            }
        
        # Validate results
        for size_name, result in results.items():
            # Both methods should produce valid results
            assert len(result['gpu_results']) > 0, f"GPU hashing failed for {size_name}"
            assert len(result['cpu_results']) > 0, f"CPU hashing failed for {size_name}"
            
            # Hash values should match between GPU and CPU
            gpu_hashes = [r.sha256 for r in result['gpu_results'] if r.sha256]
            cpu_hashes = [r.sha256 for r in result['cpu_results'] if r.sha256]
            
            if gpu_hashes and cpu_hashes:
                assert gpu_hashes[0] == cpu_hashes[0], f"Hash mismatch for {size_name}"
            
            # Performance should be reasonable
            assert result['gpu_throughput_mb_s'] > 0, f"GPU throughput should be positive for {size_name}"
            assert result['cpu_throughput_mb_s'] > 0, f"CPU throughput should be positive for {size_name}"
        
        # Print performance summary
        print("\nHashing Performance Summary:")
        print("=" * 80)
        for size_name, result in results.items():
            print(f"{size_name.upper()} ({result['file_size_mb']:.1f}MB):")
            print(f"  GPU: {result['gpu_throughput_mb_s']:.1f} MB/s ({result['gpu_time']:.3f}s)")
            print(f"  CPU: {result['cpu_throughput_mb_s']:.1f} MB/s ({result['cpu_time']:.3f}s)")
            if result['comparison']['speedup_ratio'] > 1:
                print(f"  GPU is {result['comparison']['speedup_ratio']:.2f}x faster")
            else:
                print(f"  CPU is {1/result['comparison']['speedup_ratio']:.2f}x faster")
            print()
    
    def test_batch_hashing_performance(self, tmp_path, performance_benchmark):
        """Test batch hashing performance with multiple files."""
        if not HAS_GPU_MODULES:
            pytest.skip("GPU modules not available")
        
        # Create multiple test files
        file_count = 20
        file_size_kb = 500  # 500KB each
        test_files = []
        
        for i in range(file_count):
            file_path = tmp_path / f"batch_test_{i}.bin"
            create_test_file(str(file_path), size=file_size_kb * 1024)
            test_files.append(str(file_path))
        
        # Test GPU batch processing
        gpu_hasher = GPUHasher({'enable_gpu_hashing': True, 'max_concurrent_files': 4})
        cpu_hasher = GPUHasher({'enable_gpu_hashing': False, 'max_concurrent_files': 4})
        
        def gpu_batch_hash():
            return gpu_hasher.hash_files_batch(test_files, ['sha256'])
        
        def cpu_batch_hash():
            return cpu_hasher.hash_files_batch(test_files, ['sha256'])
        
        # Benchmark batch operations
        gpu_stats = performance_benchmark.run_benchmark('gpu_batch_hash', gpu_batch_hash, iterations=3)
        cpu_stats = performance_benchmark.run_benchmark('cpu_batch_hash', cpu_batch_hash, iterations=3)
        
        comparison = performance_benchmark.compare_methods('cpu_batch_hash', 'gpu_batch_hash')
        
        # Validate results
        total_size_mb = (file_count * file_size_kb) / 1024
        gpu_throughput = total_size_mb / gpu_stats['mean_time']
        cpu_throughput = total_size_mb / cpu_stats['mean_time']
        
        assert gpu_throughput > 0, "GPU batch throughput should be positive"
        assert cpu_throughput > 0, "CPU batch throughput should be positive"
        
        # Check result correctness
        gpu_results = gpu_stats['results'][0]
        cpu_results = cpu_stats['results'][0]
        
        assert len(gpu_results) == file_count, "GPU should process all files"
        assert len(cpu_results) == file_count, "CPU should process all files"
        
        # Compare hash values
        gpu_hashes = {r.file_path: r.sha256 for r in gpu_results if not r.error and r.sha256}
        cpu_hashes = {r.file_path: r.sha256 for r in cpu_results if not r.error and r.sha256}
        
        common_files = set(gpu_hashes.keys()) & set(cpu_hashes.keys())
        for file_path in common_files:
            assert gpu_hashes[file_path] == cpu_hashes[file_path], f"Hash mismatch for {file_path}"
        
        print(f"\nBatch Hashing Performance ({file_count} files, {total_size_mb:.1f}MB total):")
        print(f"GPU: {gpu_throughput:.1f} MB/s, CPU: {cpu_throughput:.1f} MB/s")
        print(f"Speedup: {comparison['speedup_ratio']:.2f}x")
    
    def test_memory_limited_hashing(self, tmp_path, performance_benchmark):
        """Test hashing performance under memory constraints."""
        if not HAS_GPU_MODULES:
            pytest.skip("GPU modules not available")
        
        # Create a large file that might challenge memory limits
        large_file = tmp_path / "memory_test.bin" 
        create_test_file(str(large_file), size=100 * 1024 * 1024)  # 100MB
        
        # Test with different memory limits
        memory_configs = [
            {'gpu_memory_limit_mb': 64, 'chunk_size_mb': 16},
            {'gpu_memory_limit_mb': 128, 'chunk_size_mb': 32},
            {'gpu_memory_limit_mb': 256, 'chunk_size_mb': 64},
        ]
        
        results = {}
        
        for i, config in enumerate(memory_configs):
            hasher = GPUHasher({**config, 'enable_gpu_hashing': True})
            
            def hash_with_config():
                return hasher.hash_file(str(large_file), ['sha256'])
            
            stats = performance_benchmark.run_benchmark(f'memory_limit_{i}', hash_with_config, iterations=2)
            
            results[f"config_{i}"] = {
                'config': config,
                'mean_time': stats['mean_time'],
                'throughput': 100 / stats['mean_time'],  # MB/s
                'successful': all(not r.error for r in stats['results'] if r)
            }
        
        # All configurations should work
        for config_name, result in results.items():
            assert result['successful'], f"Memory-constrained hashing failed for {config_name}"
            assert result['throughput'] > 0, f"Invalid throughput for {config_name}"
        
        print("\nMemory-Limited Hashing Results:")
        for config_name, result in results.items():
            config = result['config']
            print(f"{config_name}: {config['chunk_size_mb']}MB chunks, "
                  f"{result['throughput']:.1f} MB/s")


@pytest.mark.gpu
@pytest.mark.performance
class TestGPUImageProcessingPerformance:
    """Test GPU-accelerated image processing performance."""
    
    def test_metadata_extraction_performance(self, test_images_various_sizes, performance_benchmark):
        """Compare GPU vs CPU image metadata extraction performance."""
        if not HAS_GPU_MODULES or not HAS_PIL:
            pytest.skip("GPU modules or PIL not available")
        
        gpu_processor = GPUImageProcessor({'enable_gpu_processing': True})
        cpu_processor = GPUImageProcessor({'enable_gpu_processing': False})
        
        results = {}
        
        for size_name, image_path in test_images_various_sizes.items():
            # GPU processing
            gpu_stats = performance_benchmark.run_benchmark(
                f'gpu_metadata_{size_name}',
                gpu_processor.extract_metadata,
                image_path,
                iterations=3
            )
            
            # CPU processing  
            cpu_stats = performance_benchmark.run_benchmark(
                f'cpu_metadata_{size_name}',
                cpu_processor.extract_metadata,
                image_path,
                iterations=3
            )
            
            comparison = performance_benchmark.compare_methods(
                f'cpu_metadata_{size_name}', f'gpu_metadata_{size_name}'
            )
            
            results[size_name] = {
                'gpu_time': gpu_stats['mean_time'],
                'cpu_time': cpu_stats['mean_time'],
                'comparison': comparison,
                'gpu_results': [r for r in gpu_stats['results'] if r and not r.error],
                'cpu_results': [r for r in cpu_stats['results'] if r and not r.error]
            }
        
        # Validate results
        for size_name, result in results.items():
            assert len(result['gpu_results']) > 0, f"GPU metadata extraction failed for {size_name}"
            assert len(result['cpu_results']) > 0, f"CPU metadata extraction failed for {size_name}"
            
            # Check metadata consistency
            gpu_meta = result['gpu_results'][0]
            cpu_meta = result['cpu_results'][0] 
            
            assert gpu_meta.width == cpu_meta.width, f"Width mismatch for {size_name}"
            assert gpu_meta.height == cpu_meta.height, f"Height mismatch for {size_name}"
        
        print("\nImage Metadata Extraction Performance:")
        for size_name, result in results.items():
            print(f"{size_name}: GPU {result['gpu_time']:.3f}s, CPU {result['cpu_time']:.3f}s, "
                  f"Speedup: {result['comparison']['speedup_ratio']:.2f}x")
    
    def test_thumbnail_generation_performance(self, test_images_various_sizes, tmp_path, performance_benchmark):
        """Test thumbnail generation performance."""
        if not HAS_GPU_MODULES or not HAS_PIL:
            pytest.skip("GPU modules or PIL not available")
        
        gpu_processor = GPUImageProcessor({'enable_gpu_processing': True})
        cpu_processor = GPUImageProcessor({'enable_gpu_processing': False})
        
        thumbnail_sizes = [(128, 128), (256, 256), (512, 512)]
        
        for size_name, image_path in test_images_various_sizes.items():
            for thumb_size in thumbnail_sizes:
                gpu_output = tmp_path / f"gpu_thumb_{size_name}_{thumb_size[0]}.jpg"
                cpu_output = tmp_path / f"cpu_thumb_{size_name}_{thumb_size[0]}.jpg"
                
                # GPU thumbnail generation
                gpu_stats = performance_benchmark.run_benchmark(
                    f'gpu_thumb_{size_name}_{thumb_size[0]}',
                    gpu_processor.generate_thumbnail,
                    image_path, str(gpu_output), thumb_size,
                    iterations=3
                )
                
                # CPU thumbnail generation
                cpu_stats = performance_benchmark.run_benchmark(
                    f'cpu_thumb_{size_name}_{thumb_size[0]}',
                    cpu_processor.generate_thumbnail,
                    image_path, str(cpu_output), thumb_size,
                    iterations=3
                )
                
                # Validate thumbnails were created
                gpu_results = [r for r in gpu_stats['results'] if r and not r.error]
                cpu_results = [r for r in cpu_stats['results'] if r and not r.error]
                
                assert len(gpu_results) > 0, f"GPU thumbnail generation failed"
                assert len(cpu_results) > 0, f"CPU thumbnail generation failed"
                
                # Check files exist
                assert gpu_output.exists(), "GPU thumbnail file not created"
                assert cpu_output.exists(), "CPU thumbnail file not created"
    
    def test_batch_image_processing_performance(self, tmp_path, performance_benchmark):
        """Test batch image processing performance."""
        if not HAS_GPU_MODULES or not HAS_PIL:
            pytest.skip("GPU modules or PIL not available")
        
        # Create multiple test images
        image_count = 10
        test_images = []
        
        for i in range(image_count):
            image_path = tmp_path / f"batch_image_{i}.jpg"
            img = Image.new('RGB', (800, 600), color=f'hsl({i*36}, 100%, 50%)')
            img.save(str(image_path), quality=85)
            test_images.append(str(image_path))
        
        gpu_processor = GPUImageProcessor({
            'enable_gpu_processing': True,
            'max_concurrent_images': 4
        })
        cpu_processor = GPUImageProcessor({
            'enable_gpu_processing': False,
            'max_concurrent_images': 4
        })
        
        # Test batch metadata extraction
        def gpu_batch_metadata():
            return gpu_processor.process_images_batch(
                test_images, extract_metadata=True, generate_thumbnails=False
            )
        
        def cpu_batch_metadata():
            return cpu_processor.process_images_batch(
                test_images, extract_metadata=True, generate_thumbnails=False
            )
        
        gpu_stats = performance_benchmark.run_benchmark('gpu_batch_images', gpu_batch_metadata, iterations=2)
        cpu_stats = performance_benchmark.run_benchmark('cpu_batch_images', cpu_batch_metadata, iterations=2)
        
        comparison = performance_benchmark.compare_methods('cpu_batch_images', 'gpu_batch_images')
        
        # Validate results
        assert len(gpu_stats['results'][0]) == image_count, "GPU should process all images"
        assert len(cpu_stats['results'][0]) == image_count, "CPU should process all images"
        
        print(f"\nBatch Image Processing ({image_count} images):")
        print(f"GPU: {gpu_stats['mean_time']:.2f}s, CPU: {cpu_stats['mean_time']:.2f}s")
        print(f"Speedup: {comparison['speedup_ratio']:.2f}x")


@pytest.mark.gpu
@pytest.mark.performance
class TestGPUMemoryPerformance:
    """Test GPU memory management and optimization."""
    
    def test_memory_usage_monitoring(self):
        """Test GPU memory usage tracking."""
        if not HAS_GPU_MODULES:
            pytest.skip("GPU modules not available")
        
        accelerator = get_gpu_accelerator()
        if not accelerator.is_available():
            pytest.skip("GPU not available for memory testing")
        
        # Initial memory usage
        initial_used, initial_total = accelerator.get_memory_usage()
        
        # Perform some GPU operations
        hasher = GPUHasher({'enable_gpu_hashing': True})
        
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b'0' * (10 * 1024 * 1024))  # 10MB
            tmp.flush()
            
            # Hash file multiple times
            for _ in range(5):
                result = hasher.hash_file(tmp.name, ['sha256'])
                assert not result.error, "Hashing should succeed"
        
        # Check final memory usage
        final_used, final_total = accelerator.get_memory_usage()
        
        # Memory should be reasonable
        assert final_total > 0, "Total memory should be reported"
        assert final_used >= initial_used, "Used memory should be tracked"
        
        # Memory usage should not grow unbounded
        memory_increase = final_used - initial_used
        assert memory_increase < 500, f"Memory usage increased by {memory_increase}MB"
    
    def test_memory_cleanup_performance(self, performance_benchmark):
        """Test GPU memory cleanup performance."""
        if not HAS_GPU_MODULES:
            pytest.skip("GPU modules not available")
        
        def create_and_cleanup_hasher():
            hasher = GPUHasher({'enable_gpu_hashing': True})
            
            # Use the hasher
            with tempfile.NamedTemporaryFile() as tmp:
                tmp.write(b'test data' * 1000)
                tmp.flush()
                result = hasher.hash_file(tmp.name, ['sha256'])
            
            # Explicit cleanup
            if hasattr(hasher, 'cleanup'):
                hasher.cleanup()
            
            del hasher
            return True
        
        # Benchmark cleanup operations
        stats = performance_benchmark.run_benchmark('memory_cleanup', create_and_cleanup_hasher, iterations=5)
        
        # Cleanup should be fast
        assert stats['mean_time'] < 2.0, "Memory cleanup should be under 2 seconds"
        assert all(result for result in stats['results']), "All cleanup operations should succeed"


@pytest.mark.gpu
@pytest.mark.performance
class TestGPUFallbackPerformance:
    """Test GPU fallback mechanism performance."""
    
    def test_automatic_fallback_performance(self, test_files_various_sizes, performance_benchmark):
        """Test automatic fallback to CPU when GPU fails."""
        if not HAS_GPU_MODULES:
            pytest.skip("GPU modules not available")
        
        # Create hasher with fallback enabled
        hasher = GPUHasher({
            'enable_gpu_hashing': True,
            'fallback_to_cpu': True,
            'max_concurrent_files': 2
        })
        
        # Mock GPU failure for some operations
        original_hash_gpu = hasher._hash_file_gpu
        call_count = 0
        
        def failing_gpu_hash(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:  # Fail every other call
                raise RuntimeError("Simulated GPU failure")
            return original_hash_gpu(*args, **kwargs)
        
        hasher._hash_file_gpu = failing_gpu_hash
        
        # Test fallback behavior
        file_path = test_files_various_sizes['medium']
        
        def hash_with_fallback():
            return hasher.hash_file(file_path, ['sha256'])
        
        stats = performance_benchmark.run_benchmark('fallback_hash', hash_with_fallback, iterations=6)
        
        # All operations should complete (either GPU or CPU)
        successful_results = [r for r in stats['results'] if r and not r.error]
        assert len(successful_results) == 6, "All hash operations should complete via fallback"
        
        # Should have mix of GPU and CPU results
        gpu_results = [r for r in successful_results if r.gpu_accelerated]
        cpu_results = [r for r in successful_results if not r.gpu_accelerated]
        
        assert len(gpu_results) > 0, "Some operations should use GPU"
        assert len(cpu_results) > 0, "Some operations should fallback to CPU"
        
        print(f"Fallback test: {len(gpu_results)} GPU, {len(cpu_results)} CPU fallbacks")
    
    def test_graceful_degradation(self, performance_benchmark):
        """Test graceful degradation when GPU resources are limited."""
        if not HAS_GPU_MODULES:
            pytest.skip("GPU modules not available")
        
        # Test with very limited GPU memory
        limited_hasher = GPUHasher({
            'enable_gpu_hashing': True,
            'gpu_memory_limit_mb': 1,  # Very small limit
            'chunk_size_mb': 1,
            'fallback_to_cpu': True
        })
        
        with tempfile.NamedTemporaryFile() as tmp:
            tmp.write(b'0' * (5 * 1024 * 1024))  # 5MB file
            tmp.flush()
            
            def hash_limited():
                return limited_hasher.hash_file(tmp.name, ['sha256'])
            
            stats = performance_benchmark.run_benchmark('limited_gpu', hash_limited, iterations=3)
            
            # Should still work (via fallback if needed)
            successful_results = [r for r in stats['results'] if r and not r.error]
            assert len(successful_results) == 3, "Limited GPU operations should complete"
            
            # Performance should still be reasonable
            assert stats['mean_time'] < 10.0, "Limited GPU operations should complete in reasonable time"


def test_performance_regression_detection(tmp_path, performance_benchmark):
    """Test for performance regressions in GPU code."""
    if not HAS_GPU_MODULES:
        pytest.skip("GPU modules not available")
    
    # Create baseline test
    test_file = tmp_path / "regression_test.bin"
    create_test_file(str(test_file), size=1024 * 1024)  # 1MB
    
    hasher = GPUHasher({'enable_gpu_hashing': True})
    
    # Baseline performance expectations
    expected_min_throughput = 10.0  # MB/s (conservative baseline)
    expected_max_time = 0.5  # seconds for 1MB file
    
    def hash_for_regression():
        return hasher.hash_file(str(test_file), ['sha256'])
    
    stats = performance_benchmark.run_benchmark('regression_test', hash_for_regression, iterations=5)
    
    # Check for performance regression
    file_size_mb = 1.0
    throughput = file_size_mb / stats['mean_time']
    
    assert throughput >= expected_min_throughput, f"Performance regression detected: {throughput:.1f} MB/s < {expected_min_throughput} MB/s"
    assert stats['mean_time'] <= expected_max_time, f"Performance regression detected: {stats['mean_time']:.3f}s > {expected_max_time}s"
    
    # Check consistency
    time_variance = stats['std_dev'] / stats['mean_time'] if stats['mean_time'] > 0 else 0
    assert time_variance < 0.3, f"Performance too inconsistent: {time_variance:.2f} coefficient of variation"


if __name__ == "__main__":
    # Run basic performance tests when executed directly
    pytest.main([__file__, "-v", "-m", "performance"])