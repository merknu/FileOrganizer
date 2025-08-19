"""
GPU Test Fixtures and Utilities for FileOrganizer.

Provides common fixtures, utilities, and helper functions for GPU testing:
- GPU hardware detection and setup
- Mock GPU implementations for CI environments
- Performance measurement utilities
- Test data generation for GPU benchmarks
- GPU-specific assertion helpers
- Memory management utilities
- Cross-platform GPU compatibility helpers
"""

import pytest
import os
import tempfile
import time
import statistics
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
from unittest.mock import Mock, MagicMock, patch
from dataclasses import dataclass
import logging
import threading
import contextlib

# Try importing required modules
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from PIL import Image, ImageDraw
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# Import GPU modules with error handling
try:
    from file_handler.gpu_acceleration import (
        GPUAccelerator, GPUBackend, GPUDevice, get_gpu_accelerator
    )
    from file_handler.gpu_hasher import GPUHasher
    from file_handler.gpu_image_processor import GPUImageProcessor
    from file_handler.gpu_monitor import GPUMonitor
    HAS_GPU_MODULES = True
except ImportError:
    HAS_GPU_MODULES = False

# Test utilities
from tests.conftest import create_test_file


@dataclass
class GPUTestConfig:
    """Configuration for GPU tests."""
    enable_gpu: bool = True
    backend: str = 'auto'
    mock_gpu: bool = False
    skip_slow_tests: bool = False
    memory_limit_mb: int = 512
    timeout_seconds: int = 30


@dataclass
class PerformanceMetrics:
    """Performance measurement results."""
    duration_seconds: float
    throughput_mb_s: float
    operations_per_second: float
    gpu_accelerated: bool
    memory_used_mb: float
    success_rate: float


class GPUTestEnvironment:
    """Manages GPU test environment setup and cleanup."""
    
    def __init__(self, config: GPUTestConfig):
        self.config = config
        self.temp_dir = None
        self.accelerator = None
        self.monitor = None
        self.cleanup_callbacks = []
        
    def __enter__(self):
        """Set up GPU test environment."""
        # Create temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix='gpu_test_')
        
        # Initialize GPU components if available
        if HAS_GPU_MODULES and not self.config.mock_gpu:
            try:
                self.accelerator = GPUAccelerator({
                    'enable_gpu': self.config.enable_gpu,
                    'backend': self.config.backend,
                    'run_initial_benchmark': False
                })
                
                self.monitor = GPUMonitor({
                    'enable_monitoring': False,  # Manual control for tests
                    'metrics_history_size': 100
                })
            except Exception:
                # Fallback to CPU-only mode
                pass
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up GPU test environment."""
        # Run cleanup callbacks
        for callback in reversed(self.cleanup_callbacks):
            try:
                callback()
            except Exception:
                pass
        
        # Cleanup GPU components
        if self.monitor:
            try:
                self.monitor.cleanup()
            except Exception:
                pass
        
        if self.accelerator:
            try:
                self.accelerator.cleanup()
            except Exception:
                pass
        
        # Remove temporary directory
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
            except Exception:
                pass
    
    def add_cleanup(self, callback: Callable):
        """Add cleanup callback."""
        self.cleanup_callbacks.append(callback)
    
    def is_gpu_available(self) -> bool:
        """Check if GPU is available for testing."""
        return (self.accelerator and self.accelerator.is_available()) or self.config.mock_gpu
    
    def get_temp_path(self, filename: str) -> str:
        """Get path in temporary directory."""
        return os.path.join(self.temp_dir, filename)


class PerformanceTimer:
    """High-precision performance timer with statistics."""
    
    def __init__(self, name: str = "operation"):
        self.name = name
        self.measurements = []
        self.start_time = None
        self.current_measurement = None
        
    def start(self):
        """Start timing."""
        self.start_time = time.perf_counter()
        return self
    
    def stop(self) -> float:
        """Stop timing and record measurement."""
        if self.start_time is None:
            raise RuntimeError("Timer not started")
        
        duration = time.perf_counter() - self.start_time
        self.measurements.append(duration)
        self.start_time = None
        return duration
    
    def __enter__(self):
        """Context manager entry."""
        return self.start()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
    
    def get_stats(self) -> Dict[str, float]:
        """Get timing statistics."""
        if not self.measurements:
            return {}
        
        return {
            'count': len(self.measurements),
            'mean': statistics.mean(self.measurements),
            'min': min(self.measurements),
            'max': max(self.measurements),
            'stdev': statistics.stdev(self.measurements) if len(self.measurements) > 1 else 0.0,
            'total': sum(self.measurements)
        }
    
    def reset(self):
        """Reset all measurements."""
        self.measurements = []
        self.start_time = None


class MockGPUDevice:
    """Mock GPU device for testing without hardware."""
    
    def __init__(self, name: str = "Mock GPU", memory_mb: int = 8192, backend: str = 'cuda'):
        self.name = name
        self.memory_total_mb = memory_mb
        self.memory_used_mb = 0
        self.backend = backend
        self.utilization = 0.0
        self.temperature = 45.0
        
    def allocate_memory(self, size_mb: int) -> bool:
        """Mock memory allocation."""
        if self.memory_used_mb + size_mb <= self.memory_total_mb:
            self.memory_used_mb += size_mb
            return True
        return False
    
    def free_memory(self, size_mb: int):
        """Mock memory deallocation."""
        self.memory_used_mb = max(0, self.memory_used_mb - size_mb)
    
    def get_memory_usage(self) -> Tuple[int, int]:
        """Get memory usage (used, total)."""
        return self.memory_used_mb, self.memory_total_mb


class GPUTestDataGenerator:
    """Generates test data optimized for GPU benchmarks."""
    
    def __init__(self, temp_dir: str):
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(exist_ok=True)
    
    def create_binary_files(self, sizes: List[Tuple[str, int]]) -> Dict[str, str]:
        """Create binary test files of specified sizes."""
        files = {}
        
        for name, size_bytes in sizes:
            file_path = self.temp_dir / f"binary_{name}.bin"
            create_test_file(str(file_path), size=size_bytes)
            files[name] = str(file_path)
        
        return files
    
    def create_image_files(self, sizes: List[Tuple[str, int, int]]) -> Dict[str, str]:
        """Create image test files of specified dimensions."""
        if not HAS_PIL:
            return {}
        
        files = {}
        
        for name, width, height in sizes:
            img_path = self.temp_dir / f"image_{name}.jpg"
            
            # Create test image with gradient pattern
            img = Image.new('RGB', (width, height))
            pixels = []
            
            for y in range(height):
                for x in range(width):
                    r = int((x / width) * 255)
                    g = int((y / height) * 255)
                    b = int(((x + y) / (width + height)) * 255)
                    pixels.append((r, g, b))
            
            img.putdata(pixels)
            img.save(str(img_path), quality=85)
            files[name] = str(img_path)
        
        return files
    
    def create_duplicate_files(self, content_patterns: List[bytes], 
                             duplicates_per_pattern: int = 2) -> Tuple[List[str], Dict[str, List[str]]]:
        """Create files with duplicates for testing duplicate detection."""
        all_files = []
        duplicate_groups = {}
        
        for i, content in enumerate(content_patterns):
            pattern_files = []
            
            for j in range(duplicates_per_pattern):
                file_path = self.temp_dir / f"duplicate_pattern_{i}_copy_{j}.bin"
                file_path.write_bytes(content)
                pattern_files.append(str(file_path))
                all_files.append(str(file_path))
            
            duplicate_groups[f'pattern_{i}'] = pattern_files
        
        return all_files, duplicate_groups
    
    def create_directory_structure(self, structure: Dict[str, Any]) -> str:
        """Create complex directory structure for testing."""
        base_dir = self.temp_dir / "test_structure"
        base_dir.mkdir(exist_ok=True)
        
        def create_level(current_dir: Path, level_structure: Dict[str, Any]):
            for name, content in level_structure.items():
                if isinstance(content, dict):
                    # Subdirectory
                    sub_dir = current_dir / name
                    sub_dir.mkdir(exist_ok=True)
                    create_level(sub_dir, content)
                elif isinstance(content, bytes):
                    # File with specific content
                    file_path = current_dir / name
                    file_path.write_bytes(content)
                elif isinstance(content, int):
                    # File with specified size
                    file_path = current_dir / name
                    create_test_file(str(file_path), size=content)
        
        create_level(base_dir, structure)
        return str(base_dir)


# Pytest Fixtures

@pytest.fixture
def gpu_test_config():
    """Basic GPU test configuration."""
    return GPUTestConfig()


@pytest.fixture
def gpu_test_environment(gpu_test_config):
    """Set up and tear down GPU test environment."""
    with GPUTestEnvironment(gpu_test_config) as env:
        yield env


@pytest.fixture
def performance_timer():
    """Performance timing utility."""
    return PerformanceTimer()


@pytest.fixture
def mock_gpu_device():
    """Mock GPU device for testing."""
    return MockGPUDevice()


@pytest.fixture
def gpu_test_data(gpu_test_environment):
    """Generate test data for GPU benchmarks."""
    generator = GPUTestDataGenerator(gpu_test_environment.temp_dir)
    return generator


@pytest.fixture
def skip_if_no_gpu():
    """Skip test if GPU is not available."""
    if not HAS_GPU_MODULES:
        pytest.skip("GPU modules not available")
    
    try:
        accelerator = GPUAccelerator({'enable_gpu': True})
        if not accelerator.is_available():
            pytest.skip("GPU hardware not available")
    except Exception:
        pytest.skip("GPU initialization failed")


@pytest.fixture
def require_numpy():
    """Require NumPy for GPU array operations."""
    if not HAS_NUMPY:
        pytest.skip("NumPy not available for GPU array operations")


@pytest.fixture
def require_pil():
    """Require PIL for image processing tests."""
    if not HAS_PIL:
        pytest.skip("PIL not available for image processing tests")


@pytest.fixture
def gpu_memory_monitor():
    """Monitor GPU memory usage during tests."""
    class MemoryMonitor:
        def __init__(self):
            self.initial_usage = None
            self.peak_usage = 0
            self.samples = []
            self.monitoring = False
            
        def start_monitoring(self):
            if HAS_GPU_MODULES:
                try:
                    accelerator = get_gpu_accelerator()
                    if accelerator.is_available():
                        used, total = accelerator.get_memory_usage()
                        self.initial_usage = used
                        self.peak_usage = used
                        self.monitoring = True
                except Exception:
                    pass
        
        def sample_memory(self):
            if self.monitoring and HAS_GPU_MODULES:
                try:
                    accelerator = get_gpu_accelerator()
                    used, total = accelerator.get_memory_usage()
                    self.samples.append(used)
                    self.peak_usage = max(self.peak_usage, used)
                except Exception:
                    pass
        
        def get_memory_stats(self) -> Dict[str, float]:
            if not self.monitoring or self.initial_usage is None:
                return {}
            
            return {
                'initial_mb': self.initial_usage,
                'peak_mb': self.peak_usage,
                'increase_mb': self.peak_usage - self.initial_usage,
                'samples': len(self.samples),
                'avg_mb': statistics.mean(self.samples) if self.samples else 0
            }
    
    monitor = MemoryMonitor()
    monitor.start_monitoring()
    yield monitor


@pytest.fixture(params=['cuda', 'opencl', 'auto'])
def gpu_backend(request):
    """Parametrized fixture for testing different GPU backends."""
    return request.param


@pytest.fixture
def gpu_hasher_factory(gpu_test_environment):
    """Factory for creating GPU hashers with different configurations."""
    def create_hasher(config: Dict[str, Any] = None):
        if not HAS_GPU_MODULES:
            pytest.skip("GPU modules not available")
        
        default_config = {
            'enable_gpu_hashing': True,
            'fallback_to_cpu': True,
            'chunk_size_mb': 32
        }
        
        if config:
            default_config.update(config)
        
        return GPUHasher(default_config)
    
    return create_hasher


@pytest.fixture
def gpu_image_processor_factory(gpu_test_environment):
    """Factory for creating GPU image processors."""
    def create_processor(config: Dict[str, Any] = None):
        if not HAS_GPU_MODULES:
            pytest.skip("GPU modules not available")
        
        default_config = {
            'enable_gpu_processing': True,
            'max_concurrent_images': 2
        }
        
        if config:
            default_config.update(config)
        
        return GPUImageProcessor(default_config)
    
    return create_processor


# Utility Functions

def assert_performance_improvement(gpu_time: float, cpu_time: float, 
                                 min_improvement: float = 1.1,
                                 context: str = "operation"):
    """Assert that GPU provides performance improvement over CPU."""
    if gpu_time <= 0 or cpu_time <= 0:
        pytest.fail(f"Invalid timing values for {context}: GPU={gpu_time}s, CPU={cpu_time}s")
    
    speedup = cpu_time / gpu_time
    if speedup < min_improvement:
        pytest.fail(f"GPU did not provide expected speedup for {context}. "
                   f"Expected: {min_improvement}x, Actual: {speedup:.2f}x "
                   f"(GPU: {gpu_time:.3f}s, CPU: {cpu_time:.3f}s)")


def assert_throughput_threshold(throughput_mb_s: float, min_threshold: float,
                               context: str = "operation"):
    """Assert that throughput meets minimum threshold."""
    if throughput_mb_s < min_threshold:
        pytest.fail(f"Throughput below threshold for {context}. "
                   f"Expected: >{min_threshold} MB/s, Actual: {throughput_mb_s:.1f} MB/s")


def assert_memory_usage_reasonable(used_mb: float, total_mb: float,
                                 max_usage_percent: float = 90.0,
                                 context: str = "operation"):
    """Assert that GPU memory usage is reasonable."""
    if total_mb <= 0:
        return  # Skip if memory info not available
    
    usage_percent = (used_mb / total_mb) * 100
    if usage_percent > max_usage_percent:
        pytest.fail(f"GPU memory usage too high for {context}. "
                   f"Used: {usage_percent:.1f}% ({used_mb:.1f}MB / {total_mb:.1f}MB)")


def assert_error_rate_acceptable(error_count: int, total_count: int,
                                max_error_rate: float = 0.05,
                                context: str = "operations"):
    """Assert that error rate is acceptable."""
    if total_count == 0:
        return
    
    error_rate = error_count / total_count
    if error_rate > max_error_rate:
        pytest.fail(f"Error rate too high for {context}. "
                   f"Expected: <{max_error_rate:.1%}, Actual: {error_rate:.1%} "
                   f"({error_count}/{total_count})")


def create_performance_comparison(name: str, gpu_results: List[float], 
                                cpu_results: List[float]) -> Dict[str, Any]:
    """Create performance comparison between GPU and CPU results."""
    comparison = {
        'name': name,
        'gpu_stats': {},
        'cpu_stats': {},
        'comparison': {}
    }
    
    if gpu_results:
        comparison['gpu_stats'] = {
            'mean': statistics.mean(gpu_results),
            'min': min(gpu_results),
            'max': max(gpu_results),
            'count': len(gpu_results)
        }
    
    if cpu_results:
        comparison['cpu_stats'] = {
            'mean': statistics.mean(cpu_results),
            'min': min(cpu_results),
            'max': max(cpu_results),
            'count': len(cpu_results)
        }
    
    if gpu_results and cpu_results:
        gpu_mean = statistics.mean(gpu_results)
        cpu_mean = statistics.mean(cpu_results)
        
        comparison['comparison'] = {
            'speedup_ratio': cpu_mean / gpu_mean if gpu_mean > 0 else 0,
            'gpu_faster': gpu_mean < cpu_mean,
            'improvement_percent': ((cpu_mean - gpu_mean) / cpu_mean * 100) if cpu_mean > 0 else 0
        }
    
    return comparison


def benchmark_function(func: Callable, iterations: int = 3, 
                      timeout: Optional[float] = None) -> Dict[str, Any]:
    """Benchmark a function with multiple iterations."""
    results = []
    errors = []
    
    for i in range(iterations):
        start_time = time.perf_counter()
        try:
            if timeout:
                # Simple timeout implementation
                import signal
                def timeout_handler(signum, frame):
                    raise TimeoutError(f"Function timed out after {timeout}s")
                
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(int(timeout))
                
                try:
                    result = func()
                    duration = time.perf_counter() - start_time
                    results.append((result, duration))
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
            else:
                result = func()
                duration = time.perf_counter() - start_time
                results.append((result, duration))
                
        except Exception as e:
            duration = time.perf_counter() - start_time
            errors.append((str(e), duration))
    
    # Analyze results
    successful_results = [r for r in results if r is not None]
    durations = [r[1] for r in successful_results]
    
    stats = {}
    if durations:
        stats = {
            'mean_duration': statistics.mean(durations),
            'min_duration': min(durations),
            'max_duration': max(durations),
            'std_duration': statistics.stdev(durations) if len(durations) > 1 else 0.0,
            'success_rate': len(successful_results) / iterations,
            'total_iterations': iterations,
            'successful_iterations': len(successful_results),
            'error_count': len(errors),
            'results': [r[0] for r in successful_results]
        }
    
    if errors:
        stats['errors'] = [e[0] for e in errors]
    
    return stats


# Context managers

@contextlib.contextmanager
def gpu_memory_limit(limit_mb: int):
    """Context manager to temporarily limit GPU memory usage."""
    if HAS_GPU_MODULES:
        try:
            accelerator = get_gpu_accelerator()
            original_limit = getattr(accelerator, 'max_gpu_memory_usage', None)
            
            # Set temporary limit
            if hasattr(accelerator, 'max_gpu_memory_usage'):
                accelerator.max_gpu_memory_usage = min(0.9, limit_mb / accelerator.device.memory_total)
            
            yield
            
            # Restore original limit
            if original_limit is not None and hasattr(accelerator, 'max_gpu_memory_usage'):
                accelerator.max_gpu_memory_usage = original_limit
        except Exception:
            yield  # Fallback - just continue without memory limiting
    else:
        yield


@contextlib.contextmanager
def gpu_backend_override(backend: str):
    """Context manager to override GPU backend for testing."""
    if HAS_GPU_MODULES:
        # This would require modifying the GPU acceleration module
        # For now, just yield - individual tests can specify backend in config
        yield
    else:
        yield


# Performance test decorators

def gpu_performance_test(min_speedup: float = 1.1, timeout: float = 60.0):
    """Decorator for GPU performance tests."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                duration = time.perf_counter() - start_time
                
                if duration > timeout:
                    pytest.fail(f"Test {func.__name__} exceeded timeout of {timeout}s")
                
                return result
            except Exception as e:
                duration = time.perf_counter() - start_time
                pytest.fail(f"Test {func.__name__} failed after {duration:.2f}s: {e}")
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator


def skip_if_gpu_memory_insufficient(required_mb: int):
    """Skip test if GPU doesn't have sufficient memory."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if HAS_GPU_MODULES:
                try:
                    accelerator = get_gpu_accelerator()
                    if accelerator.is_available():
                        used, total = accelerator.get_memory_usage()
                        available = total - used
                        if available < required_mb:
                            pytest.skip(f"Insufficient GPU memory: need {required_mb}MB, "
                                       f"have {available}MB available")
                except Exception:
                    pass  # Continue with test
            
            return func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    return decorator