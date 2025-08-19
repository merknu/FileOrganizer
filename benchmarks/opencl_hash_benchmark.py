#!/usr/bin/env python3
"""
OpenCL Hash Performance Benchmark
Compares CPU vs GPU hashing performance for various file sizes.
"""

import os
import sys
import time
import hashlib
import tempfile
import statistics
from pathlib import Path
from typing import List, Dict, Any
import argparse

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from file_handler.gpu_hasher import GPUHasher
    import numpy as np
    HAS_DEPENDENCIES = True
except ImportError as e:
    print(f"Warning: Missing dependencies: {e}")
    HAS_DEPENDENCIES = False

try:
    import pyopencl as cl
    HAS_OPENCL = True
except ImportError:
    HAS_OPENCL = False


class HashBenchmark:
    """Benchmark hashing performance with various configurations"""
    
    def __init__(self):
        self.results = {}
        self.gpu_hasher = GPUHasher() if HAS_DEPENDENCIES else None
    
    def create_test_files(self, sizes: List[int]) -> Dict[int, str]:
        """Create test files of various sizes"""
        files = {}
        temp_dir = tempfile.mkdtemp(prefix="hash_benchmark_")
        
        print(f"Creating test files in {temp_dir}")
        
        for size in sizes:
            filename = os.path.join(temp_dir, f"test_{size}b.bin")
            with open(filename, 'wb') as f:
                # Create deterministic but pseudo-random data
                np.random.seed(42)  # Consistent results
                data = np.random.bytes(size)
                f.write(data)
            files[size] = filename
            print(f"  Created {size:,} byte file")
        
        return files
    
    def benchmark_cpu_hashing(self, files: Dict[int, str], algorithms: List[str], 
                            runs: int = 3) -> Dict[str, Any]:
        """Benchmark CPU-only hashing"""
        results = {}
        
        print("Benchmarking CPU hashing...")
        
        for size, filename in files.items():
            results[size] = {}
            
            for algorithm in algorithms:
                times = []
                
                for run in range(runs):
                    start_time = time.perf_counter()
                    
                    # CPU hashing
                    with open(filename, 'rb') as f:
                        if algorithm == 'sha256':
                            hasher = hashlib.sha256()
                        elif algorithm == 'md5':
                            hasher = hashlib.md5()
                        
                        while chunk := f.read(8192):
                            hasher.update(chunk)
                        
                        hash_result = hasher.hexdigest()
                    
                    end_time = time.perf_counter()
                    times.append(end_time - start_time)
                
                results[size][algorithm] = {
                    'times': times,
                    'avg_time': statistics.mean(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
                    'throughput_mbps': size / statistics.mean(times) / (1024 * 1024),
                    'hash': hash_result
                }
                
                print(f"  {size:,} bytes, {algorithm}: {statistics.mean(times):.4f}s "
                      f"({size / statistics.mean(times) / (1024 * 1024):.1f} MB/s)")
        
        return results
    
    def benchmark_gpu_hashing(self, files: Dict[int, str], algorithms: List[str], 
                            runs: int = 3) -> Dict[str, Any]:
        """Benchmark GPU-accelerated hashing"""
        if not HAS_DEPENDENCIES or not self.gpu_hasher:
            print("GPU hashing not available")
            return {}
        
        results = {}
        
        print("Benchmarking GPU hashing...")
        
        for size, filename in files.items():
            results[size] = {}
            
            for algorithm in algorithms:
                times = []
                gpu_accelerated_count = 0
                
                for run in range(runs):
                    start_time = time.perf_counter()
                    
                    # GPU hashing
                    hash_result = self.gpu_hasher.hash_file(filename, [algorithm])
                    
                    end_time = time.perf_counter()
                    times.append(end_time - start_time)
                    
                    if hash_result.gpu_accelerated:
                        gpu_accelerated_count += 1
                
                results[size][algorithm] = {
                    'times': times,
                    'avg_time': statistics.mean(times),
                    'min_time': min(times),
                    'max_time': max(times),
                    'std_dev': statistics.stdev(times) if len(times) > 1 else 0,
                    'throughput_mbps': size / statistics.mean(times) / (1024 * 1024),
                    'hash': getattr(hash_result, algorithm),
                    'gpu_accelerated': gpu_accelerated_count / runs,
                    'avg_gpu_acceleration': hash_result.gpu_accelerated
                }
                
                gpu_status = "GPU" if hash_result.gpu_accelerated else "CPU fallback"
                print(f"  {size:,} bytes, {algorithm} ({gpu_status}): {statistics.mean(times):.4f}s "
                      f"({size / statistics.mean(times) / (1024 * 1024):.1f} MB/s)")
        
        return results
    
    def compare_results(self, cpu_results: Dict, gpu_results: Dict) -> Dict[str, Any]:
        """Compare CPU vs GPU results and calculate speedup"""
        comparison = {}
        
        print("\n" + "="*80)
        print("PERFORMANCE COMPARISON")
        print("="*80)
        
        for size in cpu_results.keys():
            if size not in gpu_results:
                continue
            
            comparison[size] = {}
            
            print(f"\nFile Size: {size:,} bytes ({size / (1024*1024):.1f} MB)")
            print("-" * 60)
            
            for algorithm in cpu_results[size].keys():
                if algorithm not in gpu_results[size]:
                    continue
                
                cpu_time = cpu_results[size][algorithm]['avg_time']
                gpu_time = gpu_results[size][algorithm]['avg_time']
                cpu_throughput = cpu_results[size][algorithm]['throughput_mbps']
                gpu_throughput = gpu_results[size][algorithm]['throughput_mbps']
                
                speedup = cpu_time / gpu_time if gpu_time > 0 else 0
                throughput_improvement = gpu_throughput / cpu_throughput if cpu_throughput > 0 else 0
                
                comparison[size][algorithm] = {
                    'cpu_time': cpu_time,
                    'gpu_time': gpu_time,
                    'speedup': speedup,
                    'cpu_throughput': cpu_throughput,
                    'gpu_throughput': gpu_throughput,
                    'throughput_improvement': throughput_improvement,
                    'gpu_accelerated': gpu_results[size][algorithm].get('gpu_accelerated', 0)
                }
                
                print(f"{algorithm.upper():>8}: CPU {cpu_time:.4f}s ({cpu_throughput:.1f} MB/s) | "
                      f"GPU {gpu_time:.4f}s ({gpu_throughput:.1f} MB/s) | "
                      f"Speedup: {speedup:.2f}x")
        
        return comparison
    
    def generate_report(self, comparison: Dict[str, Any]) -> str:
        """Generate a comprehensive benchmark report"""
        report = []
        report.append("OpenCL Hash Performance Benchmark Report")
        report.append("=" * 50)
        report.append("")
        
        # System information
        report.append("System Information:")
        report.append(f"  OpenCL Available: {HAS_OPENCL}")
        
        if HAS_OPENCL:
            try:
                platforms = cl.get_platforms()
                report.append(f"  OpenCL Platforms: {len(platforms)}")
                for i, platform in enumerate(platforms):
                    report.append(f"    {i}: {platform.name}")
                    devices = platform.get_devices()
                    for j, device in enumerate(devices):
                        report.append(f"      Device {j}: {device.name}")
            except Exception as e:
                report.append(f"  OpenCL Info Error: {e}")
        
        report.append("")
        
        # Performance summary
        report.append("Performance Summary:")
        report.append("-" * 30)
        
        total_speedup_sha256 = []
        total_speedup_md5 = []
        
        for size, algorithms in comparison.items():
            size_mb = size / (1024 * 1024)
            report.append(f"\nFile Size: {size:,} bytes ({size_mb:.1f} MB)")
            
            for algorithm, metrics in algorithms.items():
                speedup = metrics['speedup']
                gpu_accel = metrics['gpu_accelerated']
                
                if algorithm == 'sha256':
                    total_speedup_sha256.append(speedup)
                elif algorithm == 'md5':
                    total_speedup_md5.append(speedup)
                
                accel_status = f"({gpu_accel*100:.0f}% GPU)" if gpu_accel > 0 else "(CPU fallback)"
                report.append(f"  {algorithm.upper():>8}: {speedup:.2f}x speedup {accel_status}")
                report.append(f"           CPU: {metrics['cpu_time']:.4f}s ({metrics['cpu_throughput']:.1f} MB/s)")
                report.append(f"           GPU: {metrics['gpu_time']:.4f}s ({metrics['gpu_throughput']:.1f} MB/s)")
        
        # Overall statistics
        report.append("")
        report.append("Overall Performance:")
        report.append("-" * 25)
        
        if total_speedup_sha256:
            avg_sha256_speedup = statistics.mean(total_speedup_sha256)
            max_sha256_speedup = max(total_speedup_sha256)
            report.append(f"SHA256 Average Speedup: {avg_sha256_speedup:.2f}x")
            report.append(f"SHA256 Maximum Speedup: {max_sha256_speedup:.2f}x")
        
        if total_speedup_md5:
            avg_md5_speedup = statistics.mean(total_speedup_md5)
            max_md5_speedup = max(total_speedup_md5)
            report.append(f"MD5 Average Speedup: {avg_md5_speedup:.2f}x")
            report.append(f"MD5 Maximum Speedup: {max_md5_speedup:.2f}x")
        
        # Recommendations
        report.append("")
        report.append("Recommendations:")
        report.append("-" * 20)
        
        if HAS_OPENCL and any(algorithms.get('sha256', {}).get('gpu_accelerated', 0) > 0 
                             for algorithms in comparison.values()):
            report.append("✅ OpenCL GPU acceleration is working and provides performance benefits")
            report.append("✅ GPU acceleration is most effective for larger files (>1MB)")
        else:
            report.append("⚠️  OpenCL GPU acceleration not active - using CPU fallback")
            report.append("💡 Install PyOpenCL and ensure GPU drivers are up to date")
            report.append("💡 Check that your GPU supports OpenCL compute")
        
        return "\n".join(report)
    
    def cleanup_files(self, files: Dict[int, str]):
        """Clean up test files"""
        temp_dir = None
        for filename in files.values():
            if temp_dir is None:
                temp_dir = os.path.dirname(filename)
            try:
                os.unlink(filename)
            except OSError:
                pass
        
        if temp_dir:
            try:
                os.rmdir(temp_dir)
                print(f"Cleaned up test files from {temp_dir}")
            except OSError:
                pass


def main():
    """Main benchmark execution"""
    parser = argparse.ArgumentParser(description="OpenCL Hash Performance Benchmark")
    parser.add_argument("--sizes", nargs="+", type=int, 
                       default=[1024, 10240, 102400, 1048576, 10485760],
                       help="File sizes to test in bytes")
    parser.add_argument("--algorithms", nargs="+", default=["sha256", "md5"],
                       help="Hash algorithms to test")
    parser.add_argument("--runs", type=int, default=3,
                       help="Number of benchmark runs per test")
    parser.add_argument("--output", type=str, help="Output report file")
    
    args = parser.parse_args()
    
    if not HAS_DEPENDENCIES:
        print("Error: Required dependencies not available")
        print("Install with: pip install numpy pyopencl")
        return 1
    
    benchmark = HashBenchmark()
    
    print("OpenCL Hash Performance Benchmark")
    print("=" * 50)
    print(f"Test sizes: {[f'{s:,}' for s in args.sizes]} bytes")
    print(f"Algorithms: {args.algorithms}")
    print(f"Runs per test: {args.runs}")
    print(f"OpenCL available: {HAS_OPENCL}")
    print()
    
    # Create test files
    files = benchmark.create_test_files(args.sizes)
    
    try:
        # Run benchmarks
        cpu_results = benchmark.benchmark_cpu_hashing(files, args.algorithms, args.runs)
        gpu_results = benchmark.benchmark_gpu_hashing(files, args.algorithms, args.runs)
        
        # Compare and report
        comparison = benchmark.compare_results(cpu_results, gpu_results)
        report = benchmark.generate_report(comparison)
        
        print()
        print(report)
        
        # Save report if requested
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
            print(f"\nReport saved to {args.output}")
    
    finally:
        # Cleanup
        benchmark.cleanup_files(files)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())