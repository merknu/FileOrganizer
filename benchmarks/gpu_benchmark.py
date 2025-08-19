"""
Comprehensive GPU Benchmark Suite for FileOrganizer.

This benchmark suite provides detailed performance analysis of GPU-accelerated
features including:
- GPU vs CPU performance comparisons
- Real-world scenario benchmarks
- Hardware compatibility testing
- Performance regression detection
- Memory usage analysis
- Throughput optimization testing

Usage:
    python benchmarks/gpu_benchmark.py [options]
    
Options:
    --hardware-only     Run only hardware detection tests
    --performance-only  Run only performance benchmarks  
    --quick            Run quick benchmark suite (reduced test data)
    --full             Run full comprehensive benchmark
    --output FILE      Save results to JSON file
    --compare FILE     Compare with previous benchmark results
    --profile          Enable detailed profiling
    --gpu-backend BACKEND  Force specific GPU backend (cuda/opencl/auto)
"""

import argparse
import json
import os
import sys
import time
import tempfile
import statistics
import platform
import traceback
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import test utilities
try:
    from tests.conftest import create_test_file
except ImportError:
    # Fallback test file creation
    def create_test_file(filepath, size=1024):
        """Create test file with specified size"""
        with open(filepath, 'wb') as f:
            f.write(os.urandom(size))

# Try importing required modules
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    print("Warning: NumPy not available - some benchmarks will be limited")

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("Warning: PIL not available - image benchmarks will be skipped")

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    print("Warning: psutil not available - system monitoring limited")

# Import GPU modules  
try:
    from file_handler.gpu_acceleration import (
        GPUAccelerator, GPUBackend, get_gpu_accelerator, 
        get_system_gpu_info, initialize_gpu_acceleration
    )
    from file_handler.gpu_hasher import GPUHasher, find_duplicate_files
    from file_handler.gpu_image_processor import GPUImageProcessor
    from file_handler.gpu_monitor import GPUMonitor, get_gpu_monitor
    HAS_GPU_MODULES = True
except ImportError as e:
    HAS_GPU_MODULES = False
    print(f"Warning: GPU modules not available - {e}")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class BenchmarkConfig:
    """Benchmark configuration."""
    hardware_only: bool = False
    performance_only: bool = False
    quick: bool = False
    full: bool = True
    output_file: Optional[str] = None
    compare_file: Optional[str] = None
    enable_profiling: bool = False
    gpu_backend: str = 'auto'
    test_data_sizes: List[Tuple[str, int]] = None
    iterations: int = 3
    timeout_seconds: int = 300


@dataclass
class BenchmarkResult:
    """Individual benchmark result."""
    name: str
    success: bool
    duration_seconds: float
    throughput_mb_s: float = 0.0
    gpu_accelerated: bool = False
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = None


@dataclass 
class SystemInfo:
    """System information for benchmarking."""
    platform: str
    python_version: str
    cpu_count: int
    total_memory_gb: float
    gpu_info: Dict[str, Any]
    libraries: Dict[str, bool]


class GPUBenchmarkSuite:
    """Comprehensive GPU benchmark suite."""
    
    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.results = {}
        self.system_info = None
        self.start_time = None
        self.end_time = None
        self.temp_dir = None
        
        # Initialize temporary directory
        self.temp_dir = tempfile.mkdtemp(prefix='gpu_benchmark_')
        logger.info(f"Benchmark temp directory: {self.temp_dir}")
        
        # Set default test data sizes
        if config.test_data_sizes is None:
            if config.quick:
                config.test_data_sizes = [
                    ('tiny', 1024),           # 1KB
                    ('small', 100 * 1024),   # 100KB
                    ('medium', 1024 * 1024), # 1MB
                ]
            else:
                config.test_data_sizes = [
                    ('tiny', 1024),                    # 1KB
                    ('small', 100 * 1024),            # 100KB
                    ('medium', 1024 * 1024),          # 1MB
                    ('large', 10 * 1024 * 1024),      # 10MB
                    ('xlarge', 50 * 1024 * 1024),     # 50MB
                    ('xxlarge', 100 * 1024 * 1024),   # 100MB
                ]
    
    def run_complete_benchmark(self) -> Dict[str, Any]:
        """Run the complete benchmark suite."""
        logger.info("Starting comprehensive GPU benchmark suite")
        self.start_time = datetime.now()
        
        try:
            # Collect system information
            self.system_info = self._collect_system_info()
            logger.info(f"System: {self.system_info.platform}, "
                       f"CPUs: {self.system_info.cpu_count}, "
                       f"RAM: {self.system_info.total_memory_gb:.1f}GB")
            
            # Run benchmark categories
            if not self.config.performance_only:
                self._run_hardware_detection_tests()
            
            if not self.config.hardware_only:
                self._run_performance_benchmarks()
                self._run_real_world_scenarios()
                self._run_stress_tests()
            
            self._run_regression_tests()
            
        except Exception as e:
            logger.error(f"Benchmark suite failed: {e}")
            self.results['benchmark_error'] = str(e)
            
        finally:
            self.end_time = datetime.now()
            
            # Cleanup
            self._cleanup_temp_files()
        
        # Compile final results
        return self._compile_results()
    
    def _collect_system_info(self) -> SystemInfo:
        """Collect comprehensive system information."""
        info = SystemInfo(
            platform=platform.platform(),
            python_version=sys.version,
            cpu_count=os.cpu_count() or 1,
            total_memory_gb=0.0,
            gpu_info={},
            libraries={}
        )
        
        # Memory information
        if HAS_PSUTIL:
            info.total_memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # GPU information
        if HAS_GPU_MODULES:
            info.gpu_info = get_system_gpu_info()
        
        # Library availability
        info.libraries = {
            'numpy': HAS_NUMPY,
            'PIL': HAS_PIL,
            'psutil': HAS_PSUTIL,
            'gpu_modules': HAS_GPU_MODULES,
        }
        
        # Try to detect additional GPU libraries
        gpu_libs = {}
        for lib_name in ['cupy', 'pycuda', 'pyopencl', 'GPUtil', 'py3nvml']:
            try:
                __import__(lib_name)
                gpu_libs[lib_name] = True
            except ImportError:
                gpu_libs[lib_name] = False
        
        info.libraries.update(gpu_libs)
        
        return info
    
    def _run_hardware_detection_tests(self):
        """Run hardware detection and compatibility tests."""
        logger.info("Running hardware detection tests...")
        
        self.results['hardware'] = {}
        
        # Test GPU initialization
        self.results['hardware']['gpu_initialization'] = self._test_gpu_initialization()
        
        # Test device detection
        self.results['hardware']['device_detection'] = self._test_device_detection()
        
        # Test backend selection
        self.results['hardware']['backend_selection'] = self._test_backend_selection()
        
        # Test memory detection
        self.results['hardware']['memory_detection'] = self._test_memory_detection()
    
    def _run_performance_benchmarks(self):
        """Run core performance benchmarks."""
        logger.info("Running performance benchmarks...")
        
        self.results['performance'] = {}
        
        # File hashing benchmarks
        self.results['performance']['hashing'] = self._benchmark_file_hashing()
        
        # Image processing benchmarks
        if HAS_PIL:
            self.results['performance']['image_processing'] = self._benchmark_image_processing()
        
        # Memory bandwidth tests
        self.results['performance']['memory_bandwidth'] = self._benchmark_memory_bandwidth()
        
        # Batch processing tests
        self.results['performance']['batch_processing'] = self._benchmark_batch_processing()
    
    def _run_real_world_scenarios(self):
        """Run real-world usage scenario benchmarks."""
        logger.info("Running real-world scenario benchmarks...")
        
        self.results['scenarios'] = {}
        
        # Large directory processing
        self.results['scenarios']['large_directory'] = self._benchmark_large_directory()
        
        # Duplicate detection
        self.results['scenarios']['duplicate_detection'] = self._benchmark_duplicate_detection()
        
        # Mixed workload
        self.results['scenarios']['mixed_workload'] = self._benchmark_mixed_workload()
    
    def _run_stress_tests(self):
        """Run stress and stability tests."""
        logger.info("Running stress tests...")
        
        self.results['stress'] = {}
        
        # Memory stress test
        self.results['stress']['memory_stress'] = self._stress_test_memory()
        
        # Concurrent operations test
        self.results['stress']['concurrent_operations'] = self._stress_test_concurrent()
        
        # Long running operation test
        self.results['stress']['long_running'] = self._stress_test_long_running()
    
    def _run_regression_tests(self):
        """Run performance regression detection tests."""
        logger.info("Running regression tests...")
        
        self.results['regression'] = {}
        
        # Compare with previous results if available
        if self.config.compare_file and os.path.exists(self.config.compare_file):
            self.results['regression'] = self._compare_with_baseline()
        else:
            # Run baseline performance tests
            self.results['regression']['baseline'] = self._establish_performance_baseline()
    
    def _test_gpu_initialization(self) -> BenchmarkResult:
        """Test GPU initialization performance and reliability."""
        if not HAS_GPU_MODULES:
            return BenchmarkResult(
                name='gpu_initialization',
                success=False,
                duration_seconds=0.0,
                error_message='GPU modules not available'
            )
        
        results = []
        
        for i in range(self.config.iterations):
            start_time = time.perf_counter()
            try:
                accelerator = GPUAccelerator({
                    'enable_gpu': True,
                    'backend': self.config.gpu_backend,
                    'run_initial_benchmark': False
                })
                success = accelerator.is_available()
                accelerator.cleanup()
                
                duration = time.perf_counter() - start_time
                results.append((success, duration))
                
            except Exception as e:
                duration = time.perf_counter() - start_time
                results.append((False, duration))
        
        # Analyze results
        successful_inits = [r for r in results if r[0]]
        all_durations = [r[1] for r in results]
        
        return BenchmarkResult(
            name='gpu_initialization',
            success=len(successful_inits) > 0,
            duration_seconds=statistics.mean(all_durations),
            metadata={
                'success_rate': len(successful_inits) / len(results),
                'avg_duration': statistics.mean(all_durations),
                'min_duration': min(all_durations),
                'max_duration': max(all_durations),
                'iterations': len(results)
            }
        )
    
    def _test_device_detection(self) -> BenchmarkResult:
        """Test GPU device detection."""
        if not HAS_GPU_MODULES:
            return BenchmarkResult(
                name='device_detection',
                success=False,
                duration_seconds=0.0,
                error_message='GPU modules not available'
            )
        
        start_time = time.perf_counter()
        try:
            accelerator = GPUAccelerator({'enable_gpu': True})
            devices = accelerator.available_devices
            duration = time.perf_counter() - start_time
            
            return BenchmarkResult(
                name='device_detection',
                success=True,
                duration_seconds=duration,
                metadata={
                    'devices_found': len(devices),
                    'devices': [{'name': d.name, 'backend': d.backend.value, 'memory_mb': d.memory_total} 
                               for d in devices]
                }
            )
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            return BenchmarkResult(
                name='device_detection',
                success=False,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    def _test_backend_selection(self) -> BenchmarkResult:
        """Test GPU backend selection logic."""
        if not HAS_GPU_MODULES:
            return BenchmarkResult(
                name='backend_selection',
                success=False,
                duration_seconds=0.0,
                error_message='GPU modules not available'
            )
        
        backends_tested = []
        
        for backend in ['auto', 'cuda', 'opencl']:
            start_time = time.perf_counter()
            try:
                accelerator = GPUAccelerator({
                    'enable_gpu': True,
                    'backend': backend
                })
                duration = time.perf_counter() - start_time
                
                backends_tested.append({
                    'backend': backend,
                    'success': accelerator.is_available(),
                    'selected_backend': accelerator.backend.value if accelerator.device else 'none',
                    'duration': duration
                })
                
                accelerator.cleanup()
                
            except Exception as e:
                duration = time.perf_counter() - start_time
                backends_tested.append({
                    'backend': backend,
                    'success': False,
                    'error': str(e),
                    'duration': duration
                })
        
        total_duration = sum(b['duration'] for b in backends_tested)
        successful_backends = [b for b in backends_tested if b['success']]
        
        return BenchmarkResult(
            name='backend_selection',
            success=len(successful_backends) > 0,
            duration_seconds=total_duration,
            metadata={
                'backends_tested': backends_tested,
                'successful_backends': len(successful_backends),
                'total_backends': len(backends_tested)
            }
        )
    
    def _test_memory_detection(self) -> BenchmarkResult:
        """Test GPU memory detection and reporting."""
        if not HAS_GPU_MODULES:
            return BenchmarkResult(
                name='memory_detection',
                success=False,
                duration_seconds=0.0,
                error_message='GPU modules not available'
            )
        
        start_time = time.perf_counter()
        try:
            accelerator = GPUAccelerator({'enable_gpu': True})
            
            if not accelerator.is_available():
                return BenchmarkResult(
                    name='memory_detection',
                    success=False,
                    duration_seconds=time.perf_counter() - start_time,
                    error_message='GPU not available'
                )
            
            used, total = accelerator.get_memory_usage()
            duration = time.perf_counter() - start_time
            
            return BenchmarkResult(
                name='memory_detection',
                success=total > 0,
                duration_seconds=duration,
                metadata={
                    'memory_used_mb': used,
                    'memory_total_mb': total,
                    'memory_available_mb': total - used,
                    'utilization_percent': (used / total * 100) if total > 0 else 0
                }
            )
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            return BenchmarkResult(
                name='memory_detection',
                success=False,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    def _benchmark_file_hashing(self) -> Dict[str, BenchmarkResult]:
        """Benchmark file hashing performance."""
        if not HAS_GPU_MODULES:
            return {'error': BenchmarkResult(
                name='file_hashing',
                success=False,
                duration_seconds=0.0,
                error_message='GPU modules not available'
            )}
        
        results = {}
        
        # Create test files of various sizes
        test_files = {}
        for size_name, size_bytes in self.config.test_data_sizes:
            file_path = Path(self.temp_dir) / f"hash_test_{size_name}.bin"
            create_test_file(str(file_path), size=size_bytes)
            test_files[size_name] = str(file_path)
        
        # Initialize hashers
        gpu_hasher = GPUHasher({'enable_gpu_hashing': True})
        cpu_hasher = GPUHasher({'enable_gpu_hashing': False})
        
        # Benchmark each file size
        for size_name, file_path in test_files.items():
            file_size_mb = os.path.getsize(file_path) / 1024 / 1024
            
            # GPU hashing
            gpu_times = []
            gpu_success = False
            
            for _ in range(self.config.iterations):
                start_time = time.perf_counter()
                try:
                    result = gpu_hasher.hash_file(file_path, ['sha256'])
                    duration = time.perf_counter() - start_time
                    
                    if not result.error:
                        gpu_times.append(duration)
                        gpu_success = True
                        
                except Exception:
                    pass
            
            # CPU hashing
            cpu_times = []
            cpu_success = False
            
            for _ in range(self.config.iterations):
                start_time = time.perf_counter()
                try:
                    result = cpu_hasher.hash_file(file_path, ['sha256'])
                    duration = time.perf_counter() - start_time
                    
                    if not result.error:
                        cpu_times.append(duration)
                        cpu_success = True
                        
                except Exception:
                    pass
            
            # Calculate results
            gpu_avg = statistics.mean(gpu_times) if gpu_times else 0
            cpu_avg = statistics.mean(cpu_times) if cpu_times else 0
            
            gpu_throughput = file_size_mb / gpu_avg if gpu_avg > 0 else 0
            cpu_throughput = file_size_mb / cpu_avg if cpu_avg > 0 else 0
            
            results[f'hashing_{size_name}'] = BenchmarkResult(
                name=f'hashing_{size_name}',
                success=gpu_success or cpu_success,
                duration_seconds=gpu_avg if gpu_success else cpu_avg,
                throughput_mb_s=gpu_throughput if gpu_success else cpu_throughput,
                gpu_accelerated=gpu_success,
                metadata={
                    'file_size_mb': file_size_mb,
                    'gpu_time': gpu_avg,
                    'cpu_time': cpu_avg,
                    'gpu_throughput': gpu_throughput,
                    'cpu_throughput': cpu_throughput,
                    'speedup_ratio': cpu_avg / gpu_avg if gpu_avg > 0 and cpu_avg > 0 else 0,
                    'gpu_success': gpu_success,
                    'cpu_success': cpu_success
                }
            )
        
        return results
    
    def _benchmark_image_processing(self) -> Dict[str, BenchmarkResult]:
        """Benchmark image processing performance."""
        if not HAS_GPU_MODULES or not HAS_PIL:
            return {'error': BenchmarkResult(
                name='image_processing',
                success=False,
                duration_seconds=0.0,
                error_message='GPU modules or PIL not available'
            )}
        
        results = {}
        
        # Create test images
        image_sizes = [
            ('small', 640, 480),
            ('medium', 1920, 1080),
            ('large', 3840, 2160)
        ]
        
        if self.config.quick:
            image_sizes = image_sizes[:2]  # Only small and medium for quick tests
        
        test_images = {}
        for size_name, width, height in image_sizes:
            img_path = Path(self.temp_dir) / f"test_image_{size_name}.jpg"
            
            # Create test image
            img = Image.new('RGB', (width, height))
            pixels = []
            for y in range(height):
                for x in range(width):
                    r = (x * 255) // width
                    g = (y * 255) // height
                    b = ((x + y) * 255) // (width + height)
                    pixels.append((r, g, b))
            img.putdata(pixels)
            img.save(str(img_path), quality=85)
            
            test_images[size_name] = str(img_path)
        
        # Initialize processors
        gpu_processor = GPUImageProcessor({'enable_gpu_processing': True})
        cpu_processor = GPUImageProcessor({'enable_gpu_processing': False})
        
        # Benchmark metadata extraction
        for size_name, img_path in test_images.items():
            # GPU processing
            gpu_times = []
            gpu_success = False
            
            for _ in range(self.config.iterations):
                start_time = time.perf_counter()
                try:
                    result = gpu_processor.extract_metadata(img_path)
                    duration = time.perf_counter() - start_time
                    
                    if not result.error:
                        gpu_times.append(duration)
                        gpu_success = True
                        
                except Exception:
                    pass
            
            # CPU processing
            cpu_times = []
            cpu_success = False
            
            for _ in range(self.config.iterations):
                start_time = time.perf_counter()
                try:
                    result = cpu_processor.extract_metadata(img_path)
                    duration = time.perf_counter() - start_time
                    
                    if not result.error:
                        cpu_times.append(duration)
                        cpu_success = True
                        
                except Exception:
                    pass
            
            # Calculate results
            gpu_avg = statistics.mean(gpu_times) if gpu_times else 0
            cpu_avg = statistics.mean(cpu_times) if cpu_times else 0
            
            results[f'image_metadata_{size_name}'] = BenchmarkResult(
                name=f'image_metadata_{size_name}',
                success=gpu_success or cpu_success,
                duration_seconds=gpu_avg if gpu_success else cpu_avg,
                gpu_accelerated=gpu_success,
                metadata={
                    'gpu_time': gpu_avg,
                    'cpu_time': cpu_avg,
                    'speedup_ratio': cpu_avg / gpu_avg if gpu_avg > 0 and cpu_avg > 0 else 0,
                    'gpu_success': gpu_success,
                    'cpu_success': cpu_success
                }
            )
        
        return results
    
    def _benchmark_memory_bandwidth(self) -> BenchmarkResult:
        """Benchmark GPU memory bandwidth."""
        if not HAS_GPU_MODULES:
            return BenchmarkResult(
                name='memory_bandwidth',
                success=False,
                duration_seconds=0.0,
                error_message='GPU modules not available'
            )
        
        start_time = time.perf_counter()
        try:
            monitor = GPUMonitor({'enable_monitoring': False})
            benchmark_results = monitor.run_comprehensive_benchmark()
            duration = time.perf_counter() - start_time
            
            if benchmark_results['success']:
                tests = benchmark_results.get('tests', {})
                memory_test = tests.get('memory_bandwidth', {})
                
                return BenchmarkResult(
                    name='memory_bandwidth',
                    success=memory_test.get('success', False),
                    duration_seconds=duration,
                    metadata=memory_test
                )
            else:
                return BenchmarkResult(
                    name='memory_bandwidth',
                    success=False,
                    duration_seconds=duration,
                    error_message=benchmark_results.get('error', 'Benchmark failed')
                )
                
        except Exception as e:
            duration = time.perf_counter() - start_time
            return BenchmarkResult(
                name='memory_bandwidth',
                success=False,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    def _benchmark_batch_processing(self) -> BenchmarkResult:
        """Benchmark batch processing performance."""
        if not HAS_GPU_MODULES:
            return BenchmarkResult(
                name='batch_processing',
                success=False,
                duration_seconds=0.0,
                error_message='GPU modules not available'
            )
        
        # Create batch of test files
        batch_size = 20 if self.config.quick else 50
        file_size = 1024 * 500  # 500KB each
        
        test_files = []
        for i in range(batch_size):
            file_path = Path(self.temp_dir) / f"batch_test_{i}.bin"
            create_test_file(str(file_path), size=file_size)
            test_files.append(str(file_path))
        
        # Benchmark batch hashing
        start_time = time.perf_counter()
        try:
            hasher = GPUHasher({'enable_gpu_hashing': True})
            results = hasher.hash_files_batch(test_files, ['sha256'])
            duration = time.perf_counter() - start_time
            
            # Analyze results
            successful_results = [r for r in results if not r.error]
            gpu_results = [r for r in successful_results if r.gpu_accelerated]
            
            total_size_mb = sum(os.path.getsize(f) for f in test_files) / 1024 / 1024
            throughput = total_size_mb / duration if duration > 0 else 0
            
            return BenchmarkResult(
                name='batch_processing',
                success=len(successful_results) > 0,
                duration_seconds=duration,
                throughput_mb_s=throughput,
                gpu_accelerated=len(gpu_results) > len(successful_results) / 2,
                metadata={
                    'batch_size': batch_size,
                    'successful_files': len(successful_results),
                    'gpu_processed': len(gpu_results),
                    'total_size_mb': total_size_mb,
                    'files_per_second': len(successful_results) / duration if duration > 0 else 0
                }
            )
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            return BenchmarkResult(
                name='batch_processing',
                success=False,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    def _benchmark_large_directory(self) -> BenchmarkResult:
        """Benchmark large directory processing."""
        if not HAS_GPU_MODULES:
            return BenchmarkResult(
                name='large_directory',
                success=False,
                duration_seconds=0.0,
                error_message='GPU modules not available'
            )
        
        # Create large directory structure
        num_files = 100 if self.config.quick else 500
        base_dir = Path(self.temp_dir) / 'large_directory_test'
        base_dir.mkdir()
        
        # Create subdirectories with files
        subdirs = ['docs', 'images', 'data', 'misc']
        files_per_subdir = num_files // len(subdirs)
        
        all_files = []
        for subdir in subdirs:
            subdir_path = base_dir / subdir
            subdir_path.mkdir()
            
            for i in range(files_per_subdir):
                file_path = subdir_path / f'file_{i:04d}.txt'
                content = f'Content for {subdir}/file_{i} ' * (50 + i % 100)
                file_path.write_text(content)
                all_files.append(str(file_path))
        
        # Benchmark directory processing
        start_time = time.perf_counter()
        try:
            hasher = GPUHasher({'enable_gpu_hashing': True})
            results = hasher.hash_files_batch(all_files, ['sha256'])
            duration = time.perf_counter() - start_time
            
            # Analyze results
            successful_results = [r for r in results if not r.error]
            total_size = sum(os.path.getsize(f) for f in all_files)
            total_size_mb = total_size / 1024 / 1024
            throughput = total_size_mb / duration if duration > 0 else 0
            
            return BenchmarkResult(
                name='large_directory',
                success=len(successful_results) == len(all_files),
                duration_seconds=duration,
                throughput_mb_s=throughput,
                metadata={
                    'total_files': len(all_files),
                    'successful_files': len(successful_results),
                    'total_size_mb': total_size_mb,
                    'files_per_second': len(successful_results) / duration if duration > 0 else 0
                }
            )
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            return BenchmarkResult(
                name='large_directory',
                success=False,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    def _benchmark_duplicate_detection(self) -> BenchmarkResult:
        """Benchmark duplicate file detection."""
        if not HAS_GPU_MODULES:
            return BenchmarkResult(
                name='duplicate_detection',
                success=False,
                duration_seconds=0.0,
                error_message='GPU modules not available'
            )
        
        # Create test files with some duplicates
        test_dir = Path(self.temp_dir) / 'duplicate_test'
        test_dir.mkdir()
        
        # Create original files
        file_contents = [
            b'Content A' * 1000,
            b'Content B' * 1500, 
            b'Content C' * 800,
            b'Unique content' * 600
        ]
        
        all_files = []
        
        # Create original files
        for i, content in enumerate(file_contents):
            file_path = test_dir / f'original_{i}.txt'
            file_path.write_bytes(content)
            all_files.append(str(file_path))
        
        # Create duplicates
        for i in range(3):  # Duplicate first 3 files
            dup_path = test_dir / f'duplicate_{i}.txt'
            dup_path.write_bytes(file_contents[i])
            all_files.append(str(dup_path))
        
        # Benchmark duplicate detection
        start_time = time.perf_counter()
        try:
            duplicates = find_duplicate_files(
                str(test_dir),
                recursive=True,
                algorithms=['sha256']
            )
            duration = time.perf_counter() - start_time
            
            return BenchmarkResult(
                name='duplicate_detection',
                success=len(duplicates) == 3,  # Should find 3 duplicate groups
                duration_seconds=duration,
                metadata={
                    'total_files': len(all_files),
                    'duplicate_groups': len(duplicates),
                    'expected_duplicates': 3,
                    'files_per_second': len(all_files) / duration if duration > 0 else 0
                }
            )
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            return BenchmarkResult(
                name='duplicate_detection',
                success=False,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    def _benchmark_mixed_workload(self) -> BenchmarkResult:
        """Benchmark mixed GPU workload."""
        if not HAS_GPU_MODULES:
            return BenchmarkResult(
                name='mixed_workload',
                success=False,
                duration_seconds=0.0,
                error_message='GPU modules not available'
            )
        
        # Create mixed content
        test_dir = Path(self.temp_dir) / 'mixed_workload'
        test_dir.mkdir()
        
        # Binary files
        binary_files = []
        for i in range(10):
            file_path = test_dir / f'binary_{i}.bin'
            create_test_file(str(file_path), size=1024 * 1024)  # 1MB
            binary_files.append(str(file_path))
        
        # Image files (if PIL available)
        image_files = []
        if HAS_PIL:
            for i in range(5):
                img_path = test_dir / f'image_{i}.jpg'
                img = Image.new('RGB', (800, 600), color='red')
                img.save(str(img_path), quality=85)
                image_files.append(str(img_path))
        
        # Mixed processing
        start_time = time.perf_counter()
        try:
            hasher = GPUHasher({'enable_gpu_hashing': True})
            
            # Hash all files
            all_files = binary_files + image_files
            hash_results = hasher.hash_files_batch(all_files, ['sha256'])
            
            # Process images if available
            image_results = []
            if image_files and HAS_PIL:
                processor = GPUImageProcessor({'enable_gpu_processing': True})
                for img_path in image_files:
                    result = processor.extract_metadata(img_path)
                    image_results.append(result)
            
            duration = time.perf_counter() - start_time
            
            # Analyze results
            successful_hashes = [r for r in hash_results if not r.error]
            successful_images = [r for r in image_results if not r.error]
            
            total_size = sum(os.path.getsize(f) for f in all_files)
            total_size_mb = total_size / 1024 / 1024
            throughput = total_size_mb / duration if duration > 0 else 0
            
            return BenchmarkResult(
                name='mixed_workload',
                success=len(successful_hashes) == len(all_files),
                duration_seconds=duration,
                throughput_mb_s=throughput,
                metadata={
                    'binary_files': len(binary_files),
                    'image_files': len(image_files),
                    'successful_hashes': len(successful_hashes),
                    'successful_images': len(successful_images),
                    'total_size_mb': total_size_mb
                }
            )
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            return BenchmarkResult(
                name='mixed_workload',
                success=False,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    def _stress_test_memory(self) -> BenchmarkResult:
        """Run GPU memory stress test."""
        if not HAS_GPU_MODULES:
            return BenchmarkResult(
                name='memory_stress',
                success=False,
                duration_seconds=0.0,
                error_message='GPU modules not available'
            )
        
        # Create large files to stress memory
        large_file_size = 50 * 1024 * 1024  # 50MB
        num_files = 5
        
        test_files = []
        for i in range(num_files):
            file_path = Path(self.temp_dir) / f'stress_test_{i}.bin'
            create_test_file(str(file_path), size=large_file_size)
            test_files.append(str(file_path))
        
        start_time = time.perf_counter()
        try:
            hasher = GPUHasher({
                'enable_gpu_hashing': True,
                'gpu_memory_limit_mb': 512,  # Limited memory
                'chunk_size_mb': 64
            })
            
            results = []
            for file_path in test_files:
                result = hasher.hash_file(file_path, ['sha256'])
                results.append(result)
            
            duration = time.perf_counter() - start_time
            
            successful_results = [r for r in results if not r.error]
            total_size_mb = (large_file_size * num_files) / 1024 / 1024
            throughput = total_size_mb / duration if duration > 0 else 0
            
            return BenchmarkResult(
                name='memory_stress',
                success=len(successful_results) == num_files,
                duration_seconds=duration,
                throughput_mb_s=throughput,
                metadata={
                    'large_files_processed': len(successful_results),
                    'total_files': num_files,
                    'file_size_mb': large_file_size / 1024 / 1024,
                    'total_size_mb': total_size_mb
                }
            )
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            return BenchmarkResult(
                name='memory_stress',
                success=False,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    def _stress_test_concurrent(self) -> BenchmarkResult:
        """Run concurrent operations stress test."""
        if not HAS_GPU_MODULES:
            return BenchmarkResult(
                name='concurrent_stress',
                success=False,
                duration_seconds=0.0,
                error_message='GPU modules not available'
            )
        
        import threading
        import concurrent.futures
        
        # Create test files
        num_threads = 4
        files_per_thread = 10
        test_files = []
        
        for i in range(num_threads * files_per_thread):
            file_path = Path(self.temp_dir) / f'concurrent_{i}.bin'
            create_test_file(str(file_path), size=1024 * 512)  # 512KB
            test_files.append(str(file_path))
        
        def worker_thread(file_chunk):
            hasher = GPUHasher({'enable_gpu_hashing': True})
            results = []
            for file_path in file_chunk:
                try:
                    result = hasher.hash_file(file_path, ['sha256'])
                    results.append(result)
                except Exception as e:
                    results.append(None)
            return results
        
        # Split files into chunks for each thread
        file_chunks = [test_files[i::num_threads] for i in range(num_threads)]
        
        start_time = time.perf_counter()
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(worker_thread, chunk) for chunk in file_chunks]
                all_results = []
                
                for future in concurrent.futures.as_completed(futures, timeout=60):
                    thread_results = future.result()
                    all_results.extend(thread_results)
            
            duration = time.perf_counter() - start_time
            
            successful_results = [r for r in all_results if r and not r.error]
            total_size_mb = sum(os.path.getsize(f) for f in test_files) / 1024 / 1024
            throughput = total_size_mb / duration if duration > 0 else 0
            
            return BenchmarkResult(
                name='concurrent_stress',
                success=len(successful_results) == len(test_files),
                duration_seconds=duration,
                throughput_mb_s=throughput,
                metadata={
                    'threads': num_threads,
                    'total_files': len(test_files),
                    'successful_files': len(successful_results),
                    'total_size_mb': total_size_mb
                }
            )
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            return BenchmarkResult(
                name='concurrent_stress',
                success=False,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    def _stress_test_long_running(self) -> BenchmarkResult:
        """Run long running operation stress test."""
        if not HAS_GPU_MODULES:
            return BenchmarkResult(
                name='long_running_stress',
                success=False,
                duration_seconds=0.0,
                error_message='GPU modules not available'
            )
        
        # Create files for extended processing
        num_iterations = 50 if self.config.quick else 200
        file_size = 1024 * 1024  # 1MB
        
        test_file = Path(self.temp_dir) / 'long_running_test.bin'
        create_test_file(str(test_file), size=file_size)
        
        start_time = time.perf_counter()
        try:
            hasher = GPUHasher({'enable_gpu_hashing': True})
            successful_operations = 0
            
            for i in range(num_iterations):
                result = hasher.hash_file(str(test_file), ['sha256'])
                if not result.error:
                    successful_operations += 1
                
                # Check for memory leaks periodically
                if i % 20 == 0 and HAS_PSUTIL:
                    import psutil
                    process = psutil.Process()
                    memory_mb = process.memory_info().rss / 1024 / 1024
                    if memory_mb > 2000:  # 2GB threshold
                        raise RuntimeError(f"Memory usage too high: {memory_mb:.1f}MB")
            
            duration = time.perf_counter() - start_time
            
            return BenchmarkResult(
                name='long_running_stress',
                success=successful_operations == num_iterations,
                duration_seconds=duration,
                metadata={
                    'iterations': num_iterations,
                    'successful_operations': successful_operations,
                    'operations_per_second': successful_operations / duration if duration > 0 else 0,
                    'avg_time_per_operation': duration / num_iterations if num_iterations > 0 else 0
                }
            )
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            return BenchmarkResult(
                name='long_running_stress',
                success=False,
                duration_seconds=duration,
                error_message=str(e)
            )
    
    def _establish_performance_baseline(self) -> Dict[str, float]:
        """Establish performance baseline metrics."""
        baseline = {}
        
        if not HAS_GPU_MODULES:
            return baseline
        
        # Basic operation baselines
        try:
            # Single file hashing baseline (1MB)
            test_file = Path(self.temp_dir) / 'baseline_test.bin'
            create_test_file(str(test_file), size=1024 * 1024)
            
            hasher = GPUHasher({'enable_gpu_hashing': True})
            
            times = []
            for _ in range(5):
                start_time = time.perf_counter()
                result = hasher.hash_file(str(test_file), ['sha256'])
                duration = time.perf_counter() - start_time
                
                if not result.error:
                    times.append(duration)
            
            if times:
                baseline['single_file_hash_1mb'] = statistics.mean(times)
                baseline['single_file_throughput_mb_s'] = 1.0 / statistics.mean(times)
            
        except Exception as e:
            logger.warning(f"Could not establish baseline: {e}")
        
        return baseline
    
    def _compare_with_baseline(self) -> Dict[str, Any]:
        """Compare current results with baseline from file."""
        comparison = {}
        
        try:
            with open(self.config.compare_file, 'r') as f:
                baseline_data = json.load(f)
            
            baseline_results = baseline_data.get('results', {})
            current_results = self.results
            
            # Compare specific metrics
            comparison['baseline_file'] = self.config.compare_file
            comparison['baseline_timestamp'] = baseline_data.get('timestamp')
            comparison['comparisons'] = {}
            
            # Compare performance benchmarks
            if 'performance' in baseline_results and 'performance' in current_results:
                perf_comparison = {}
                
                baseline_perf = baseline_results['performance']
                current_perf = current_results['performance']
                
                for test_name in baseline_perf.keys():
                    if test_name in current_perf:
                        baseline_time = baseline_perf[test_name].get('duration_seconds', 0)
                        current_time = current_perf[test_name].get('duration_seconds', 0)
                        
                        if baseline_time > 0 and current_time > 0:
                            speedup = baseline_time / current_time
                            change_percent = ((current_time - baseline_time) / baseline_time) * 100
                            
                            perf_comparison[test_name] = {
                                'baseline_time': baseline_time,
                                'current_time': current_time,
                                'speedup_ratio': speedup,
                                'change_percent': change_percent,
                                'regression': change_percent > 10  # >10% slower is regression
                            }
                
                comparison['comparisons']['performance'] = perf_comparison
            
            # Overall regression summary
            regressions = []
            improvements = []
            
            for test_name, comp in comparison.get('comparisons', {}).get('performance', {}).items():
                if comp.get('regression'):
                    regressions.append(test_name)
                elif comp.get('speedup_ratio', 0) > 1.1:  # >10% faster
                    improvements.append(test_name)
            
            comparison['summary'] = {
                'regressions': len(regressions),
                'improvements': len(improvements),
                'regression_tests': regressions,
                'improvement_tests': improvements
            }
            
        except Exception as e:
            comparison['error'] = f"Could not compare with baseline: {e}"
        
        return comparison
    
    def _cleanup_temp_files(self):
        """Clean up temporary test files."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                import shutil
                shutil.rmtree(self.temp_dir)
                logger.info(f"Cleaned up temporary directory: {self.temp_dir}")
            except Exception as e:
                logger.warning(f"Could not clean up temp directory: {e}")
    
    def _compile_results(self) -> Dict[str, Any]:
        """Compile final benchmark results."""
        total_duration = (self.end_time - self.start_time).total_seconds() if self.end_time and self.start_time else 0
        
        final_results = {
            'benchmark_info': {
                'version': '1.0.0',
                'timestamp': self.start_time.isoformat() if self.start_time else None,
                'duration_seconds': total_duration,
                'config': asdict(self.config)
            },
            'system_info': asdict(self.system_info) if self.system_info else {},
            'results': self.results
        }
        
        # Calculate summary statistics
        summary = self._calculate_summary_stats()
        final_results['summary'] = summary
        
        return final_results
    
    def _calculate_summary_stats(self) -> Dict[str, Any]:
        """Calculate summary statistics from all results."""
        summary = {
            'total_tests': 0,
            'successful_tests': 0,
            'failed_tests': 0,
            'gpu_accelerated_tests': 0,
            'average_throughput_mb_s': 0.0,
            'categories': {}
        }
        
        def process_result_category(category_results, category_name):
            if isinstance(category_results, dict):
                cat_stats = {
                    'total': 0,
                    'successful': 0,
                    'failed': 0,
                    'gpu_accelerated': 0
                }
                
                for result_name, result in category_results.items():
                    if isinstance(result, dict) and 'success' in result:
                        cat_stats['total'] += 1
                        summary['total_tests'] += 1
                        
                        if result['success']:
                            cat_stats['successful'] += 1
                            summary['successful_tests'] += 1
                        else:
                            cat_stats['failed'] += 1
                            summary['failed_tests'] += 1
                        
                        if result.get('gpu_accelerated', False):
                            cat_stats['gpu_accelerated'] += 1
                            summary['gpu_accelerated_tests'] += 1
                
                summary['categories'][category_name] = cat_stats
        
        # Process each category
        for category_name, category_results in self.results.items():
            process_result_category(category_results, category_name)
        
        # Calculate success rate
        if summary['total_tests'] > 0:
            summary['success_rate'] = summary['successful_tests'] / summary['total_tests']
            summary['gpu_utilization_rate'] = summary['gpu_accelerated_tests'] / summary['total_tests']
        
        return summary


def main():
    """Main benchmark execution function."""
    parser = argparse.ArgumentParser(description='GPU Benchmark Suite for FileOrganizer')
    parser.add_argument('--hardware-only', action='store_true', help='Run only hardware detection tests')
    parser.add_argument('--performance-only', action='store_true', help='Run only performance benchmarks')
    parser.add_argument('--quick', action='store_true', help='Run quick benchmark (reduced test data)')
    parser.add_argument('--output', type=str, help='Save results to JSON file')
    parser.add_argument('--compare', type=str, help='Compare with previous benchmark file')
    parser.add_argument('--profile', action='store_true', help='Enable detailed profiling')
    parser.add_argument('--gpu-backend', type=str, choices=['cuda', 'opencl', 'auto'], default='auto',
                       help='Force specific GPU backend')
    parser.add_argument('--iterations', type=int, default=3, help='Number of iterations for each test')
    parser.add_argument('--timeout', type=int, default=300, help='Timeout in seconds')
    
    args = parser.parse_args()
    
    # Create benchmark configuration
    config = BenchmarkConfig(
        hardware_only=args.hardware_only,
        performance_only=args.performance_only,
        quick=args.quick,
        full=not args.quick,
        output_file=args.output,
        compare_file=args.compare,
        enable_profiling=args.profile,
        gpu_backend=args.gpu_backend,
        iterations=args.iterations,
        timeout_seconds=args.timeout
    )
    
    print(f"FileOrganizer GPU Benchmark Suite")
    print(f"=" * 50)
    print(f"Configuration:")
    print(f"  Hardware Only: {config.hardware_only}")
    print(f"  Performance Only: {config.performance_only}")
    print(f"  Quick Mode: {config.quick}")
    print(f"  GPU Backend: {config.gpu_backend}")
    print(f"  Iterations: {config.iterations}")
    print(f"  Timeout: {config.timeout_seconds}s")
    print()
    
    # Run benchmark suite
    benchmark_suite = GPUBenchmarkSuite(config)
    
    try:
        results = benchmark_suite.run_complete_benchmark()
        
        # Print summary
        print("\nBenchmark Results Summary:")
        print("=" * 50)
        
        summary = results.get('summary', {})
        print(f"Total Tests: {summary.get('total_tests', 0)}")
        print(f"Successful: {summary.get('successful_tests', 0)}")
        print(f"Failed: {summary.get('failed_tests', 0)}")
        print(f"Success Rate: {summary.get('success_rate', 0):.1%}")
        print(f"GPU Accelerated: {summary.get('gpu_accelerated_tests', 0)}")
        print(f"GPU Utilization: {summary.get('gpu_utilization_rate', 0):.1%}")
        
        # Print category breakdown
        categories = summary.get('categories', {})
        if categories:
            print("\nCategory Breakdown:")
            for cat_name, cat_stats in categories.items():
                print(f"  {cat_name}: {cat_stats['successful']}/{cat_stats['total']} successful")
        
        # Print performance highlights
        performance_results = results.get('results', {}).get('performance', {})
        if performance_results:
            print("\nPerformance Highlights:")
            for test_name, result in performance_results.items():
                if isinstance(result, dict) and result.get('success'):
                    throughput = result.get('throughput_mb_s', 0)
                    gpu_accel = result.get('gpu_accelerated', False)
                    status = "GPU" if gpu_accel else "CPU"
                    if throughput > 0:
                        print(f"  {test_name}: {throughput:.1f} MB/s ({status})")
        
        # Save results if requested
        if config.output_file:
            try:
                with open(config.output_file, 'w') as f:
                    json.dump(results, f, indent=2, default=str)
                print(f"\nResults saved to: {config.output_file}")
            except Exception as e:
                print(f"\nError saving results: {e}")
        
        # Show comparison results if available
        regression_results = results.get('results', {}).get('regression', {})
        if regression_results and 'summary' in regression_results:
            reg_summary = regression_results['summary']
            print(f"\nRegression Analysis:")
            print(f"  Regressions: {reg_summary.get('regressions', 0)}")
            print(f"  Improvements: {reg_summary.get('improvements', 0)}")
            
            if reg_summary.get('regression_tests'):
                print(f"  Regression Tests: {', '.join(reg_summary['regression_tests'])}")
        
        # Exit with appropriate code
        if summary.get('failed_tests', 0) > 0:
            print(f"\nWARNING: {summary['failed_tests']} tests failed")
            sys.exit(1)
        else:
            print(f"\nAll tests passed successfully!")
            sys.exit(0)
            
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
        sys.exit(2)
    except Exception as e:
        print(f"\nBenchmark failed with error: {e}")
        traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()