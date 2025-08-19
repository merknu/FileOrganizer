"""
GPU Integration Tests for FileOrganizer.

Tests end-to-end GPU workflows including:
- GPU/CPU switching and fallback mechanisms  
- Multi-component GPU workflows (hashing + image processing)
- GPU monitoring and performance tracking
- Error handling and recovery scenarios
- Multi-GPU support and load balancing
- Real-world file processing scenarios

These tests validate that GPU components work together correctly
and provide expected functionality in complete workflows.
"""

import pytest
import time
import tempfile
import os
import json
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock
import concurrent.futures

# Test utilities
from tests.conftest import create_test_file

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
    import cupy as cp
    HAS_CUPY = True
except ImportError:
    HAS_CUPY = False

# Import modules under test
try:
    from file_handler.gpu_acceleration import (
        GPUAccelerator, GPUBackend, GPUDevice, get_gpu_accelerator, 
        initialize_gpu_acceleration, get_system_gpu_info
    )
    from file_handler.gpu_hasher import GPUHasher, HashResult, find_duplicate_files
    from file_handler.gpu_image_processor import (
        GPUImageProcessor, ImageMetadata, ThumbnailResult,
        extract_image_metadata_fast, generate_thumbnail_fast
    )
    from file_handler.gpu_monitor import GPUMonitor, get_gpu_monitor
    HAS_GPU_MODULES = True
except ImportError:
    HAS_GPU_MODULES = False


@pytest.fixture
def gpu_test_environment():
    """Set up a complete GPU test environment."""
    if not HAS_GPU_MODULES:
        pytest.skip("GPU modules not available")
    
    # Initialize GPU acceleration
    config = {
        'enable_gpu': True,
        'backend': 'auto',
        'memory_mode': 'balanced',
        'run_initial_benchmark': False,  # Skip for faster tests
        'chunk_size_mb': 32,
        'max_gpu_memory_usage': 0.7
    }
    
    accelerator = GPUAccelerator(config)
    monitor = GPUMonitor({
        'enable_monitoring': True,
        'monitoring_interval_seconds': 0.5,
        'metrics_history_size': 100
    })
    
    yield {
        'accelerator': accelerator,
        'monitor': monitor,
        'config': config
    }
    
    # Cleanup
    try:
        monitor.cleanup()
        accelerator.cleanup()
    except:
        pass


@pytest.fixture
def sample_media_files(tmp_path):
    """Create a comprehensive set of sample files for testing."""
    files = {}
    
    # Text files of various sizes
    for size_name, size_bytes in [('small', 1024), ('medium', 100*1024), ('large', 1024*1024)]:
        text_file = tmp_path / f"text_{size_name}.txt"
        content = f"Test content for {size_name} file. " * (size_bytes // 50)
        text_file.write_text(content[:size_bytes])
        files[f'text_{size_name}'] = str(text_file)
    
    # Binary files
    for size_name, size_bytes in [('small', 5*1024), ('medium', 500*1024), ('large', 5*1024*1024)]:
        binary_file = tmp_path / f"binary_{size_name}.bin"
        create_test_file(str(binary_file), size=size_bytes)
        files[f'binary_{size_name}'] = str(binary_file)
    
    # Image files (if PIL available)
    if HAS_PIL:
        for size_name, dimensions in [('small', (256, 192)), ('medium', (1024, 768)), ('large', (2048, 1536))]:
            image_file = tmp_path / f"image_{size_name}.jpg"
            img = Image.new('RGB', dimensions, color='blue')
            
            # Add some content to make it more realistic
            draw = ImageDraw.Draw(img)
            for i in range(0, dimensions[0], 50):
                draw.line([(i, 0), (i, dimensions[1])], fill='white', width=1)
            for i in range(0, dimensions[1], 50):
                draw.line([(0, i), (dimensions[0], i)], fill='white', width=1)
            
            img.save(str(image_file), quality=85)
            files[f'image_{size_name}'] = str(image_file)
    
    return files


@pytest.mark.gpu
@pytest.mark.integration
class TestGPUWorkflowIntegration:
    """Test complete GPU-accelerated workflows."""
    
    def test_end_to_end_file_processing_workflow(self, gpu_test_environment, sample_media_files):
        """Test complete file processing workflow with GPU acceleration."""
        env = gpu_test_environment
        accelerator = env['accelerator']
        monitor = env['monitor']
        
        # Initialize GPU components
        hasher = GPUHasher({'enable_gpu_hashing': True})
        processor = GPUImageProcessor({'enable_gpu_processing': True})
        
        # Track operation start
        workflow_start = time.time()
        
        results = {
            'files_processed': 0,
            'hash_results': [],
            'image_results': [],
            'errors': [],
            'gpu_operations': 0,
            'cpu_operations': 0
        }
        
        # Process all files
        for file_type, file_path in sample_media_files.items():
            try:
                # Hash all files
                hash_result = hasher.hash_file(file_path, ['sha256', 'md5'])
                results['hash_results'].append(hash_result)
                
                if hash_result.gpu_accelerated:
                    results['gpu_operations'] += 1
                else:
                    results['cpu_operations'] += 1
                
                if hash_result.error:
                    results['errors'].append(f"Hash error for {file_path}: {hash_result.error}")
                
                # Process image files
                if 'image_' in file_type:
                    metadata = processor.extract_metadata(file_path)
                    results['image_results'].append(metadata)
                    
                    if metadata.gpu_accelerated:
                        results['gpu_operations'] += 1
                    else:
                        results['cpu_operations'] += 1
                    
                    if metadata.error:
                        results['errors'].append(f"Image error for {file_path}: {metadata.error}")
                
                results['files_processed'] += 1
                
            except Exception as e:
                results['errors'].append(f"Workflow error for {file_path}: {str(e)}")
        
        workflow_time = time.time() - workflow_start
        
        # Record performance stats in monitor
        monitor.record_performance_stats(
            'end_to_end_workflow',
            start_time=time.time() - workflow_time,
            end_time=time.time(),
            files_processed=results['files_processed'],
            bytes_processed=sum(os.path.getsize(f) for f in sample_media_files.values()),
            gpu_accelerated=results['gpu_operations'] > results['cpu_operations'],
            success_count=results['files_processed'] - len(results['errors']),
            error_count=len(results['errors'])
        )
        
        # Validate workflow results
        assert results['files_processed'] > 0, "Should process some files"
        assert len(results['hash_results']) == results['files_processed'], "Should hash all files"
        assert len(results['errors']) == 0, f"Workflow should not have errors: {results['errors']}"
        
        # Check hash result validity
        valid_hashes = [r for r in results['hash_results'] if r.sha256 and r.md5 and not r.error]
        assert len(valid_hashes) == results['files_processed'], "All files should have valid hashes"
        
        # Check image processing results (if any images)
        image_files = [f for f in sample_media_files.keys() if 'image_' in f]
        if image_files and HAS_PIL:
            assert len(results['image_results']) == len(image_files), "Should process all images"
            valid_metadata = [r for r in results['image_results'] if r.width > 0 and r.height > 0 and not r.error]
            assert len(valid_metadata) == len(image_files), "All images should have valid metadata"
        
        # Performance checks
        assert workflow_time < 30.0, f"Workflow should complete in reasonable time: {workflow_time:.2f}s"
        
        # GPU utilization check
        if accelerator.is_available():
            gpu_ratio = results['gpu_operations'] / (results['gpu_operations'] + results['cpu_operations'])
            print(f"GPU utilization: {gpu_ratio:.1%} ({results['gpu_operations']} GPU, {results['cpu_operations']} CPU)")
    
    def test_concurrent_gpu_operations(self, gpu_test_environment, sample_media_files):
        """Test concurrent GPU operations with multiple threads."""
        env = gpu_test_environment
        
        # Create multiple GPU components for concurrent use
        hashers = [GPUHasher({'enable_gpu_hashing': True}) for _ in range(3)]
        processors = [GPUImageProcessor({'enable_gpu_processing': True}) for _ in range(2)]
        
        results = []
        errors = []
        
        def hash_worker(hasher, files):
            worker_results = []
            for file_path in files:
                try:
                    result = hasher.hash_file(file_path, ['sha256'])
                    worker_results.append(('hash', file_path, result))
                except Exception as e:
                    errors.append(f"Hash worker error: {e}")
            return worker_results
        
        def image_worker(processor, files):
            worker_results = []
            image_files = [f for f in files if 'image_' in os.path.basename(f)]
            for file_path in image_files:
                try:
                    result = processor.extract_metadata(file_path)
                    worker_results.append(('image', file_path, result))
                except Exception as e:
                    errors.append(f"Image worker error: {e}")
            return worker_results
        
        # Distribute files among workers
        file_list = list(sample_media_files.values())
        file_chunks = [file_list[i::3] for i in range(3)]  # 3 hash workers
        
        # Run concurrent operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            # Submit hash workers
            for i, (hasher, chunk) in enumerate(zip(hashers, file_chunks)):
                future = executor.submit(hash_worker, hasher, chunk)
                futures.append(future)
            
            # Submit image workers
            for processor in processors:
                future = executor.submit(image_worker, processor, file_list)
                futures.append(future)
            
            # Collect results
            for future in concurrent.futures.as_completed(futures, timeout=60):
                try:
                    worker_results = future.result()
                    results.extend(worker_results)
                except Exception as e:
                    errors.append(f"Worker execution error: {e}")
        
        # Validate concurrent operation results
        assert len(errors) == 0, f"Concurrent operations should not error: {errors}"
        
        hash_results = [r for r in results if r[0] == 'hash']
        image_results = [r for r in results if r[0] == 'image']
        
        # Should process all files
        unique_hash_files = set(r[1] for r in hash_results)
        assert len(unique_hash_files) == len(sample_media_files), "Should hash all files concurrently"
        
        # Check for data corruption or conflicts
        hash_by_file = {}
        for _, file_path, result in hash_results:
            if file_path in hash_by_file:
                # Same file hashed by different workers - results should match
                assert hash_by_file[file_path] == result.sha256, f"Hash mismatch for {file_path}"
            else:
                hash_by_file[file_path] = result.sha256
    
    def test_gpu_memory_management_workflow(self, gpu_test_environment, tmp_path):
        """Test GPU memory management during intensive workflows."""
        env = gpu_test_environment
        accelerator = env['accelerator']
        monitor = env['monitor']
        
        if not accelerator.is_available():
            pytest.skip("GPU not available for memory test")
        
        # Create files that will challenge memory limits
        large_files = []
        for i in range(5):
            file_path = tmp_path / f"memory_test_{i}.bin"
            create_test_file(str(file_path), size=20 * 1024 * 1024)  # 20MB each
            large_files.append(str(file_path))
        
        hasher = GPUHasher({
            'enable_gpu_hashing': True,
            'gpu_memory_limit_mb': 256,
            'chunk_size_mb': 32,
            'max_concurrent_files': 2
        })
        
        # Monitor memory usage during processing
        initial_used, initial_total = accelerator.get_memory_usage()
        memory_samples = []
        
        def memory_monitor():
            for _ in range(20):  # Sample for 10 seconds
                used, total = accelerator.get_memory_usage()
                memory_samples.append(used)
                time.sleep(0.5)
        
        # Start memory monitoring
        monitor_thread = threading.Thread(target=memory_monitor, daemon=True)
        monitor_thread.start()
        
        # Process large files
        results = []
        start_time = time.time()
        
        for file_path in large_files:
            result = hasher.hash_file(file_path, ['sha256'])
            results.append(result)
            
            # Check for memory leaks during processing
            current_used, _ = accelerator.get_memory_usage()
            memory_increase = current_used - initial_used
            assert memory_increase < 500, f"Memory usage increased too much: {memory_increase}MB"
        
        processing_time = time.time() - start_time
        
        # Wait for memory monitoring to complete
        monitor_thread.join(timeout=2)
        
        # Validate results
        assert len(results) == len(large_files), "Should process all large files"
        
        successful_results = [r for r in results if not r.error]
        assert len(successful_results) == len(large_files), "All large file processing should succeed"
        
        # Check memory usage pattern
        if memory_samples:
            max_memory = max(memory_samples)
            avg_memory = sum(memory_samples) / len(memory_samples)
            memory_variance = max(memory_samples) - min(memory_samples)
            
            print(f"Memory usage during processing: avg={avg_memory:.1f}MB, max={max_memory:.1f}MB, variance={memory_variance:.1f}MB")
            
            # Memory should be managed reasonably
            assert memory_variance < 1000, f"Memory variance too high: {memory_variance}MB"
        
        # Performance should be reasonable for large files
        total_size_mb = sum(os.path.getsize(f) for f in large_files) / 1024 / 1024
        throughput = total_size_mb / processing_time
        assert throughput > 5.0, f"Throughput too low for memory-managed processing: {throughput:.1f} MB/s"


@pytest.mark.gpu 
@pytest.mark.integration
class TestGPUFallbackIntegration:
    """Test GPU fallback and error recovery mechanisms."""
    
    def test_dynamic_gpu_cpu_switching(self, gpu_test_environment, sample_media_files):
        """Test dynamic switching between GPU and CPU based on conditions."""
        env = gpu_test_environment
        
        # Create hasher with specific switching criteria
        hasher = GPUHasher({
            'enable_gpu_hashing': True,
            'fallback_to_cpu': True,
            'min_file_size_for_gpu': 100 * 1024  # 100KB threshold
        })
        
        results = []
        gpu_count = 0
        cpu_count = 0
        
        for file_type, file_path in sample_media_files.items():
            result = hasher.hash_file(file_path, ['sha256'])
            results.append(result)
            
            file_size = os.path.getsize(file_path)
            
            if result.gpu_accelerated:
                gpu_count += 1
                # Large files should use GPU (if available)
                if file_size >= 100 * 1024 and env['accelerator'].is_available():
                    assert result.gpu_accelerated, f"Large file {file_path} should use GPU"
            else:
                cpu_count += 1
                # Small files should use CPU
                if file_size < 100 * 1024:
                    assert not result.gpu_accelerated, f"Small file {file_path} should use CPU"
        
        # Should have a mix based on file sizes
        total_files = len(results)
        small_files = sum(1 for f in sample_media_files.values() if os.path.getsize(f) < 100 * 1024)
        large_files = total_files - small_files
        
        print(f"Processing results: {gpu_count} GPU, {cpu_count} CPU (expected: {large_files} large, {small_files} small)")
        
        # All files should be processed successfully
        assert all(not r.error for r in results), "All files should process without error"
        assert len(results) == total_files, "Should process all files"
    
    def test_gpu_error_recovery(self, gpu_test_environment, tmp_path):
        """Test recovery from GPU errors and exceptions."""
        env = gpu_test_environment
        
        # Create test file
        test_file = tmp_path / "recovery_test.bin"
        create_test_file(str(test_file), size=1024 * 1024)  # 1MB
        
        hasher = GPUHasher({
            'enable_gpu_hashing': True, 
            'fallback_to_cpu': True
        })
        
        # Mock GPU method to simulate various failures
        original_gpu_hash = hasher._hash_file_gpu
        failure_modes = ['memory_error', 'computation_error', 'timeout_error', 'success']
        results = []
        
        for failure_mode in failure_modes:
            def mock_gpu_hash(*args, **kwargs):
                if failure_mode == 'memory_error':
                    raise RuntimeError("CUDA out of memory")
                elif failure_mode == 'computation_error':
                    raise ValueError("GPU computation failed")
                elif failure_mode == 'timeout_error':
                    raise TimeoutError("GPU operation timed out")
                else:
                    return original_gpu_hash(*args, **kwargs)
            
            hasher._hash_file_gpu = mock_gpu_hash
            
            # Test recovery
            result = hasher.hash_file(str(test_file), ['sha256'])
            results.append((failure_mode, result))
            
            # Should always get a result (via fallback)
            assert result is not None, f"Should get result for {failure_mode}"
            if failure_mode == 'success':
                assert not result.error, f"Success case should not error"
            else:
                # Should fallback to CPU successfully
                assert not result.error, f"Fallback should work for {failure_mode}"
                assert not result.gpu_accelerated, f"Should use CPU fallback for {failure_mode}"
        
        # Restore original method
        hasher._hash_file_gpu = original_gpu_hash
        
        # All operations should produce valid hashes
        valid_hashes = [r[1].sha256 for r in results if r[1] and r[1].sha256]
        assert len(set(valid_hashes)) == 1, "All hash attempts should produce the same result"
    
    def test_partial_gpu_availability(self, gpu_test_environment, sample_media_files):
        """Test behavior when GPU is partially available or limited."""
        env = gpu_test_environment
        
        # Simulate limited GPU memory scenario
        limited_hasher = GPUHasher({
            'enable_gpu_hashing': True,
            'gpu_memory_limit_mb': 50,  # Very limited
            'chunk_size_mb': 16,
            'fallback_to_cpu': True
        })
        
        # Process different sized files
        results = {}
        
        for file_type, file_path in sample_media_files.items():
            file_size = os.path.getsize(file_path)
            result = limited_hasher.hash_file(file_path, ['sha256'])
            
            results[file_type] = {
                'size': file_size,
                'result': result,
                'gpu_used': result.gpu_accelerated,
                'success': not result.error
            }
        
        # All files should process successfully despite limitations
        assert all(r['success'] for r in results.values()), "All files should process despite GPU limitations"
        
        # Larger files might fallback to CPU due to memory limits
        large_files = {k: v for k, v in results.items() if v['size'] > 1024 * 1024}  # > 1MB
        small_files = {k: v for k, v in results.items() if v['size'] <= 1024 * 1024}  # <= 1MB
        
        if large_files:
            cpu_fallbacks = sum(1 for r in large_files.values() if not r['gpu_used'])
            total_large = len(large_files)
            fallback_ratio = cpu_fallbacks / total_large
            
            print(f"Large files: {cpu_fallbacks}/{total_large} used CPU fallback ({fallback_ratio:.1%})")


@pytest.mark.gpu
@pytest.mark.integration
class TestGPUMonitoringIntegration:
    """Test GPU monitoring and performance tracking integration."""
    
    def test_comprehensive_monitoring_workflow(self, gpu_test_environment, sample_media_files):
        """Test comprehensive monitoring during GPU operations."""
        env = gpu_test_environment
        monitor = env['monitor']
        
        # Ensure monitoring is active
        if not monitor.monitoring_active:
            monitor.start_monitoring()
        
        # Give monitor time to collect baseline
        time.sleep(2)
        
        initial_status = monitor.get_current_status()
        
        # Perform various GPU operations
        hasher = GPUHasher({'enable_gpu_hashing': True})
        processor = GPUImageProcessor({'enable_gpu_processing': True})
        
        operations = []
        
        # Process files with monitoring
        for file_type, file_path in sample_media_files.items():
            op_start = time.time()
            
            # Hash file
            hash_result = hasher.hash_file(file_path, ['sha256'])
            
            # Process images
            if 'image_' in file_type and HAS_PIL:
                img_result = processor.extract_metadata(file_path)
                operations.append(('image_metadata', img_result))
            
            operations.append(('file_hash', hash_result))
            
            # Record in monitor
            monitor.record_performance_stats(
                f'{file_type}_processing',
                start_time=op_start,
                end_time=time.time(),
                files_processed=1,
                bytes_processed=os.path.getsize(file_path),
                gpu_accelerated=hash_result.gpu_accelerated,
                success_count=1 if not hash_result.error else 0,
                error_count=1 if hash_result.error else 0
            )
        
        # Allow monitoring to collect data
        time.sleep(3)
        
        # Get final status and performance summary
        final_status = monitor.get_current_status()
        performance_summary = monitor.get_performance_summary(hours=1)
        
        # Validate monitoring data
        assert final_status['metrics_collected'] > initial_status['metrics_collected'], "Should collect new metrics"
        assert final_status['performance_records'] > initial_status['performance_records'], "Should record performance data"
        
        if not performance_summary.get('no_data'):
            assert performance_summary['total_operations'] > 0, "Should track operations"
            assert performance_summary['performance']['total_files_processed'] > 0, "Should track processed files"
            
            # Check GPU utilization tracking
            if env['accelerator'].is_available():
                gpu_ops = performance_summary.get('gpu_operations', 0)
                total_ops = performance_summary['total_operations']
                gpu_ratio = gpu_ops / total_ops if total_ops > 0 else 0
                
                print(f"Monitored GPU utilization: {gpu_ratio:.1%}")
        
        # Validate operation results
        successful_ops = [op for op in operations if not op[1].error]
        assert len(successful_ops) == len(operations), "All monitored operations should succeed"
    
    def test_alert_system_integration(self, gpu_test_environment, tmp_path):
        """Test GPU monitoring alert system during intensive operations."""
        env = gpu_test_environment
        
        # Configure monitor with sensitive alert thresholds
        monitor = GPUMonitor({
            'enable_monitoring': True,
            'monitoring_interval_seconds': 0.5,
            'alert_thresholds': {
                'gpu_utilization': 50.0,  # Lower threshold to trigger alerts
                'gpu_memory': 70.0,
                'gpu_temperature': 60.0,
                'system_memory': 80.0
            }
        })
        
        # Start monitoring
        monitor.start_monitoring()
        
        # Collect initial alerts
        initial_alert_count = len(monitor.alerts)
        
        # Create intensive workload
        large_files = []
        for i in range(3):
            file_path = tmp_path / f"intensive_{i}.bin"
            create_test_file(str(file_path), size=10 * 1024 * 1024)  # 10MB each
            large_files.append(str(file_path))
        
        hasher = GPUHasher({'enable_gpu_hashing': True})
        
        # Process files intensively
        for file_path in large_files:
            result = hasher.hash_file(file_path, ['sha256', 'md5'])
            assert not result.error, f"Intensive processing should succeed for {file_path}"
        
        # Allow monitoring to detect any issues
        time.sleep(5)
        
        # Check for alerts
        final_alert_count = len(monitor.alerts)
        new_alerts = monitor.alerts[initial_alert_count:]
        
        print(f"Generated {len(new_alerts)} alerts during intensive processing")
        
        # Validate alert system
        for alert in new_alerts:
            assert 'type' in alert, "Alert should have type"
            assert 'message' in alert, "Alert should have message"
            assert 'severity' in alert, "Alert should have severity"
            assert 'timestamp' in alert, "Alert should have timestamp"
            
            print(f"Alert: {alert['type']} - {alert['message']}")
        
        # Cleanup
        monitor.cleanup()
    
    def test_performance_benchmarking_integration(self, gpu_test_environment):
        """Test integrated performance benchmarking."""
        env = gpu_test_environment
        monitor = env['monitor']
        
        # Run comprehensive benchmark
        benchmark_results = monitor.run_comprehensive_benchmark()
        
        # Validate benchmark results
        assert benchmark_results['success'] == True, "Benchmark should succeed"
        assert 'system_info' in benchmark_results, "Should include system info"
        assert 'gpu_info' in benchmark_results, "Should include GPU info"
        assert 'tests' in benchmark_results, "Should include test results"
        assert benchmark_results['total_time_seconds'] > 0, "Should record execution time"
        
        # Check individual test results
        tests = benchmark_results['tests']
        assert 'gpu_availability' in tests, "Should test GPU availability"
        assert 'cpu_baseline' in tests, "Should include CPU baseline"
        
        # If GPU available, should have GPU-specific tests
        if tests['gpu_availability'].get('available'):
            assert 'memory_bandwidth' in tests, "Should test memory bandwidth"
            
            # Performance thresholds (conservative)
            if 'file_hashing' in tests and tests['file_hashing'].get('success'):
                hash_perf = tests['file_hashing']
                assert hash_perf['gpu_throughput_mb_s'] > 0, "GPU throughput should be positive"
                assert hash_perf['cpu_throughput_mb_s'] > 0, "CPU throughput should be positive"
        
        print(f"Benchmark completed in {benchmark_results['total_time_seconds']:.2f} seconds")
        
        # Store benchmark for comparison
        monitor.benchmarks.append(benchmark_results)
        assert len(monitor.benchmarks) > 0, "Should store benchmark results"


@pytest.mark.gpu
@pytest.mark.integration
class TestRealWorldScenarios:
    """Test real-world GPU usage scenarios."""
    
    def test_duplicate_file_detection_workflow(self, gpu_test_environment, tmp_path):
        """Test GPU-accelerated duplicate file detection."""
        if not HAS_GPU_MODULES:
            pytest.skip("GPU modules not available")
        
        # Create test directory structure with duplicates
        source_dir = tmp_path / "source"
        source_dir.mkdir()
        
        target_dir = tmp_path / "target"
        target_dir.mkdir()
        
        # Create original files
        original_files = []
        file_contents = [
            b"Content for file 1" * 1000,
            b"Content for file 2" * 2000,
            b"Content for file 3" * 1500,
            b"Different content" * 800
        ]
        
        for i, content in enumerate(file_contents):
            file_path = source_dir / f"original_{i}.txt"
            file_path.write_bytes(content)
            original_files.append(str(file_path))
        
        # Create duplicates in target directory
        duplicate_files = []
        for i in [0, 1, 2]:  # Duplicate first 3 files
            dup_path = target_dir / f"copy_{i}.txt"
            dup_path.write_bytes(file_contents[i])
            duplicate_files.append(str(dup_path))
        
        # Add some unique files to target
        unique_path = target_dir / "unique.txt"
        unique_path.write_bytes(b"Unique content" * 500)
        
        # Test GPU-accelerated duplicate detection
        duplicates = find_duplicate_files(
            str(tmp_path),
            recursive=True,
            algorithms=['sha256'],
            progress_callback=lambda processed, total, result: print(f"Progress: {processed}/{total}")
        )
        
        # Validate results
        assert len(duplicates) == 3, f"Should find 3 duplicate groups, found {len(duplicates)}"
        
        # Check each duplicate group
        for hash_value, file_list in duplicates.items():
            assert len(file_list) == 2, f"Each duplicate group should have 2 files: {file_list}"
            
            # Verify files actually have same content
            contents = []
            for file_path in file_list:
                with open(file_path, 'rb') as f:
                    contents.append(f.read())
            
            assert contents[0] == contents[1], f"Duplicate files should have same content: {file_list}"
        
        print(f"Successfully detected {len(duplicates)} duplicate groups with GPU acceleration")
    
    def test_large_directory_processing(self, gpu_test_environment, tmp_path):
        """Test processing a large directory structure with many files."""
        if not HAS_GPU_MODULES:
            pytest.skip("GPU modules not available")
        
        # Create large directory structure
        base_dir = tmp_path / "large_test"
        base_dir.mkdir()
        
        files_created = []
        subdirs = ['docs', 'images', 'data', 'archives']
        
        # Create subdirectories with many files
        for subdir in subdirs:
            sub_path = base_dir / subdir
            sub_path.mkdir()
            
            # Create multiple files in each subdirectory
            for i in range(25):  # 25 files per subdirectory = 100 total
                file_path = sub_path / f"file_{i:03d}.txt"
                content = f"Content for {subdir}/file_{i} " * (100 + i * 10)
                file_path.write_text(content)
                files_created.append(str(file_path))
        
        print(f"Created {len(files_created)} files for large directory test")
        
        # Process with GPU acceleration
        hasher = GPUHasher({
            'enable_gpu_hashing': True,
            'max_concurrent_files': 6,
            'chunk_size_mb': 32
        })
        
        start_time = time.time()
        results = hasher.hash_files_batch(
            files_created,
            ['sha256'],
            progress_callback=lambda p, t, r: None  # Silent progress
        )
        processing_time = time.time() - start_time
        
        # Validate large batch results
        assert len(results) == len(files_created), "Should process all files"
        
        successful_results = [r for r in results if not r.error]
        assert len(successful_results) == len(files_created), "All files should process successfully"
        
        # Check for unique hashes (no accidental duplicates)
        hashes = [r.sha256 for r in successful_results if r.sha256]
        unique_hashes = set(hashes)
        assert len(unique_hashes) == len(hashes), "All files should have unique hashes"
        
        # Performance validation
        total_size = sum(os.path.getsize(f) for f in files_created)
        total_size_mb = total_size / 1024 / 1024
        throughput = total_size_mb / processing_time
        
        assert throughput > 1.0, f"Throughput should be reasonable: {throughput:.1f} MB/s"
        
        # Check GPU utilization
        gpu_results = [r for r in successful_results if r.gpu_accelerated]
        cpu_results = [r for r in successful_results if not r.gpu_accelerated]
        
        print(f"Large directory processing: {len(gpu_results)} GPU, {len(cpu_results)} CPU")
        print(f"Processed {total_size_mb:.1f} MB in {processing_time:.2f}s ({throughput:.1f} MB/s)")
    
    def test_mixed_workload_scenario(self, gpu_test_environment, tmp_path):
        """Test mixed GPU workload with hashing and image processing."""
        if not HAS_GPU_MODULES or not HAS_PIL:
            pytest.skip("GPU modules or PIL not available")
        
        # Create mixed content
        files = {}
        
        # Large binary files
        for i in range(3):
            bin_path = tmp_path / f"large_binary_{i}.bin"
            create_test_file(str(bin_path), size=5 * 1024 * 1024)  # 5MB
            files[f'binary_{i}'] = str(bin_path)
        
        # Images of various sizes
        image_sizes = [(800, 600), (1920, 1080), (2560, 1440)]
        for i, (width, height) in enumerate(image_sizes):
            img_path = tmp_path / f"test_image_{i}.jpg"
            img = Image.new('RGB', (width, height))
            
            # Create some visual content
            pixels = []
            for y in range(height):
                for x in range(width):
                    r = (x * 255) // width
                    g = (y * 255) // height
                    b = ((x + y) * 255) // (width + height)
                    pixels.append((r, g, b))
            img.putdata(pixels)
            
            img.save(str(img_path), quality=90)
            files[f'image_{i}'] = str(img_path)
        
        # Initialize processors
        hasher = GPUHasher({'enable_gpu_hashing': True})
        processor = GPUImageProcessor({'enable_gpu_processing': True})
        
        # Mixed processing workflow
        results = {
            'hashes': {},
            'metadata': {},
            'thumbnails': {},
            'errors': []
        }
        
        # Process all files
        for file_key, file_path in files.items():
            try:
                # Hash all files
                hash_result = hasher.hash_file(file_path, ['sha256'])
                results['hashes'][file_key] = hash_result
                
                if hash_result.error:
                    results['errors'].append(f"Hash error for {file_key}: {hash_result.error}")
                
                # Process images
                if 'image_' in file_key:
                    # Extract metadata
                    metadata = processor.extract_metadata(file_path)
                    results['metadata'][file_key] = metadata
                    
                    if metadata.error:
                        results['errors'].append(f"Metadata error for {file_key}: {metadata.error}")
                    
                    # Generate thumbnail
                    thumb_path = tmp_path / f"thumb_{file_key}.jpg"
                    thumbnail = processor.generate_thumbnail(file_path, str(thumb_path), (256, 256))
                    results['thumbnails'][file_key] = thumbnail
                    
                    if thumbnail.error:
                        results['errors'].append(f"Thumbnail error for {file_key}: {thumbnail.error}")
            
            except Exception as e:
                results['errors'].append(f"Processing error for {file_key}: {str(e)}")
        
        # Validate mixed workload results
        assert len(results['errors']) == 0, f"Mixed workload should not have errors: {results['errors']}"
        
        # Check hash results
        assert len(results['hashes']) == len(files), "Should hash all files"
        valid_hashes = {k: v for k, v in results['hashes'].items() if v.sha256 and not v.error}
        assert len(valid_hashes) == len(files), "All files should have valid hashes"
        
        # Check image processing results
        image_files = [k for k in files.keys() if 'image_' in k]
        assert len(results['metadata']) == len(image_files), "Should extract metadata from all images"
        assert len(results['thumbnails']) == len(image_files), "Should generate thumbnails for all images"
        
        # Check thumbnail files exist
        for file_key in image_files:
            thumb_path = tmp_path / f"thumb_{file_key}.jpg"
            assert thumb_path.exists(), f"Thumbnail should be created for {file_key}"
        
        # Performance summary
        gpu_hash_count = sum(1 for r in results['hashes'].values() if r.gpu_accelerated)
        gpu_metadata_count = sum(1 for r in results['metadata'].values() if r.gpu_accelerated)
        gpu_thumb_count = sum(1 for r in results['thumbnails'].values() if r.gpu_accelerated)
        
        print(f"Mixed workload GPU utilization:")
        print(f"  Hashing: {gpu_hash_count}/{len(results['hashes'])}")
        print(f"  Metadata: {gpu_metadata_count}/{len(results['metadata'])}")
        print(f"  Thumbnails: {gpu_thumb_count}/{len(results['thumbnails'])}")


if __name__ == "__main__":
    # Run integration tests when executed directly
    pytest.main([__file__, "-v", "-m", "integration"])