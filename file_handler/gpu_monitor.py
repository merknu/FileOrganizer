# file_handler/gpu_monitor.py
"""
GPU Status Monitoring and Performance Benchmarking Module for FileOrganizer
Provides real-time monitoring, performance tracking, and system optimization recommendations.
"""

import os
import time
import json
import threading
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable, Any, Tuple
from collections import deque, defaultdict
import statistics

# System monitoring
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

# GPU-specific monitoring
try:
    import GPUtil
    HAS_GPUTIL = True
except ImportError:
    HAS_GPUTIL = False

try:
    import py3nvml.py3nvml as nvml
    HAS_NVML = True
except ImportError:
    HAS_NVML = False

# GPU acceleration imports
try:
    from .gpu_acceleration import get_gpu_accelerator, GPUAccelerator, GPUBenchmark
    from .gpu_hasher import GPUHasher
    from .gpu_image_processor import GPUImageProcessor
    HAS_GPU_MODULES = True
except ImportError:
    HAS_GPU_MODULES = False


@dataclass
class SystemMetrics:
    """System performance metrics"""
    timestamp: str
    cpu_percent: float
    memory_used_mb: float
    memory_total_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_sent_mb: float
    network_recv_mb: float


@dataclass
class GPUMetrics:
    """GPU performance metrics"""
    timestamp: str
    gpu_id: int
    name: str
    utilization_percent: float
    memory_used_mb: float
    memory_total_mb: float
    temperature_c: float
    power_draw_w: float
    fan_speed_percent: float
    clock_graphics_mhz: float
    clock_memory_mhz: float


@dataclass
class PerformanceStats:
    """Performance statistics for FileOrganizer operations"""
    operation_type: str
    start_time: str
    end_time: str
    duration_seconds: float
    files_processed: int
    bytes_processed: int
    gpu_accelerated: bool
    throughput_mb_s: float
    success_rate: float
    error_count: int


class GPUMonitor:
    """Real-time GPU monitoring and performance tracking"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        
        # Configuration
        self.monitoring_enabled = self.config.get('enable_monitoring', True)
        self.monitoring_interval = self.config.get('monitoring_interval_seconds', 1.0)
        self.metrics_history_size = self.config.get('metrics_history_size', 1000)
        self.benchmark_interval_hours = self.config.get('benchmark_interval_hours', 24)
        self.alert_thresholds = self.config.get('alert_thresholds', {
            'gpu_utilization': 95.0,
            'gpu_memory': 90.0,
            'gpu_temperature': 80.0,
            'system_memory': 85.0
        })
        
        # Data storage
        self.system_metrics_history = deque(maxlen=self.metrics_history_size)
        self.gpu_metrics_history = deque(maxlen=self.metrics_history_size)
        self.performance_stats = []
        self.benchmarks = []
        self.alerts = []
        
        # Monitoring state
        self.monitoring_thread = None
        self.monitoring_active = False
        self.last_benchmark_time = None
        self.alert_callbacks: List[Callable] = []
        
        # Initialize GPU monitoring
        self._initialize_gpu_monitoring()
        
        # Start monitoring if enabled
        if self.monitoring_enabled:
            self.start_monitoring()

    def _initialize_gpu_monitoring(self):
        """Initialize GPU monitoring libraries"""
        self.gpu_monitoring_available = False
        self.nvidia_monitoring = False
        
        # Try to initialize NVIDIA monitoring
        if HAS_NVML:
            try:
                nvml.nvmlInit()
                self.nvidia_monitoring = True
                self.gpu_monitoring_available = True
                device_count = nvml.nvmlDeviceGetCount()
                self.logger.info(f"NVIDIA GPU monitoring initialized: {device_count} devices")
            except Exception as e:
                self.logger.warning(f"NVIDIA monitoring initialization failed: {e}")
        
        # Fallback to GPUtil
        if not self.gpu_monitoring_available and HAS_GPUTIL:
            try:
                gpus = GPUtil.getGPUs()
                if gpus:
                    self.gpu_monitoring_available = True
                    self.logger.info(f"GPU monitoring initialized via GPUtil: {len(gpus)} devices")
            except Exception as e:
                self.logger.warning(f"GPUtil initialization failed: {e}")
        
        if not self.gpu_monitoring_available:
            self.logger.info("GPU monitoring not available")

    def start_monitoring(self):
        """Start background monitoring thread"""
        if self.monitoring_active:
            self.logger.warning("Monitoring already active")
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("GPU monitoring started")

    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=2.0)
        self.logger.info("GPU monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                if system_metrics:
                    self.system_metrics_history.append(system_metrics)
                
                # Collect GPU metrics
                gpu_metrics = self._collect_gpu_metrics()
                for metric in gpu_metrics:
                    self.gpu_metrics_history.append(metric)
                
                # Check for alerts
                self._check_alerts(system_metrics, gpu_metrics)
                
                # Auto-benchmark if needed
                self._check_auto_benchmark()
                
                # Sleep until next interval
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.monitoring_interval)

    def _collect_system_metrics(self) -> Optional[SystemMetrics]:
        """Collect system performance metrics"""
        if not HAS_PSUTIL:
            return None
        
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            
            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read_mb = (disk_io.read_bytes / (1024 * 1024)) if disk_io else 0
            disk_write_mb = (disk_io.write_bytes / (1024 * 1024)) if disk_io else 0
            
            # Network I/O
            network_io = psutil.net_io_counters()
            network_sent_mb = (network_io.bytes_sent / (1024 * 1024)) if network_io else 0
            network_recv_mb = (network_io.bytes_recv / (1024 * 1024)) if network_io else 0
            
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu_percent=cpu_percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_total_mb=memory.total / (1024 * 1024),
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_sent_mb=network_sent_mb,
                network_recv_mb=network_recv_mb
            )
            
        except Exception as e:
            self.logger.warning(f"Error collecting system metrics: {e}")
            return None

    def _collect_gpu_metrics(self) -> List[GPUMetrics]:
        """Collect GPU performance metrics"""
        metrics = []
        
        if not self.gpu_monitoring_available:
            return metrics
        
        try:
            if self.nvidia_monitoring and HAS_NVML:
                metrics.extend(self._collect_nvidia_metrics())
            elif HAS_GPUTIL:
                metrics.extend(self._collect_gputil_metrics())
                
        except Exception as e:
            self.logger.warning(f"Error collecting GPU metrics: {e}")
        
        return metrics

    def _collect_nvidia_metrics(self) -> List[GPUMetrics]:
        """Collect metrics using NVIDIA ML library"""
        metrics = []
        
        try:
            device_count = nvml.nvmlDeviceGetCount()
            
            for i in range(device_count):
                handle = nvml.nvmlDeviceGetHandleByIndex(i)
                
                # Basic info
                name = nvml.nvmlDeviceGetName(handle).decode('utf-8')
                
                # Utilization
                utilization = nvml.nvmlDeviceGetUtilizationRates(handle)
                
                # Memory
                memory_info = nvml.nvmlDeviceGetMemoryInfo(handle)
                
                # Temperature
                try:
                    temperature = nvml.nvmlDeviceGetTemperature(handle, nvml.NVML_TEMPERATURE_GPU)
                except:
                    temperature = 0
                
                # Power
                try:
                    power_draw = nvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # Convert to watts
                except:
                    power_draw = 0
                
                # Fan speed
                try:
                    fan_speed = nvml.nvmlDeviceGetFanSpeed(handle)
                except:
                    fan_speed = 0
                
                # Clock speeds
                try:
                    graphics_clock = nvml.nvmlDeviceGetClockInfo(handle, nvml.NVML_CLOCK_GRAPHICS)
                    memory_clock = nvml.nvmlDeviceGetClockInfo(handle, nvml.NVML_CLOCK_MEM)
                except:
                    graphics_clock = memory_clock = 0
                
                metrics.append(GPUMetrics(
                    timestamp=datetime.now().isoformat(),
                    gpu_id=i,
                    name=name,
                    utilization_percent=utilization.gpu,
                    memory_used_mb=memory_info.used / (1024 * 1024),
                    memory_total_mb=memory_info.total / (1024 * 1024),
                    temperature_c=temperature,
                    power_draw_w=power_draw,
                    fan_speed_percent=fan_speed,
                    clock_graphics_mhz=graphics_clock,
                    clock_memory_mhz=memory_clock
                ))
                
        except Exception as e:
            self.logger.warning(f"Error collecting NVIDIA metrics: {e}")
        
        return metrics

    def _collect_gputil_metrics(self) -> List[GPUMetrics]:
        """Collect metrics using GPUtil"""
        metrics = []
        
        try:
            gpus = GPUtil.getGPUs()
            
            for gpu in gpus:
                metrics.append(GPUMetrics(
                    timestamp=datetime.now().isoformat(),
                    gpu_id=gpu.id,
                    name=gpu.name,
                    utilization_percent=gpu.load * 100,
                    memory_used_mb=gpu.memoryUsed,
                    memory_total_mb=gpu.memoryTotal,
                    temperature_c=gpu.temperature,
                    power_draw_w=0,  # Not available in GPUtil
                    fan_speed_percent=0,  # Not available in GPUtil
                    clock_graphics_mhz=0,  # Not available in GPUtil
                    clock_memory_mhz=0  # Not available in GPUtil
                ))
                
        except Exception as e:
            self.logger.warning(f"Error collecting GPUtil metrics: {e}")
        
        return metrics

    def _check_alerts(self, system_metrics: Optional[SystemMetrics], 
                     gpu_metrics: List[GPUMetrics]):
        """Check for performance alerts"""
        current_time = datetime.now()
        alerts_triggered = []
        
        # System alerts
        if system_metrics:
            if system_metrics.memory_used_mb / system_metrics.memory_total_mb * 100 > self.alert_thresholds['system_memory']:
                alerts_triggered.append({
                    'type': 'system_memory_high',
                    'message': f"System memory usage high: {system_metrics.memory_used_mb/system_metrics.memory_total_mb*100:.1f}%",
                    'severity': 'warning',
                    'timestamp': current_time.isoformat()
                })
        
        # GPU alerts
        for gpu_metric in gpu_metrics:
            if gpu_metric.utilization_percent > self.alert_thresholds['gpu_utilization']:
                alerts_triggered.append({
                    'type': 'gpu_utilization_high',
                    'message': f"GPU {gpu_metric.gpu_id} utilization high: {gpu_metric.utilization_percent:.1f}%",
                    'severity': 'info',
                    'timestamp': current_time.isoformat()
                })
            
            memory_usage_percent = gpu_metric.memory_used_mb / gpu_metric.memory_total_mb * 100
            if memory_usage_percent > self.alert_thresholds['gpu_memory']:
                alerts_triggered.append({
                    'type': 'gpu_memory_high',
                    'message': f"GPU {gpu_metric.gpu_id} memory usage high: {memory_usage_percent:.1f}%",
                    'severity': 'warning',
                    'timestamp': current_time.isoformat()
                })
            
            if gpu_metric.temperature_c > self.alert_thresholds['gpu_temperature']:
                alerts_triggered.append({
                    'type': 'gpu_temperature_high',
                    'message': f"GPU {gpu_metric.gpu_id} temperature high: {gpu_metric.temperature_c:.1f}°C",
                    'severity': 'critical',
                    'timestamp': current_time.isoformat()
                })
        
        # Store and notify alerts
        for alert in alerts_triggered:
            self.alerts.append(alert)
            self.logger.warning(f"Alert: {alert['message']}")
            
            # Call registered alert callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(alert)
                except Exception as e:
                    self.logger.error(f"Error in alert callback: {e}")

    def _check_auto_benchmark(self):
        """Check if auto-benchmark should be run"""
        if not self.last_benchmark_time:
            return
        
        next_benchmark = self.last_benchmark_time + timedelta(hours=self.benchmark_interval_hours)
        if datetime.now() >= next_benchmark:
            self.logger.info("Running scheduled benchmark")
            try:
                self.run_comprehensive_benchmark()
            except Exception as e:
                self.logger.error(f"Auto-benchmark failed: {e}")

    def record_performance_stats(self, operation_type: str, start_time: datetime,
                                end_time: datetime, files_processed: int,
                                bytes_processed: int, gpu_accelerated: bool,
                                success_count: int, error_count: int):
        """Record performance statistics for an operation"""
        duration = (end_time - start_time).total_seconds()
        throughput = (bytes_processed / (1024 * 1024)) / duration if duration > 0 else 0
        success_rate = success_count / (success_count + error_count) if (success_count + error_count) > 0 else 0
        
        stats = PerformanceStats(
            operation_type=operation_type,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            duration_seconds=duration,
            files_processed=files_processed,
            bytes_processed=bytes_processed,
            gpu_accelerated=gpu_accelerated,
            throughput_mb_s=throughput,
            success_rate=success_rate,
            error_count=error_count
        )
        
        self.performance_stats.append(stats)
        self.logger.info(f"Performance recorded: {operation_type} - "
                        f"{throughput:.1f} MB/s, {success_rate:.1%} success rate")

    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive performance benchmark"""
        self.logger.info("Starting comprehensive GPU benchmark...")
        benchmark_start = time.time()
        
        benchmark_results = {
            'timestamp': datetime.now().isoformat(),
            'system_info': self._get_system_info(),
            'gpu_info': self._get_gpu_info(),
            'tests': {}
        }
        
        try:
            # GPU acceleration availability test
            if HAS_GPU_MODULES:
                gpu_accelerator = get_gpu_accelerator()
                if gpu_accelerator.is_available():
                    benchmark_results['tests']['gpu_availability'] = {
                        'available': True,
                        'backend': gpu_accelerator.backend.value,
                        'device': gpu_accelerator.device.name if gpu_accelerator.device else 'Unknown'
                    }
                    
                    # Memory bandwidth test
                    memory_test = self._benchmark_memory_bandwidth(gpu_accelerator)
                    benchmark_results['tests']['memory_bandwidth'] = memory_test
                    
                    # File hashing benchmark
                    hash_test = self._benchmark_file_hashing()
                    benchmark_results['tests']['file_hashing'] = hash_test
                    
                    # Image processing benchmark
                    image_test = self._benchmark_image_processing()
                    benchmark_results['tests']['image_processing'] = image_test
                    
                else:
                    benchmark_results['tests']['gpu_availability'] = {
                        'available': False,
                        'reason': 'GPU not available'
                    }
            else:
                benchmark_results['tests']['gpu_availability'] = {
                    'available': False,
                    'reason': 'GPU modules not imported'
                }
            
            # CPU baseline tests
            cpu_test = self._benchmark_cpu_performance()
            benchmark_results['tests']['cpu_baseline'] = cpu_test
            
            benchmark_results['total_time_seconds'] = time.time() - benchmark_start
            benchmark_results['success'] = True
            
            # Store benchmark
            self.benchmarks.append(benchmark_results)
            self.last_benchmark_time = datetime.now()
            
            self.logger.info(f"Benchmark completed in {benchmark_results['total_time_seconds']:.2f} seconds")
            
        except Exception as e:
            benchmark_results['error'] = str(e)
            benchmark_results['success'] = False
            self.logger.error(f"Benchmark failed: {e}")
        
        return benchmark_results

    def _benchmark_memory_bandwidth(self, gpu_accelerator: 'GPUAccelerator') -> Dict[str, Any]:
        """Benchmark GPU memory bandwidth"""
        test_results = {'success': False}
        
        try:
            # This would typically involve GPU-specific memory tests
            # For now, use the built-in benchmark if available
            stats = gpu_accelerator.get_performance_stats()
            if stats['benchmarks']:
                latest_benchmark = stats['benchmarks'][-1]
                test_results.update({
                    'success': True,
                    'memory_bandwidth_gb_s': latest_benchmark['memory_bandwidth_gb_s'],
                    'initialization_time_ms': latest_benchmark['initialization_time_ms']
                })
            else:
                test_results['error'] = 'No benchmark data available'
                
        except Exception as e:
            test_results['error'] = str(e)
        
        return test_results

    def _benchmark_file_hashing(self) -> Dict[str, Any]:
        """Benchmark file hashing performance"""
        test_results = {'success': False}
        
        try:
            if not HAS_GPU_MODULES:
                test_results['error'] = 'GPU modules not available'
                return test_results
            
            # Create test data
            import tempfile
            test_data_size_mb = 100
            test_data = b'0' * (test_data_size_mb * 1024 * 1024)
            
            with tempfile.NamedTemporaryFile() as tmp_file:
                tmp_file.write(test_data)
                tmp_file.flush()
                
                # GPU hashing test
                hasher = GPUHasher()
                gpu_start = time.time()
                gpu_result = hasher.hash_file(tmp_file.name, ['sha256'])
                gpu_time = time.time() - gpu_start
                
                # CPU hashing test for comparison
                from .file_operations import calculate_file_hash
                cpu_start = time.time()
                cpu_result = calculate_file_hash(tmp_file.name)
                cpu_time = time.time() - cpu_start
                
                test_results.update({
                    'success': True,
                    'test_data_size_mb': test_data_size_mb,
                    'gpu_time_seconds': gpu_time,
                    'cpu_time_seconds': cpu_time,
                    'gpu_throughput_mb_s': test_data_size_mb / gpu_time if gpu_time > 0 else 0,
                    'cpu_throughput_mb_s': test_data_size_mb / cpu_time if cpu_time > 0 else 0,
                    'gpu_accelerated': gpu_result.gpu_accelerated,
                    'speedup_ratio': cpu_time / gpu_time if gpu_time > 0 else 0
                })
                
        except Exception as e:
            test_results['error'] = str(e)
        
        return test_results

    def _benchmark_image_processing(self) -> Dict[str, Any]:
        """Benchmark image processing performance"""
        test_results = {'success': False}
        
        try:
            if not HAS_GPU_MODULES:
                test_results['error'] = 'GPU modules not available'
                return test_results
            
            # Create test image
            try:
                from PIL import Image
                import tempfile
                
                test_image = Image.new('RGB', (2048, 1536), color='red')
                with tempfile.NamedTemporaryFile(suffix='.jpg') as tmp_file:
                    test_image.save(tmp_file.name, quality=95)
                    
                    # GPU processing test
                    processor = GPUImageProcessor()
                    gpu_start = time.time()
                    gpu_result = processor.extract_metadata(tmp_file.name)
                    gpu_time = time.time() - gpu_start
                    
                    # CPU processing test
                    from .metadata_handlers import get_file_metadata
                    cpu_start = time.time()
                    cpu_result = get_file_metadata(tmp_file.name, use_gpu=False)
                    cpu_time = time.time() - cpu_start
                    
                    test_results.update({
                        'success': True,
                        'image_size': '2048x1536',
                        'gpu_time_seconds': gpu_time,
                        'cpu_time_seconds': cpu_time,
                        'gpu_accelerated': gpu_result.gpu_accelerated,
                        'speedup_ratio': cpu_time / gpu_time if gpu_time > 0 else 0
                    })
                    
            except ImportError:
                test_results['error'] = 'PIL not available for image test'
                
        except Exception as e:
            test_results['error'] = str(e)
        
        return test_results

    def _benchmark_cpu_performance(self) -> Dict[str, Any]:
        """Benchmark CPU baseline performance"""
        test_results = {'success': False}
        
        try:
            import hashlib
            
            # Simple CPU computation test
            test_data = b'0' * (50 * 1024 * 1024)  # 50MB
            
            start_time = time.time()
            hash_result = hashlib.sha256(test_data).hexdigest()
            end_time = time.time()
            
            cpu_time = end_time - start_time
            throughput = 50 / cpu_time if cpu_time > 0 else 0
            
            test_results.update({
                'success': True,
                'test_data_size_mb': 50,
                'cpu_time_seconds': cpu_time,
                'cpu_throughput_mb_s': throughput,
                'cpu_cores': os.cpu_count()
            })
            
        except Exception as e:
            test_results['error'] = str(e)
        
        return test_results

    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information"""
        info = {
            'platform': os.name,
            'cpu_count': os.cpu_count(),
            'python_version': os.sys.version
        }
        
        if HAS_PSUTIL:
            info.update({
                'total_memory_mb': psutil.virtual_memory().total / (1024 * 1024),
                'cpu_freq_mhz': psutil.cpu_freq().current if psutil.cpu_freq() else 0
            })
        
        return info

    def _get_gpu_info(self) -> Dict[str, Any]:
        """Get GPU information"""
        info = {'gpus': []}
        
        if self.gpu_monitoring_available:
            # Get current GPU metrics as info
            gpu_metrics = self._collect_gpu_metrics()
            for metric in gpu_metrics:
                info['gpus'].append({
                    'id': metric.gpu_id,
                    'name': metric.name,
                    'memory_total_mb': metric.memory_total_mb,
                    'temperature_c': metric.temperature_c
                })
        
        return info

    def get_current_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        status = {
            'monitoring_active': self.monitoring_active,
            'monitoring_available': self.gpu_monitoring_available,
            'metrics_collected': len(self.system_metrics_history),
            'gpu_metrics_collected': len(self.gpu_metrics_history),
            'performance_records': len(self.performance_stats),
            'benchmarks_run': len(self.benchmarks),
            'active_alerts': len([a for a in self.alerts if 
                                datetime.fromisoformat(a['timestamp']) > 
                                datetime.now() - timedelta(hours=1)])
        }
        
        # Latest metrics
        if self.system_metrics_history:
            status['latest_system_metrics'] = asdict(self.system_metrics_history[-1])
        
        if self.gpu_metrics_history:
            status['latest_gpu_metrics'] = [asdict(m) for m in list(self.gpu_metrics_history)[-5:]]
        
        return status

    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current GPU and system metrics"""
        current_metrics = {
            'system': None,
            'gpu': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Get latest system metrics
        if self.system_metrics_history:
            current_metrics['system'] = asdict(self.system_metrics_history[-1])
        
        # Get latest GPU metrics
        if self.gpu_metrics_history:
            current_metrics['gpu'] = [asdict(m) for m in list(self.gpu_metrics_history)[-1:]]
        
        return current_metrics
    
    def get_metrics_history(self, hours: int = 1) -> Dict[str, Any]:
        """Get historical metrics for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        history = {
            'system_metrics': [],
            'gpu_metrics': [],
            'time_range_hours': hours
        }
        
        # Filter system metrics by time
        for metric in self.system_metrics_history:
            if datetime.fromisoformat(metric.timestamp) > cutoff_time:
                history['system_metrics'].append(asdict(metric))
        
        # Filter GPU metrics by time  
        for metric in self.gpu_metrics_history:
            if datetime.fromisoformat(metric.timestamp) > cutoff_time:
                history['gpu_metrics'].append(asdict(metric))
        
        return history

    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Filter recent performance stats
        recent_stats = [
            stat for stat in self.performance_stats
            if datetime.fromisoformat(stat.start_time) > cutoff_time
        ]
        
        if not recent_stats:
            return {'no_data': True, 'period_hours': hours}
        
        # Calculate summary statistics
        gpu_stats = [s for s in recent_stats if s.gpu_accelerated]
        cpu_stats = [s for s in recent_stats if not s.gpu_accelerated]
        
        summary = {
            'period_hours': hours,
            'total_operations': len(recent_stats),
            'gpu_operations': len(gpu_stats),
            'cpu_operations': len(cpu_stats),
            'gpu_utilization_percent': (len(gpu_stats) / len(recent_stats)) * 100,
            
            'performance': {
                'average_throughput_mb_s': statistics.mean([s.throughput_mb_s for s in recent_stats]),
                'max_throughput_mb_s': max([s.throughput_mb_s for s in recent_stats]),
                'average_success_rate': statistics.mean([s.success_rate for s in recent_stats]),
                'total_files_processed': sum([s.files_processed for s in recent_stats]),
                'total_bytes_processed': sum([s.bytes_processed for s in recent_stats])
            }
        }
        
        if gpu_stats:
            summary['gpu_performance'] = {
                'average_throughput_mb_s': statistics.mean([s.throughput_mb_s for s in gpu_stats]),
                'max_throughput_mb_s': max([s.throughput_mb_s for s in gpu_stats]),
                'average_success_rate': statistics.mean([s.success_rate for s in gpu_stats])
            }
        
        if cpu_stats:
            summary['cpu_performance'] = {
                'average_throughput_mb_s': statistics.mean([s.throughput_mb_s for s in cpu_stats]),
                'max_throughput_mb_s': max([s.throughput_mb_s for s in cpu_stats]),
                'average_success_rate': statistics.mean([s.success_rate for s in cpu_stats])
            }
        
        return summary

    def register_alert_callback(self, callback: Callable[[Dict], None]):
        """Register callback for alerts"""
        self.alert_callbacks.append(callback)

    def export_data(self, file_path: str):
        """Export monitoring data to JSON file"""
        export_data = {
            'export_timestamp': datetime.now().isoformat(),
            'system_metrics': [asdict(m) for m in self.system_metrics_history],
            'gpu_metrics': [asdict(m) for m in self.gpu_metrics_history],
            'performance_stats': [asdict(s) for s in self.performance_stats],
            'benchmarks': self.benchmarks,
            'alerts': self.alerts
        }
        
        with open(file_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Monitoring data exported to {file_path}")

    def cleanup(self):
        """Clean up monitoring resources"""
        self.stop_monitoring()
        
        # Cleanup NVIDIA ML if initialized
        if self.nvidia_monitoring and HAS_NVML:
            try:
                nvml.nvmlShutdown()
            except:
                pass


# Global monitor instance
_gpu_monitor: Optional[GPUMonitor] = None


def get_gpu_monitor(config: Optional[Dict] = None) -> GPUMonitor:
    """Get or create the global GPU monitor instance"""
    global _gpu_monitor
    
    if _gpu_monitor is None:
        _gpu_monitor = GPUMonitor(config)
    
    return _gpu_monitor


# Module-level testing
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    print("GPU Monitor Test")
    print("=" * 30)
    
    # Test monitoring
    monitor = GPUMonitor()
    
    print(f"Monitoring available: {monitor.gpu_monitoring_available}")
    print(f"Monitoring active: {monitor.monitoring_active}")
    
    # Get current status
    status = monitor.get_current_status()
    print(f"Status: {status}")
    
    # Run quick benchmark
    if len(sys.argv) > 1 and sys.argv[1] == '--benchmark':
        print("\nRunning comprehensive benchmark...")
        benchmark = monitor.run_comprehensive_benchmark()
        print(f"Benchmark results: {benchmark}")
    
    # Wait for some monitoring data
    if monitor.monitoring_active:
        print("\nCollecting monitoring data for 10 seconds...")
        time.sleep(10)
        
        status = monitor.get_current_status()
        print(f"Metrics collected: {status['metrics_collected']}")
        print(f"GPU metrics collected: {status['gpu_metrics_collected']}")
    
    # Cleanup
    monitor.cleanup()
    print("\nMonitoring test completed successfully!")