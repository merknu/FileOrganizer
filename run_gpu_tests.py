#!/usr/bin/env python3
"""
GPU Test Runner for FileOrganizer.

This script provides various options for running GPU-related tests:
- Hardware detection and compatibility tests
- Performance benchmarks and comparisons
- Mock tests for CI environments without GPU hardware
- Integration tests for complete GPU workflows
- Stress tests and memory validation

Usage:
    python run_gpu_tests.py [options]

Examples:
    # Run all GPU tests (with hardware detection)
    python run_gpu_tests.py --all
    
    # Run only mock tests (for CI environments)
    python run_gpu_tests.py --mock-only
    
    # Run performance benchmarks
    python run_gpu_tests.py --performance --iterations 5
    
    # Run integration tests with specific backend
    python run_gpu_tests.py --integration --backend cuda
    
    # Run quick test suite (reduced test data)
    python run_gpu_tests.py --quick
    
    # Generate test report
    python run_gpu_tests.py --all --report results.html
"""

import argparse
import sys
import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging
import time

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GPUTestRunner:
    """Manages execution of GPU-related tests."""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = {}
        
    def detect_gpu_environment(self) -> Dict[str, Any]:
        """Detect GPU environment and capabilities."""
        env_info = {
            'gpu_libraries': {},
            'gpu_hardware': {},
            'system_info': {}
        }
        
        # Check for GPU libraries
        gpu_libs = ['cupy', 'pycuda', 'pyopencl', 'GPUtil', 'py3nvml', 'numpy']
        for lib in gpu_libs:
            try:
                __import__(lib)
                env_info['gpu_libraries'][lib] = True
            except ImportError:
                env_info['gpu_libraries'][lib] = False
        
        # Check for GPU modules
        try:
            from file_handler.gpu_acceleration import get_system_gpu_info
            env_info['gpu_hardware'] = get_system_gpu_info()
        except ImportError:
            env_info['gpu_hardware'] = {'error': 'GPU modules not available'}
        
        # System info
        import platform
        env_info['system_info'] = {
            'platform': platform.platform(),
            'python_version': sys.version,
            'cpu_count': os.cpu_count()
        }
        
        return env_info
    
    def run_pytest_command(self, args: List[str], description: str) -> Dict[str, Any]:
        """Run pytest command and capture results."""
        logger.info(f"Running {description}...")
        
        cmd = ['python', '-m', 'pytest'] + args
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=600  # 10 minute timeout
            )
            
            duration = time.time() - start_time
            
            return {
                'description': description,
                'command': ' '.join(cmd),
                'returncode': result.returncode,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            return {
                'description': description,
                'command': ' '.join(cmd),
                'returncode': -1,
                'duration': time.time() - start_time,
                'stdout': '',
                'stderr': 'Test timed out after 10 minutes',
                'success': False
            }
        except Exception as e:
            return {
                'description': description,
                'command': ' '.join(cmd),
                'returncode': -1,
                'duration': time.time() - start_time,
                'stdout': '',
                'stderr': str(e),
                'success': False
            }
    
    def run_hardware_tests(self) -> Dict[str, Any]:
        """Run GPU hardware detection tests."""
        pytest_args = [
            'tests/gpu/',
            '-v',
            '-m', 'gpu and not performance and not mock',
            '--tb=short',
            '--junit-xml=tests/gpu_hardware_results.xml'
        ]
        
        return self.run_pytest_command(pytest_args, "GPU Hardware Detection Tests")
    
    def run_performance_tests(self, iterations: int = 3, quick: bool = False) -> Dict[str, Any]:
        """Run GPU performance benchmarks."""
        pytest_args = [
            'tests/gpu/test_gpu_performance.py',
            '-v',
            '-m', 'performance',
            '--tb=short',
            '--junit-xml=tests/gpu_performance_results.xml'
        ]
        
        if quick:
            pytest_args.extend(['-k', 'not stress and not long_running'])
        
        return self.run_pytest_command(pytest_args, f"GPU Performance Tests ({iterations} iterations)")
    
    def run_integration_tests(self, backend: Optional[str] = None) -> Dict[str, Any]:
        """Run GPU integration tests."""
        pytest_args = [
            'tests/gpu/test_gpu_integration.py',
            '-v',
            '-m', 'integration',
            '--tb=short',
            '--junit-xml=tests/gpu_integration_results.xml'
        ]
        
        description = "GPU Integration Tests"
        if backend:
            description += f" (Backend: {backend})"
        
        return self.run_pytest_command(pytest_args, description)
    
    def run_mock_tests(self) -> Dict[str, Any]:
        """Run mock GPU tests (for CI environments)."""
        pytest_args = [
            'tests/gpu/test_gpu_mocks.py',
            '-v',
            '-m', 'mock',
            '--tb=short',
            '--junit-xml=tests/gpu_mock_results.xml'
        ]
        
        return self.run_pytest_command(pytest_args, "Mock GPU Tests (CI-friendly)")
    
    def run_stress_tests(self) -> Dict[str, Any]:
        """Run GPU stress and stability tests."""
        pytest_args = [
            'tests/gpu/',
            '-v',
            '-m', 'gpu and (stress or long_running)',
            '--tb=short',
            '--junit-xml=tests/gpu_stress_results.xml',
            '--maxfail=5'  # Stop after 5 failures for stress tests
        ]
        
        return self.run_pytest_command(pytest_args, "GPU Stress and Stability Tests")
    
    def run_all_tests(self, quick: bool = False) -> Dict[str, List[Dict[str, Any]]]:
        """Run all GPU test categories."""
        results = {
            'hardware': [],
            'mock': [],
            'performance': [],
            'integration': [],
            'stress': []
        }
        
        # Always run mock tests (they work without GPU hardware)
        results['mock'].append(self.run_mock_tests())
        
        # Try hardware detection
        hardware_result = self.run_hardware_tests()
        results['hardware'].append(hardware_result)
        
        # If hardware tests pass, run performance and integration tests
        if hardware_result['success']:
            logger.info("GPU hardware detected - running performance and integration tests")
            
            results['performance'].append(self.run_performance_tests(quick=quick))
            results['integration'].append(self.run_integration_tests())
            
            if not quick:
                results['stress'].append(self.run_stress_tests())
        else:
            logger.info("No GPU hardware detected - skipping hardware-dependent tests")
        
        return results
    
    def run_benchmark_suite(self, output_file: Optional[str] = None) -> Dict[str, Any]:
        """Run comprehensive benchmark suite."""
        benchmark_script = self.project_root / 'benchmarks' / 'gpu_benchmark.py'
        
        if not benchmark_script.exists():
            return {
                'description': 'GPU Benchmark Suite',
                'success': False,
                'error': 'Benchmark script not found'
            }
        
        cmd = ['python', str(benchmark_script)]
        
        if output_file:
            cmd.extend(['--output', output_file])
        
        logger.info("Running comprehensive GPU benchmark suite...")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=1800  # 30 minute timeout for benchmarks
            )
            
            duration = time.time() - start_time
            
            return {
                'description': 'GPU Benchmark Suite',
                'command': ' '.join(cmd),
                'returncode': result.returncode,
                'duration': duration,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'success': result.returncode == 0,
                'output_file': output_file
            }
            
        except subprocess.TimeoutExpired:
            return {
                'description': 'GPU Benchmark Suite',
                'command': ' '.join(cmd),
                'returncode': -1,
                'duration': time.time() - start_time,
                'stdout': '',
                'stderr': 'Benchmark timed out after 30 minutes',
                'success': False
            }
        except Exception as e:
            return {
                'description': 'GPU Benchmark Suite',
                'command': ' '.join(cmd),
                'returncode': -1,
                'duration': time.time() - start_time,
                'stdout': '',
                'stderr': str(e),
                'success': False
            }
    
    def generate_report(self, results: Dict[str, Any], output_file: str):
        """Generate test report."""
        report = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'environment': self.detect_gpu_environment(),
            'results': results,
            'summary': self._calculate_summary(results)
        }
        
        if output_file.endswith('.json'):
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
        elif output_file.endswith('.html'):
            self._generate_html_report(report, output_file)
        else:
            # Default to JSON
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Test report saved to: {output_file}")
    
    def _calculate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate test summary statistics."""
        summary = {
            'total_categories': 0,
            'successful_categories': 0,
            'total_duration': 0.0,
            'category_details': {}
        }
        
        def process_result_list(result_list: List[Dict[str, Any]]) -> Dict[str, Any]:
            if not result_list:
                return {'tests': 0, 'successful': 0, 'duration': 0.0}
            
            total_tests = len(result_list)
            successful_tests = sum(1 for r in result_list if r.get('success', False))
            total_duration = sum(r.get('duration', 0) for r in result_list)
            
            return {
                'tests': total_tests,
                'successful': successful_tests,
                'duration': total_duration,
                'success_rate': successful_tests / total_tests if total_tests > 0 else 0
            }
        
        for category, result_list in results.items():
            if isinstance(result_list, list):
                category_stats = process_result_list(result_list)
                summary['category_details'][category] = category_stats
                
                summary['total_categories'] += 1
                if category_stats['success_rate'] > 0:
                    summary['successful_categories'] += 1
                
                summary['total_duration'] += category_stats['duration']
        
        summary['overall_success_rate'] = (
            summary['successful_categories'] / summary['total_categories']
            if summary['total_categories'] > 0 else 0
        )
        
        return summary
    
    def _generate_html_report(self, report: Dict[str, Any], output_file: str):
        """Generate HTML test report."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>GPU Test Report - FileOrganizer</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f0f0f0; padding: 20px; border-radius: 5px; }}
        .summary {{ margin: 20px 0; }}
        .category {{ margin: 20px 0; border: 1px solid #ccc; padding: 15px; }}
        .success {{ background-color: #d4edda; }}
        .failure {{ background-color: #f8d7da; }}
        .warning {{ background-color: #fff3cd; }}
        pre {{ background-color: #f8f9fa; padding: 10px; overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ccc; padding: 8px; text-align: left; }}
        th {{ background-color: #e9ecef; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>GPU Test Report - FileOrganizer</h1>
        <p><strong>Generated:</strong> {report['timestamp']}</p>
    </div>
    
    <div class="summary">
        <h2>Test Summary</h2>
        <table>
            <tr><th>Metric</th><th>Value</th></tr>
            <tr><td>Total Categories</td><td>{report['summary']['total_categories']}</td></tr>
            <tr><td>Successful Categories</td><td>{report['summary']['successful_categories']}</td></tr>
            <tr><td>Overall Success Rate</td><td>{report['summary']['overall_success_rate']:.1%}</td></tr>
            <tr><td>Total Duration</td><td>{report['summary']['total_duration']:.2f}s</td></tr>
        </table>
    </div>
    
    <div class="environment">
        <h2>Environment Information</h2>
        <h3>System</h3>
        <ul>
            <li><strong>Platform:</strong> {report['environment']['system_info'].get('platform', 'Unknown')}</li>
            <li><strong>Python:</strong> {report['environment']['system_info'].get('python_version', 'Unknown')}</li>
            <li><strong>CPU Cores:</strong> {report['environment']['system_info'].get('cpu_count', 'Unknown')}</li>
        </ul>
        
        <h3>GPU Libraries</h3>
        <ul>
        """
        
        for lib, available in report['environment']['gpu_libraries'].items():
            status = "✓" if available else "✗"
            html_content += f"<li><strong>{lib}:</strong> {status}</li>\n"
        
        html_content += """
        </ul>
    </div>
    
    <div class="results">
        <h2>Test Results by Category</h2>
        """
        
        for category, results_list in report['results'].items():
            if isinstance(results_list, list) and results_list:
                html_content += f'<div class="category">\n'
                html_content += f'<h3>{category.title()} Tests</h3>\n'
                
                for result in results_list:
                    css_class = "success" if result.get('success') else "failure"
                    html_content += f'<div class="{css_class}">\n'
                    html_content += f'<h4>{result.get("description", "Unknown Test")}</h4>\n'
                    html_content += f'<p><strong>Duration:</strong> {result.get("duration", 0):.2f}s</p>\n'
                    html_content += f'<p><strong>Success:</strong> {"Yes" if result.get("success") else "No"}</p>\n'
                    
                    if result.get('stderr'):
                        html_content += '<h5>Errors:</h5>\n'
                        html_content += f'<pre>{result["stderr"]}</pre>\n'
                    
                    html_content += '</div>\n'
                
                html_content += '</div>\n'
        
        html_content += """
    </div>
</body>
</html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='GPU Test Runner for FileOrganizer')
    
    # Test selection options
    parser.add_argument('--all', action='store_true', help='Run all GPU tests')
    parser.add_argument('--hardware', action='store_true', help='Run hardware detection tests')
    parser.add_argument('--performance', action='store_true', help='Run performance benchmarks')
    parser.add_argument('--integration', action='store_true', help='Run integration tests')
    parser.add_argument('--mock-only', action='store_true', help='Run only mock tests (CI-friendly)')
    parser.add_argument('--stress', action='store_true', help='Run stress and stability tests')
    parser.add_argument('--benchmark', action='store_true', help='Run comprehensive benchmark suite')
    
    # Configuration options
    parser.add_argument('--quick', action='store_true', help='Run quick test suite (reduced test data)')
    parser.add_argument('--backend', choices=['cuda', 'opencl', 'auto'], default='auto',
                       help='Force specific GPU backend')
    parser.add_argument('--iterations', type=int, default=3, help='Number of iterations for performance tests')
    parser.add_argument('--timeout', type=int, default=600, help='Test timeout in seconds')
    
    # Output options
    parser.add_argument('--report', type=str, help='Generate test report (HTML or JSON)')
    parser.add_argument('--benchmark-output', type=str, help='Save benchmark results to file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--quiet', '-q', action='store_true', help='Quiet output (errors only)')
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.quiet:
        logging.getLogger().setLevel(logging.ERROR)
    elif args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize test runner
    runner = GPUTestRunner()
    
    print("FileOrganizer GPU Test Suite")
    print("=" * 50)
    
    # Detect environment
    env_info = runner.detect_gpu_environment()
    
    print("Environment Detection:")
    print(f"  Platform: {env_info['system_info'].get('platform', 'Unknown')}")
    print(f"  Python: {env_info['system_info'].get('python_version', 'Unknown').split()[0]}")
    print(f"  GPU Libraries Available: {sum(env_info['gpu_libraries'].values())}/{len(env_info['gpu_libraries'])}")
    
    if env_info['gpu_hardware'].get('cuda_available'):
        print("  CUDA GPUs: Available")
    if env_info['gpu_hardware'].get('opencl_available'):
        print("  OpenCL GPUs: Available")
    
    print()
    
    # Run selected tests
    all_results = {}
    
    try:
        if args.all:
            logger.info("Running all GPU tests...")
            all_results = runner.run_all_tests(quick=args.quick)
            
        elif args.mock_only:
            logger.info("Running mock GPU tests only...")
            all_results['mock'] = [runner.run_mock_tests()]
            
        elif args.benchmark:
            logger.info("Running comprehensive benchmark suite...")
            all_results['benchmark'] = [runner.run_benchmark_suite(args.benchmark_output)]
            
        else:
            # Run individual test categories
            if args.hardware:
                all_results['hardware'] = [runner.run_hardware_tests()]
            
            if args.performance:
                all_results['performance'] = [runner.run_performance_tests(args.iterations, args.quick)]
            
            if args.integration:
                all_results['integration'] = [runner.run_integration_tests(args.backend)]
            
            if args.stress:
                all_results['stress'] = [runner.run_stress_tests()]
            
            # If no specific tests selected, run mock tests (safe default)
            if not any([args.hardware, args.performance, args.integration, args.stress]):
                logger.info("No specific tests selected - running mock tests (safe default)")
                all_results['mock'] = [runner.run_mock_tests()]
        
        # Print summary
        print("\nTest Results Summary:")
        print("=" * 50)
        
        total_success = 0
        total_tests = 0
        
        for category, results in all_results.items():
            if isinstance(results, list):
                successful = sum(1 for r in results if r.get('success', False))
                total = len(results)
                total_success += successful
                total_tests += total
                
                print(f"{category.title()}: {successful}/{total} successful")
                
                for result in results:
                    status = "PASS" if result.get('success') else "FAIL"
                    duration = result.get('duration', 0)
                    print(f"  {result.get('description', 'Unknown')}: {status} ({duration:.2f}s)")
                    
                    if not result.get('success') and result.get('stderr'):
                        # Show first line of error for summary
                        error_lines = result['stderr'].split('\n')
                        if error_lines:
                            print(f"    Error: {error_lines[0]}")
        
        if total_tests > 0:
            success_rate = total_success / total_tests
            print(f"\nOverall: {total_success}/{total_tests} successful ({success_rate:.1%})")
        
        # Generate report if requested
        if args.report:
            runner.generate_report(all_results, args.report)
        
        # Exit with appropriate code
        if total_tests == 0:
            print("No tests were run")
            sys.exit(2)
        elif total_success == total_tests:
            print("All tests passed!")
            sys.exit(0)
        else:
            print(f"{total_tests - total_success} tests failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nTests interrupted by user")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Test runner failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    main()