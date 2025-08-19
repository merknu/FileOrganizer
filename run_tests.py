#!/usr/bin/env python3
"""
Comprehensive test runner for FileOrganizer application.

This script provides various testing options including:
- Running specific test categories (unit, integration, GUI)
- Generating coverage reports
- Performance testing
- Automated test data setup and cleanup
"""

import os
import sys
import argparse
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import List, Optional

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))


class TestRunner:
    """Main test runner class."""
    
    def __init__(self):
        """Initialize test runner."""
        self.project_root = PROJECT_ROOT
        self.tests_dir = self.project_root / "tests"
        self.temp_dir = None
        
    def setup_test_environment(self):
        """Setup test environment and temporary directories."""
        # Create temporary directory for test data
        self.temp_dir = tempfile.mkdtemp(prefix="fileorganizer_tests_")
        print(f"Created temporary test directory: {self.temp_dir}")
        
        # Set environment variable for tests
        os.environ['FILEORGANIZER_TEST_TEMP_DIR'] = self.temp_dir
        
        return self.temp_dir
    
    def cleanup_test_environment(self):
        """Clean up test environment."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            print(f"Cleaned up temporary test directory: {self.temp_dir}")
    
    def run_pytest(self, args: List[str]) -> int:
        """Run pytest with specified arguments."""
        cmd = [sys.executable, "-m", "pytest"] + args
        print(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            return result.returncode
        except KeyboardInterrupt:
            print("\nTest execution interrupted by user")
            return 130
        except Exception as e:
            print(f"Error running tests: {e}")
            return 1
    
    def run_unit_tests(self, verbose: bool = False, coverage: bool = False) -> int:
        """Run unit tests."""
        args = ["-m", "unit"]
        
        if verbose:
            args.append("-v")
        
        if coverage:
            args.extend([
                "--cov=file_handler",
                "--cov=config",
                "--cov-report=html:tests/coverage_html_unit",
                "--cov-report=term-missing"
            ])
        
        print("Running unit tests...")
        return self.run_pytest(args)
    
    def run_integration_tests(self, verbose: bool = False) -> int:
        """Run integration tests."""
        args = ["-m", "integration"]
        
        if verbose:
            args.append("-v")
        
        print("Running integration tests...")
        return self.run_pytest(args)
    
    def run_gui_tests(self, verbose: bool = False) -> int:
        """Run GUI tests."""
        # Check if PyQt5 is available
        try:
            import PyQt5
            print("PyQt5 found, running GUI tests...")
        except ImportError:
            print("PyQt5 not available, skipping GUI tests")
            return 0
        
        args = ["-m", "gui"]
        
        if verbose:
            args.append("-v")
        
        return self.run_pytest(args)
    
    def run_all_tests(self, verbose: bool = False, coverage: bool = False) -> int:
        """Run all tests."""
        args = []
        
        if verbose:
            args.append("-v")
        
        if coverage:
            args.extend([
                "--cov=file_handler",
                "--cov=config", 
                "--cov=gui",
                "--cov-report=html:tests/coverage_html_all",
                "--cov-report=term-missing",
                "--cov-report=xml:tests/coverage.xml"
            ])
        
        print("Running all tests...")
        return self.run_pytest(args)
    
    def run_fast_tests(self) -> int:
        """Run only fast tests (exclude slow markers)."""
        args = ["-m", "not slow"]
        print("Running fast tests only...")
        return self.run_pytest(args)
    
    def run_specific_test(self, test_path: str, verbose: bool = False) -> int:
        """Run a specific test file or test function."""
        args = [test_path]
        
        if verbose:
            args.append("-v")
        
        print(f"Running specific test: {test_path}")
        return self.run_pytest(args)
    
    def run_performance_tests(self) -> int:
        """Run performance-focused tests."""
        print("Setting up performance test data...")
        
        # Import test fixtures to create performance test files
        try:
            from tests.fixtures.test_files import TestDataManager
            
            perf_dir = os.path.join(self.temp_dir, "performance")
            test_manager = TestDataManager(perf_dir)
            
            # Create many test files
            files = test_manager.create_performance_test_files(file_count=500)
            print(f"Created {len(files)} test files for performance testing")
            
            # Run tests that work with many files
            args = [
                "-k", "performance or large or many",
                "-v",
                "--durations=10"  # Show 10 slowest tests
            ]
            
            result = self.run_pytest(args)
            
            # Cleanup
            test_manager.cleanup()
            
            return result
            
        except ImportError as e:
            print(f"Could not import test fixtures: {e}")
            return 1
    
    def check_dependencies(self):
        """Check if required dependencies are available."""
        dependencies = {
            'pytest': 'pytest',
            'pytest-cov': 'pytest_cov',
            'unittest.mock': 'unittest.mock'
        }
        
        optional_dependencies = {
            'PyQt5': 'PyQt5.QtWidgets',
            'PIL': 'PIL.Image',
            'mutagen': 'mutagen',
            'pypdf': 'pypdf',
            'python-docx': 'docx',
            'moviepy': 'moviepy.editor'
        }
        
        print("Checking dependencies...")
        
        # Required dependencies
        missing_required = []
        for name, module in dependencies.items():
            try:
                __import__(module)
                print(f"  ✓ {name}")
            except ImportError:
                print(f"  ✗ {name} (REQUIRED)")
                missing_required.append(name)
        
        # Optional dependencies
        missing_optional = []
        for name, module in optional_dependencies.items():
            try:
                __import__(module)
                print(f"  ✓ {name}")
            except ImportError:
                print(f"  ! {name} (OPTIONAL - some tests will be skipped)")
                missing_optional.append(name)
        
        if missing_required:
            print(f"\nMissing required dependencies: {', '.join(missing_required)}")
            print("Install with: pip install pytest pytest-cov")
            return False
        
        if missing_optional:
            print(f"\nOptional dependencies not found: {', '.join(missing_optional)}")
            print("Some tests will be skipped. To run all tests, install:")
            print("pip install PyQt5 Pillow mutagen pypdf python-docx moviepy")
        
        return True
    
    def generate_test_report(self) -> int:
        """Generate comprehensive test report."""
        print("Generating comprehensive test report...")
        
        args = [
            "--html=tests/report.html",
            "--self-contained-html",
            "--cov=file_handler",
            "--cov=config",
            "--cov=gui", 
            "--cov-report=html:tests/coverage_html_report",
            "--cov-report=xml:tests/coverage.xml",
            "--junit-xml=tests/junit.xml",
            "-v"
        ]
        
        # Try to install pytest-html if not available
        try:
            import pytest_html
        except ImportError:
            print("Installing pytest-html for HTML reports...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pytest-html"])
        
        return self.run_pytest(args)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="FileOrganizer Test Runner")
    
    parser.add_argument(
        "command",
        choices=["unit", "integration", "gui", "all", "fast", "performance", "check", "report"],
        help="Test command to run"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--coverage", "-c",
        action="store_true",
        help="Generate coverage reports"
    )
    
    parser.add_argument(
        "--test", "-t",
        help="Run specific test file or function"
    )
    
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Don't cleanup temporary files (for debugging)"
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Check dependencies first
    if not runner.check_dependencies():
        return 1
    
    # Setup test environment
    try:
        runner.setup_test_environment()
        
        # Run requested command
        if args.command == "unit":
            result = runner.run_unit_tests(args.verbose, args.coverage)
        elif args.command == "integration":
            result = runner.run_integration_tests(args.verbose)
        elif args.command == "gui":
            result = runner.run_gui_tests(args.verbose)
        elif args.command == "all":
            result = runner.run_all_tests(args.verbose, args.coverage)
        elif args.command == "fast":
            result = runner.run_fast_tests()
        elif args.command == "performance":
            result = runner.run_performance_tests()
        elif args.command == "check":
            print("Dependencies checked successfully!")
            result = 0
        elif args.command == "report":
            result = runner.generate_test_report()
        elif args.test:
            result = runner.run_specific_test(args.test, args.verbose)
        else:
            print("No valid command specified")
            result = 1
    
    except KeyboardInterrupt:
        print("\nTest execution interrupted")
        result = 130
    except Exception as e:
        print(f"Error during test execution: {e}")
        result = 1
    finally:
        # Cleanup unless requested not to
        if not args.no_cleanup:
            runner.cleanup_test_environment()
    
    # Print summary
    if result == 0:
        print("\n✅ Tests completed successfully!")
    else:
        print(f"\n❌ Tests failed with exit code {result}")
    
    return result


if __name__ == "__main__":
    sys.exit(main())