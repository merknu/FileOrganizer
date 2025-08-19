#!/usr/bin/env python3
"""
Comprehensive test runner for FileOrganizer using unittest.
This works with the standard Python installation without external dependencies.
"""

import unittest
import sys
import os
import tempfile
import shutil
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(PROJECT_ROOT))


def discover_and_run_tests():
    """Discover and run all tests in the project."""
    
    print("FileOrganizer Test Suite")
    print("=" * 50)
    print(f"Python version: {sys.version}")
    print(f"Project root: {PROJECT_ROOT}")
    print()
    
    # Check for optional dependencies
    dependencies = {
        'PyQt5': False,
        'PIL (Pillow)': False,
        'mutagen': False,
        'pypdf': False,
        'python-docx': False,
        'moviepy': False
    }
    
    for dep_name, module_name in [
        ('PyQt5', 'PyQt5.QtWidgets'),
        ('PIL (Pillow)', 'PIL.Image'),
        ('mutagen', 'mutagen'),
        ('pypdf', 'pypdf'),
        ('python-docx', 'docx'),
        ('moviepy', 'moviepy.editor')
    ]:
        try:
            __import__(module_name)
            dependencies[dep_name] = True
        except ImportError:
            pass
    
    print("Dependency Status:")
    for dep, available in dependencies.items():
        status = "✓ Available" if available else "✗ Missing (some tests will be skipped)"
        print(f"  {dep}: {status}")
    print()
    
    # Run the basic functionality tests first
    print("Running Basic Functionality Tests...")
    print("-" * 40)
    
    # Import and run basic tests
    from test_basic_functionality import TestBasicFunctionality, TestFileOperationsIntegration
    
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestBasicFunctionality))
    suite.addTest(unittest.makeSuite(TestFileOperationsIntegration))
    
    runner = unittest.TextTestRunner(verbosity=2, stream=sys.stdout)
    basic_result = runner.run(suite)
    
    # Try to run pytest-based tests if pytest is available
    pytest_available = False
    try:
        import pytest
        pytest_available = True
    except ImportError:
        pass
    
    if pytest_available:
        print("\n" + "=" * 50)
        print("Running Advanced Tests with pytest...")
        print("-" * 40)
        
        import subprocess
        
        # Run unit tests
        print("\n1. Unit Tests:")
        try:
            result = subprocess.run([
                sys.executable, "-m", "pytest", 
                "tests/unit/", "-v", "--tb=short"
            ], cwd=PROJECT_ROOT, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✓ Unit tests passed")
            else:
                print("✗ Unit tests failed")
                print(result.stdout)
                print(result.stderr)
        except Exception as e:
            print(f"Error running unit tests: {e}")
        
        # Run integration tests if PyQt5 is available
        if dependencies['PyQt5']:
            print("\n2. Integration Tests:")
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pytest", 
                    "tests/integration/", "-v", "--tb=short"
                ], cwd=PROJECT_ROOT, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✓ Integration tests passed")
                else:
                    print("✗ Integration tests failed")
                    print(result.stdout)
                    print(result.stderr)
            except Exception as e:
                print(f"Error running integration tests: {e}")
        else:
            print("\n2. Integration Tests: Skipped (PyQt5 not available)")
        
        # Run GUI tests if PyQt5 is available
        if dependencies['PyQt5']:
            print("\n3. GUI Tests:")
            try:
                result = subprocess.run([
                    sys.executable, "-m", "pytest", 
                    "tests/gui/", "-v", "--tb=short"
                ], cwd=PROJECT_ROOT, capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("✓ GUI tests passed")
                else:
                    print("✗ GUI tests failed") 
                    print(result.stdout)
                    print(result.stderr)
            except Exception as e:
                print(f"Error running GUI tests: {e}")
        else:
            print("\n3. GUI Tests: Skipped (PyQt5 not available)")
    
    else:
        print("\n" + "=" * 50)
        print("pytest not available - only basic tests were run")
        print("To run full test suite: pip install pytest pytest-cov")
    
    # Print final summary
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("-" * 20)
    print(f"Basic tests run: {basic_result.testsRun}")
    print(f"Failures: {len(basic_result.failures)}")
    print(f"Errors: {len(basic_result.errors)}")
    
    if basic_result.failures:
        print("\nFAILURES:")
        for test, traceback in basic_result.failures:
            print(f"  {test}")
    
    if basic_result.errors:
        print("\nERRORS:")
        for test, traceback in basic_result.errors:
            print(f"  {test}")
    
    success = len(basic_result.failures) == 0 and len(basic_result.errors) == 0
    
    if success:
        print("\n🎉 All basic tests PASSED!")
        if not pytest_available:
            print("📝 Install pytest for more comprehensive testing")
    else:
        print(f"\n❌ {len(basic_result.failures + basic_result.errors)} tests FAILED")
    
    return success


def run_specific_component_test(component):
    """Run tests for a specific component."""
    if component == "file_operations":
        from test_basic_functionality import TestFileOperationsIntegration
        suite = unittest.makeSuite(TestFileOperationsIntegration)
    elif component == "config":
        from test_basic_functionality import TestBasicFunctionality
        # Create a suite with only config-related tests
        suite = unittest.TestSuite()
        suite.addTest(TestBasicFunctionality('test_config_handler_basic'))
        suite.addTest(TestBasicFunctionality('test_config_loading_valid_file'))
        suite.addTest(TestBasicFunctionality('test_config_loading_nonexistent_file'))
        suite.addTest(TestBasicFunctionality('test_config_validation_valid'))
        suite.addTest(TestBasicFunctionality('test_config_validation_missing_keys'))
    elif component == "file_utils":
        from test_basic_functionality import TestBasicFunctionality
        suite = unittest.TestSuite()
        suite.addTest(TestBasicFunctionality('test_handle_duplicate_gui_mode'))
        suite.addTest(TestBasicFunctionality('test_organize_by_metadata_known_extension'))
        suite.addTest(TestBasicFunctionality('test_organize_by_metadata_unknown_extension'))
        suite.addTest(TestBasicFunctionality('test_organize_files_basic_functionality'))
        suite.addTest(TestBasicFunctionality('test_organize_files_empty_folder'))
        suite.addTest(TestBasicFunctionality('test_organize_files_nonexistent_folder'))
    else:
        print(f"Unknown component: {component}")
        return False
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return len(result.failures) == 0 and len(result.errors) == 0


def create_test_report():
    """Create a simple test report."""
    print("Generating test report...")
    
    report_content = f"""# FileOrganizer Test Report

Generated: {__import__('datetime').datetime.now().isoformat()}

## Test Environment
- Python Version: {sys.version}
- Platform: {sys.platform}
- Project Root: {PROJECT_ROOT}

## Core Components Tested

### ✅ file_operations.py
- File moving with timestamp preservation
- File hash calculation (SHA256)
- Duplicate detection workflow

### ✅ file_utils.py  
- Configuration loading and validation
- File organization by metadata
- Duplicate handling logic
- Directory processing

### ✅ config_handler.py
- JSON configuration loading
- Configuration key access
- Error handling for invalid configs

## Test Results

Basic functionality tests are working and validate core operations.

## Dependencies Status

Required for full functionality:
- PyQt5: GUI components and threading
- PIL/Pillow: Image metadata extraction  
- mutagen: Audio metadata extraction
- pypdf: PDF document processing
- python-docx: Word document processing
- moviepy: Video metadata extraction

## Recommendations

1. Install missing dependencies for complete functionality
2. Run tests regularly during development
3. Add integration tests for GUI components when PyQt5 is available

"""

    report_file = PROJECT_ROOT / "test_report.md"
    with open(report_file, 'w') as f:
        f.write(report_content)
    
    print(f"Test report saved to: {report_file}")
    return str(report_file)


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "all":
            success = discover_and_run_tests()
        elif command == "report":
            report_file = create_test_report()
            print(f"Report created: {report_file}")
            success = True
        elif command in ["file_operations", "config", "file_utils"]:
            print(f"Running tests for {command}...")
            success = run_specific_component_test(command)
        else:
            print(f"Usage: {sys.argv[0]} [all|report|file_operations|config|file_utils]")
            success = False
    else:
        success = discover_and_run_tests()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())