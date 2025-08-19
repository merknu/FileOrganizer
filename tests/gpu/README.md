# GPU Testing Framework for FileOrganizer

This directory contains comprehensive GPU performance tests, integration tests, and benchmarks for FileOrganizer's GPU-accelerated features.

## Test Structure

### Test Files

- **`test_gpu_performance.py`** - Performance benchmarks comparing GPU vs CPU operations
- **`test_gpu_integration.py`** - End-to-end integration tests for GPU workflows  
- **`test_gpu_mocks.py`** - Mock GPU tests for CI environments without hardware
- **`gpu_fixtures.py`** - Shared fixtures and utilities for GPU testing

### Test Categories

Tests are organized using pytest markers:

- `@pytest.mark.gpu` - Tests requiring GPU libraries or hardware
- `@pytest.mark.performance` - Performance measurement tests
- `@pytest.mark.integration` - End-to-end workflow tests
- `@pytest.mark.mock` - Tests using mocked GPU implementations
- `@pytest.mark.cuda` - CUDA/NVIDIA specific tests
- `@pytest.mark.opencl` - OpenCL specific tests
- `@pytest.mark.gpu_required` - Tests requiring actual GPU hardware
- `@pytest.mark.gpu_optional` - Tests that adapt to GPU availability

## Running Tests

### Quick Start

```bash
# Run all GPU tests (auto-detects hardware)
python run_gpu_tests.py --all

# Run only mock tests (works without GPU)
python run_gpu_tests.py --mock-only

# Run performance benchmarks
python run_gpu_tests.py --performance --iterations 5
```

### Detailed Options

```bash
# Hardware-specific tests
python run_gpu_tests.py --hardware         # GPU detection and compatibility
python run_gpu_tests.py --integration      # End-to-end workflows
python run_gpu_tests.py --stress          # Memory and stability tests

# Configuration options
python run_gpu_tests.py --quick           # Reduced test data for faster runs
python run_gpu_tests.py --backend cuda    # Force specific GPU backend
python run_gpu_tests.py --timeout 300     # Set test timeout

# Output and reporting
python run_gpu_tests.py --all --report results.html
python run_gpu_tests.py --benchmark --benchmark-output perf.json
```

### Using pytest directly

```bash
# Run specific test categories
pytest tests/gpu/ -m "gpu and performance" -v
pytest tests/gpu/ -m "mock" -v                    # CI-friendly
pytest tests/gpu/ -m "integration" -v             # End-to-end tests

# Run with specific backends
pytest tests/gpu/ -k "cuda" -v                    # CUDA tests only
pytest tests/gpu/ -k "opencl" -v                  # OpenCL tests only

# Performance tests with custom parameters
pytest tests/gpu/test_gpu_performance.py::TestGPUHashingPerformance -v
```

## Test Environment Requirements

### Minimum Requirements (Mock Tests)

- Python 3.8+
- pytest 7.0+
- FileOrganizer GPU modules installed
- No GPU hardware required

### Hardware Testing Requirements

- CUDA-capable GPU (NVIDIA) or OpenCL-capable GPU (AMD/Intel/NVIDIA)
- GPU drivers installed
- At least 2GB GPU memory recommended
- One or more of:
  - CuPy (for CUDA)
  - PyCUDA (alternative CUDA interface)  
  - PyOpenCL (for OpenCL)

### Optional Dependencies

- NumPy (for array operations)
- PIL/Pillow (for image processing tests)
- psutil (for system monitoring)
- GPUtil (for NVIDIA GPU monitoring)
- py3nvml (for advanced NVIDIA monitoring)

## Test Configuration

### Environment Variables

```bash
# GPU testing configuration
export GPU_TEST_BACKEND=cuda        # Force specific backend
export GPU_TEST_MEMORY_LIMIT=1024   # Limit GPU memory usage (MB)
export GPU_TEST_TIMEOUT=60          # Test timeout in seconds
export GPU_TEST_SKIP_SLOW=1         # Skip slow/long-running tests
```

### pytest Configuration

The `pytest.ini` file includes GPU-specific markers and warning filters:

```ini
markers =
    gpu: marks tests that require GPU hardware or GPU libraries
    performance: marks tests that measure performance metrics
    mock: marks tests that use mocked implementations
    cuda: marks tests specific to CUDA/NVIDIA GPUs
    opencl: marks tests specific to OpenCL GPUs
    gpu_required: marks tests that require actual GPU hardware
    gpu_optional: marks tests that can run with or without GPU
```

## Test Data and Fixtures

### Available Fixtures

- `gpu_test_environment` - Complete GPU test setup with cleanup
- `gpu_test_data` - Generator for test files and images
- `performance_timer` - High-precision timing utilities
- `gpu_memory_monitor` - GPU memory usage tracking
- `mock_gpu_device` - Mock GPU for testing without hardware

### Test Data Generation

The framework automatically generates test data of various sizes:

- **Binary files**: 1KB to 100MB for hashing benchmarks
- **Images**: 256x192 to 4096x3072 for processing tests  
- **Directory structures**: Nested files for workflow tests
- **Duplicate files**: For duplicate detection testing

## Performance Benchmarks

### Benchmark Categories

1. **File Hashing Performance**
   - SHA256 and MD5 computation
   - Various file sizes (1KB to 100MB)
   - Batch processing efficiency
   - Memory-constrained scenarios

2. **Image Processing Performance**
   - Metadata extraction from images
   - Thumbnail generation
   - Batch image processing
   - GPU-accelerated filters and transformations

3. **Memory Management**
   - GPU memory allocation and cleanup
   - Memory leak detection
   - Large file processing under memory constraints
   - Concurrent operation memory usage

4. **Real-World Scenarios**
   - Large directory processing
   - Duplicate file detection
   - Mixed workloads (hashing + image processing)
   - Long-running operations

### Expected Performance Improvements

Based on hardware capabilities, GPU acceleration typically provides:

- **File Hashing**: 1.5-3x speedup for large files (>10MB)
- **Image Processing**: 2-5x speedup for metadata extraction
- **Batch Operations**: 3-10x speedup with proper parallelization
- **Memory Bandwidth**: 5-20x improvement for large datasets

### Performance Regression Detection

The test suite includes baseline performance tracking:

```bash
# Establish performance baseline
python run_gpu_tests.py --benchmark --benchmark-output baseline.json

# Compare against baseline (detect regressions)
python benchmarks/gpu_benchmark.py --compare baseline.json --output current.json
```

## Integration Testing

### Workflow Coverage

Integration tests validate complete GPU-accelerated workflows:

1. **End-to-End File Processing**
   - Mixed file types (binary, images, documents)
   - GPU/CPU switching based on file characteristics
   - Error handling and recovery
   - Performance monitoring integration

2. **Concurrent Operations**
   - Multiple GPU components working simultaneously
   - Thread safety validation
   - Resource contention handling
   - Load balancing between GPU and CPU

3. **Fallback Mechanisms**
   - Automatic CPU fallback when GPU fails
   - Graceful degradation under resource constraints
   - Error recovery and retry logic
   - Cross-platform compatibility

4. **Memory Management Integration**
   - Memory-constrained processing
   - Large file handling
   - Batch processing optimization
   - Memory leak prevention

## Mock Testing for CI/CD

### CI-Friendly Tests

Mock tests run without GPU hardware, making them perfect for CI/CD:

```bash
# Run in CI environment
pytest tests/gpu/test_gpu_mocks.py -v
python run_gpu_tests.py --mock-only
```

### What Mock Tests Cover

- API contracts and interfaces
- Configuration validation
- Error handling logic
- Cross-platform compatibility
- Fallback mechanism logic
- Performance measurement framework

### Mock Implementation Features

- Realistic GPU device simulation
- Configurable memory and performance characteristics
- Error injection for testing failure scenarios
- Cross-platform behavior simulation

## Troubleshooting

### Common Issues

1. **GPU Not Detected**
   ```bash
   # Check GPU libraries
   python -c "import cupy; print('CUDA available')"
   python -c "import pyopencl; print('OpenCL available')"
   
   # Check hardware
   nvidia-smi  # For NVIDIA GPUs
   clinfo      # For OpenCL devices
   ```

2. **Memory Errors**
   ```bash
   # Reduce memory usage
   export GPU_TEST_MEMORY_LIMIT=512
   pytest tests/gpu/ -k "not memory_stress"
   ```

3. **Timeout Issues**
   ```bash
   # Increase timeout or run quick tests
   python run_gpu_tests.py --quick --timeout 120
   ```

4. **Import Errors**
   ```bash
   # Install GPU dependencies
   pip install -r requirements-gpu.txt
   
   # Use mock tests if GPU libraries unavailable
   python run_gpu_tests.py --mock-only
   ```

### Debug Mode

Enable verbose logging for troubleshooting:

```bash
export GPU_TEST_DEBUG=1
python run_gpu_tests.py --verbose --all
```

### Platform-Specific Notes

**Windows:**
- Ensure CUDA toolkit is in PATH
- May require Visual Studio redistributables
- Use PowerShell for environment variables

**Linux:**
- Install appropriate GPU drivers (nvidia, amdgpu, intel)
- May require `opencl-headers` package
- Check `/dev/nvidia*` permissions

**macOS:**
- OpenCL support built-in (Metal backend)
- CUDA deprecated in recent versions
- Focus on OpenCL or CPU fallback tests

## Contributing

### Adding New Tests

1. **Performance Tests**: Add to `test_gpu_performance.py`
   ```python
   @pytest.mark.gpu
   @pytest.mark.performance  
   def test_new_performance_scenario(self, performance_benchmark):
       # Your performance test here
   ```

2. **Integration Tests**: Add to `test_gpu_integration.py`
   ```python
   @pytest.mark.gpu
   @pytest.mark.integration
   def test_new_workflow(self, gpu_test_environment):
       # Your integration test here
   ```

3. **Mock Tests**: Add to `test_gpu_mocks.py`
   ```python
   @pytest.mark.mock
   @pytest.mark.gpu
   def test_new_mock_scenario(self, mock_gpu_environment):
       # Your mock test here
   ```

### Test Guidelines

- Use appropriate pytest markers
- Include both positive and negative test cases
- Test error conditions and edge cases
- Provide meaningful assertions with clear failure messages
- Document expected performance characteristics
- Clean up resources in test teardown

### Performance Test Guidelines

- Run multiple iterations for statistical significance
- Compare GPU vs CPU performance where applicable
- Test various data sizes and scenarios
- Include memory usage validation
- Set reasonable performance thresholds
- Account for hardware variations in assertions

## Continuous Integration

### GitHub Actions Integration

```yaml
name: GPU Tests
on: [push, pull_request]

jobs:
  mock-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run mock GPU tests
        run: python run_gpu_tests.py --mock-only --report mock_results.html
      - name: Upload test results
        uses: actions/upload-artifact@v3
        with:
          name: mock-test-results
          path: mock_results.html

  hardware-tests:
    runs-on: [self-hosted, gpu]  # Requires GPU runner
    steps:
      - uses: actions/checkout@v3
      - name: Run GPU hardware tests
        run: python run_gpu_tests.py --all --report gpu_results.html
```

### Test Result Reporting

Tests generate JUnit XML files for CI integration:

- `tests/gpu_hardware_results.xml`
- `tests/gpu_performance_results.xml`  
- `tests/gpu_integration_results.xml`
- `tests/gpu_mock_results.xml`

HTML reports provide detailed analysis:
- Environment detection results
- Performance comparisons and trends
- Memory usage analysis
- Error details and stack traces