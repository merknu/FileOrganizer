# file_handler/gpu_acceleration.py
"""
GPU Acceleration Core Module for FileOrganizer
Provides GPU detection, initialization, and management for CUDA and OpenCL backends.
"""

import os
import sys
import logging
import time
from enum import Enum
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
import platform
import subprocess

# Try importing GPU libraries
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logging.warning("NumPy not available. GPU acceleration will be limited.")

try:
    import cupy as cp
    HAS_CUPY = True
except ImportError:
    HAS_CUPY = False
    cp = None

try:
    import pyopencl as cl
    HAS_OPENCL = True
except ImportError:
    HAS_OPENCL = False
    cl = None

try:
    import pycuda.driver as cuda
    import pycuda.autoinit
    from pycuda.compiler import SourceModule
    HAS_PYCUDA = True
except ImportError:
    HAS_PYCUDA = False
    cuda = None


class GPUBackend(Enum):
    """Available GPU backends"""
    NONE = "none"
    CUDA = "cuda"
    OPENCL = "opencl"
    AUTO = "auto"


class GPUMemoryMode(Enum):
    """GPU memory management modes"""
    CONSERVATIVE = "conservative"  # Use minimal GPU memory
    BALANCED = "balanced"         # Use moderate GPU memory
    AGGRESSIVE = "aggressive"     # Use maximum available GPU memory


@dataclass
class GPUDevice:
    """GPU device information"""
    backend: GPUBackend
    device_id: int
    name: str
    memory_total: int  # in MB
    memory_available: int  # in MB
    compute_capability: Optional[str] = None
    opencl_version: Optional[str] = None
    driver_version: Optional[str] = None
    is_available: bool = True


@dataclass
class GPUBenchmark:
    """GPU performance benchmark results"""
    backend: GPUBackend
    device_name: str
    hash_throughput_mb_s: float
    image_processing_fps: float
    memory_bandwidth_gb_s: float
    initialization_time_ms: float
    benchmark_timestamp: str


class GPUAccelerator:
    """Main GPU acceleration manager"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # GPU state
        self.backend = GPUBackend.NONE
        self.device = None
        self.context = None
        self.available_devices: List[GPUDevice] = []
        
        # Performance tracking
        self.benchmarks: List[GPUBenchmark] = []
        self.operations_count = 0
        self.total_processing_time = 0.0
        
        # Configuration
        self.memory_mode = GPUMemoryMode(self.config.get('memory_mode', 'balanced'))
        self.preferred_backend = GPUBackend(self.config.get('backend', 'auto'))
        self.enable_gpu = self.config.get('enable_gpu', True)
        self.chunk_size_mb = self.config.get('chunk_size_mb', 64)
        self.max_gpu_memory_usage = self.config.get('max_gpu_memory_usage', 0.8)
        
        if self.enable_gpu:
            self.initialize()

    def initialize(self) -> bool:
        """Initialize GPU acceleration"""
        start_time = time.time()
        
        try:
            self.logger.info("Initializing GPU acceleration...")
            
            # Detect available GPU devices
            self._detect_devices()
            
            if not self.available_devices:
                self.logger.warning("No GPU devices detected. Using CPU fallback.")
                return False
            
            # Select best device
            selected_device = self._select_best_device()
            if not selected_device:
                self.logger.warning("No suitable GPU device found. Using CPU fallback.")
                return False
            
            # Initialize backend
            success = self._initialize_backend(selected_device)
            
            if success:
                init_time = (time.time() - start_time) * 1000
                self.logger.info(f"GPU acceleration initialized successfully in {init_time:.1f}ms")
                self.logger.info(f"Using {selected_device.backend.value.upper()} backend on {selected_device.name}")
                
                # Run initial benchmark
                if self.config.get('run_initial_benchmark', True):
                    self._run_quick_benchmark()
                
                return True
            else:
                self.logger.error("Failed to initialize GPU backend")
                return False
                
        except Exception as e:
            self.logger.error(f"GPU initialization failed: {e}")
            return False

    def _detect_devices(self) -> None:
        """Detect available GPU devices"""
        self.available_devices = []
        
        # Detect CUDA devices
        if HAS_CUPY or HAS_PYCUDA:
            cuda_devices = self._detect_cuda_devices()
            self.available_devices.extend(cuda_devices)
        
        # Detect OpenCL devices
        if HAS_OPENCL:
            opencl_devices = self._detect_opencl_devices()
            self.available_devices.extend(opencl_devices)
        
        self.logger.info(f"Detected {len(self.available_devices)} GPU devices")
        for device in self.available_devices:
            self.logger.info(f"  - {device.backend.value.upper()}: {device.name} "
                           f"({device.memory_total}MB)")

    def _detect_cuda_devices(self) -> List[GPUDevice]:
        """Detect CUDA-capable devices"""
        devices = []
        
        try:
            if HAS_CUPY:
                # Use CuPy for device detection
                device_count = cp.cuda.runtime.getDeviceCount()
                for i in range(device_count):
                    with cp.cuda.Device(i):
                        props = cp.cuda.runtime.getDeviceProperties(i)
                        meminfo = cp.cuda.runtime.memGetInfo()
                        
                        device = GPUDevice(
                            backend=GPUBackend.CUDA,
                            device_id=i,
                            name=props['name'].decode('utf-8'),
                            memory_total=props['totalGlobalMem'] // (1024 * 1024),
                            memory_available=meminfo[0] // (1024 * 1024),
                            compute_capability=f"{props['major']}.{props['minor']}"
                        )
                        devices.append(device)
                        
            elif HAS_PYCUDA:
                # Use PyCUDA for device detection
                cuda.init()
                device_count = cuda.Device.count()
                for i in range(device_count):
                    device_handle = cuda.Device(i)
                    attrs = device_handle.get_attributes()
                    
                    # Get memory info
                    context = device_handle.make_context()
                    mem_gpu = cuda.mem_get_info()
                    context.pop()
                    
                    device = GPUDevice(
                        backend=GPUBackend.CUDA,
                        device_id=i,
                        name=device_handle.name(),
                        memory_total=mem_gpu[1] // (1024 * 1024),
                        memory_available=mem_gpu[0] // (1024 * 1024),
                        compute_capability=f"{attrs[cuda.device_attribute.COMPUTE_CAPABILITY_MAJOR]}."
                                         f"{attrs[cuda.device_attribute.COMPUTE_CAPABILITY_MINOR]}"
                    )
                    devices.append(device)
                    
        except Exception as e:
            self.logger.warning(f"Error detecting CUDA devices: {e}")
        
        return devices

    def _detect_opencl_devices(self) -> List[GPUDevice]:
        """Detect OpenCL-capable devices"""
        devices = []
        
        try:
            platforms = cl.get_platforms()
            for platform in platforms:
                try:
                    gpu_devices = platform.get_devices(device_type=cl.device_type.GPU)
                    for i, dev in enumerate(gpu_devices):
                        memory_mb = dev.global_mem_size // (1024 * 1024)
                        
                        device = GPUDevice(
                            backend=GPUBackend.OPENCL,
                            device_id=i,
                            name=dev.name.strip(),
                            memory_total=memory_mb,
                            memory_available=memory_mb,  # OpenCL doesn't provide available memory
                            opencl_version=dev.opencl_c_version,
                            driver_version=dev.driver_version
                        )
                        devices.append(device)
                        
                except Exception as e:
                    self.logger.warning(f"Error querying OpenCL platform {platform.name}: {e}")
                    
        except Exception as e:
            self.logger.warning(f"Error detecting OpenCL devices: {e}")
        
        return devices

    def _select_best_device(self) -> Optional[GPUDevice]:
        """Select the best available GPU device"""
        if not self.available_devices:
            return None
        
        # Filter by backend preference
        preferred_devices = self.available_devices
        if self.preferred_backend != GPUBackend.AUTO:
            preferred_devices = [d for d in self.available_devices 
                               if d.backend == self.preferred_backend]
            if not preferred_devices:
                self.logger.warning(f"Preferred backend {self.preferred_backend.value} not available")
                preferred_devices = self.available_devices
        
        # Score devices based on memory and capabilities
        def score_device(device: GPUDevice) -> float:
            score = device.memory_total * 1.0  # Base score from memory
            
            # Prefer CUDA over OpenCL (generally better performance)
            if device.backend == GPUBackend.CUDA:
                score *= 1.2
            
            # Prefer devices with more available memory
            if device.memory_available > 0:
                availability_ratio = device.memory_available / device.memory_total
                score *= (0.5 + availability_ratio)
            
            return score
        
        # Select highest scoring device
        best_device = max(preferred_devices, key=score_device)
        self.logger.info(f"Selected GPU device: {best_device.name} ({best_device.backend.value.upper()})")
        
        return best_device

    def _initialize_backend(self, device: GPUDevice) -> bool:
        """Initialize the selected GPU backend"""
        try:
            if device.backend == GPUBackend.CUDA:
                return self._initialize_cuda(device)
            elif device.backend == GPUBackend.OPENCL:
                return self._initialize_opencl(device)
            else:
                self.logger.error(f"Unsupported backend: {device.backend}")
                return False
                
        except Exception as e:
            self.logger.error(f"Backend initialization failed: {e}")
            return False

    def _initialize_cuda(self, device: GPUDevice) -> bool:
        """Initialize CUDA backend"""
        try:
            if HAS_CUPY:
                cp.cuda.Device(device.device_id).use()
                self.backend = GPUBackend.CUDA
                self.device = device
                self.logger.info("CUDA backend initialized with CuPy")
                return True
                
            elif HAS_PYCUDA:
                cuda_device = cuda.Device(device.device_id)
                self.context = cuda_device.make_context()
                self.backend = GPUBackend.CUDA
                self.device = device
                self.logger.info("CUDA backend initialized with PyCUDA")
                return True
                
            else:
                self.logger.error("No CUDA library available")
                return False
                
        except Exception as e:
            self.logger.error(f"CUDA initialization failed: {e}")
            return False

    def _initialize_opencl(self, device: GPUDevice) -> bool:
        """Initialize OpenCL backend"""
        try:
            platforms = cl.get_platforms()
            for platform in platforms:
                devices = platform.get_devices(device_type=cl.device_type.GPU)
                for i, dev in enumerate(devices):
                    if dev.name.strip() == device.name and i == device.device_id:
                        self.context = cl.Context([dev])
                        self.backend = GPUBackend.OPENCL
                        self.device = device
                        self.logger.info("OpenCL backend initialized")
                        return True
            
            self.logger.error("Could not find matching OpenCL device")
            return False
            
        except Exception as e:
            self.logger.error(f"OpenCL initialization failed: {e}")
            return False

    def _run_quick_benchmark(self) -> None:
        """Run a quick performance benchmark"""
        try:
            self.logger.info("Running GPU performance benchmark...")
            start_time = time.time()
            
            # Simple memory bandwidth test
            test_size_mb = min(64, self.device.memory_available // 4)
            test_data = np.random.rand(test_size_mb * 1024 * 1024 // 8).astype(np.float64)
            
            if self.backend == GPUBackend.CUDA and HAS_CUPY:
                # CuPy benchmark
                gpu_data = cp.asarray(test_data)
                cp.cuda.Stream.null.synchronize()  # Wait for transfer
                
                # Simple computation benchmark
                bench_start = time.time()
                result = cp.sum(gpu_data * gpu_data)
                cp.cuda.Stream.null.synchronize()
                bench_time = time.time() - bench_start
                
                # Calculate throughput
                throughput = (test_size_mb * 2) / bench_time  # Read + write
                
            else:
                # Fallback CPU benchmark for comparison
                bench_start = time.time()
                result = np.sum(test_data * test_data)
                bench_time = time.time() - bench_start
                throughput = (test_size_mb * 2) / bench_time
            
            total_time = (time.time() - start_time) * 1000
            
            benchmark = GPUBenchmark(
                backend=self.backend,
                device_name=self.device.name,
                hash_throughput_mb_s=throughput * 0.7,  # Estimate for hashing
                image_processing_fps=throughput * 10,   # Estimate for image ops
                memory_bandwidth_gb_s=throughput / 1024,
                initialization_time_ms=total_time,
                benchmark_timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            
            self.benchmarks.append(benchmark)
            self.logger.info(f"Benchmark completed: {throughput:.1f} MB/s memory bandwidth")
            
        except Exception as e:
            self.logger.warning(f"Benchmark failed: {e}")

    def is_available(self) -> bool:
        """Check if GPU acceleration is available"""
        return self.backend != GPUBackend.NONE and self.device is not None

    def get_device_info(self) -> Optional[GPUDevice]:
        """Get current GPU device information"""
        return self.device
    
    def get_backend(self) -> GPUBackend:
        """Get current GPU backend in use"""
        return self.backend

    def get_memory_usage(self) -> Tuple[int, int]:
        """Get current GPU memory usage (used, total) in MB"""
        if not self.is_available():
            return (0, 0)
        
        try:
            if self.backend == GPUBackend.CUDA:
                if HAS_CUPY:
                    mempool = cp.get_default_memory_pool()
                    used = mempool.used_bytes() // (1024 * 1024)
                    total = self.device.memory_total
                    return (used, total)
                elif HAS_PYCUDA and self.context:
                    mem_gpu = cuda.mem_get_info()
                    used = (mem_gpu[1] - mem_gpu[0]) // (1024 * 1024)
                    total = mem_gpu[1] // (1024 * 1024)
                    return (used, total)
            
            # Fallback - return device memory info
            return (0, self.device.memory_total)
            
        except Exception as e:
            self.logger.warning(f"Error getting memory usage: {e}")
            return (0, 0)

    def cleanup(self) -> None:
        """Clean up GPU resources"""
        try:
            if self.backend == GPUBackend.CUDA:
                if HAS_CUPY:
                    # CuPy cleanup
                    mempool = cp.get_default_memory_pool()
                    mempool.free_all_blocks()
                elif HAS_PYCUDA and self.context:
                    # PyCUDA cleanup
                    self.context.pop()
                    
            elif self.backend == GPUBackend.OPENCL and self.context:
                # OpenCL cleanup
                self.context = None
            
            self.logger.info("GPU resources cleaned up")
            
        except Exception as e:
            self.logger.warning(f"Error during GPU cleanup: {e}")

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        stats = {
            'backend': self.backend.value,
            'device_name': self.device.name if self.device else 'None',
            'operations_count': self.operations_count,
            'total_processing_time': self.total_processing_time,
            'average_operation_time': (self.total_processing_time / self.operations_count 
                                     if self.operations_count > 0 else 0),
            'benchmarks': [vars(b) for b in self.benchmarks],
            'memory_usage': self.get_memory_usage()
        }
        return stats

    def __del__(self):
        """Destructor - cleanup GPU resources"""
        try:
            self.cleanup()
        except:
            pass  # Ignore cleanup errors during destruction


def get_system_gpu_info() -> Dict[str, Any]:
    """Get detailed system GPU information"""
    info = {
        'platform': platform.system(),
        'python_version': sys.version,
        'libraries': {
            'numpy': HAS_NUMPY,
            'cupy': HAS_CUPY,
            'pycuda': HAS_PYCUDA,
            'pyopencl': HAS_OPENCL
        },
        'cuda_available': False,
        'opencl_available': False,
        'devices': []
    }
    
    # Check CUDA availability
    if HAS_CUPY:
        try:
            info['cuda_available'] = cp.cuda.runtime.getDeviceCount() > 0
        except:
            info['cuda_available'] = False
    elif HAS_PYCUDA:
        try:
            cuda.init()
            info['cuda_available'] = cuda.Device.count() > 0
        except:
            info['cuda_available'] = False
    
    # Check OpenCL availability
    if HAS_OPENCL:
        try:
            platforms = cl.get_platforms()
            info['opencl_available'] = any(
                len(p.get_devices(device_type=cl.device_type.GPU)) > 0 
                for p in platforms
            )
        except:
            info['opencl_available'] = False
    
    return info


# Global GPU accelerator instance
_gpu_accelerator: Optional[GPUAccelerator] = None


def get_gpu_accelerator(config: Optional[Dict[str, Any]] = None) -> GPUAccelerator:
    """Get or create the global GPU accelerator instance"""
    global _gpu_accelerator
    
    if _gpu_accelerator is None:
        _gpu_accelerator = GPUAccelerator(config)
    
    return _gpu_accelerator


def initialize_gpu_acceleration(config: Optional[Dict[str, Any]] = None) -> bool:
    """Initialize GPU acceleration globally"""
    accelerator = get_gpu_accelerator(config)
    return accelerator.is_available()


# Module-level initialization for testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("FileOrganizer GPU Acceleration Test")
    print("=" * 50)
    
    # System info
    sys_info = get_system_gpu_info()
    print(f"Platform: {sys_info['platform']}")
    print(f"Libraries: {sys_info['libraries']}")
    print(f"CUDA Available: {sys_info['cuda_available']}")
    print(f"OpenCL Available: {sys_info['opencl_available']}")
    print()
    
    # Test GPU initialization
    config = {
        'enable_gpu': True,
        'backend': 'auto',
        'memory_mode': 'balanced',
        'run_initial_benchmark': True
    }
    
    accelerator = GPUAccelerator(config)
    
    if accelerator.is_available():
        print("GPU Acceleration Status: ENABLED")
        device = accelerator.get_device_info()
        print(f"Device: {device.name}")
        print(f"Backend: {device.backend.value.upper()}")
        print(f"Memory: {device.memory_total}MB total")
        
        # Performance stats
        stats = accelerator.get_performance_stats()
        if stats['benchmarks']:
            bench = stats['benchmarks'][-1]
            print(f"Benchmark: {bench['memory_bandwidth_gb_s']:.2f} GB/s")
        
        memory_used, memory_total = accelerator.get_memory_usage()
        print(f"Memory Usage: {memory_used}MB / {memory_total}MB")
        
    else:
        print("GPU Acceleration Status: DISABLED (using CPU fallback)")
    
    print("\nTest completed successfully!")