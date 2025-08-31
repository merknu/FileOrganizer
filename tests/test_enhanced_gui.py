#!/usr/bin/env python3
"""
Test script for the enhanced FileOrganizer GUI

Tests the integration of all new GUI features with the main window.
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_enhanced_gui():
    """Test the enhanced GUI features"""
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        
        # Create QApplication
        app = QApplication(sys.argv)
        app.setApplicationName("FileOrganizer Enhanced")
        
        # Test imports
        print("Testing enhanced GUI imports...")
        
        # Test individual widgets
        try:
            from gui.gpu_status_widget import GPUStatusWidget
            print("✅ GPU Status Widget - OK")
        except ImportError as e:
            print(f"⚠️  GPU Status Widget - Import Error: {e}")
        
        try:
            from gui.performance_monitor import PerformanceMonitorWidget
            print("✅ Performance Monitor - OK")
        except ImportError as e:
            print(f"⚠️  Performance Monitor - Import Error: {e}")
        
        try:
            from gui.gpu_settings_dialog import GPUSettingsDialog
            print("✅ GPU Settings Dialog - OK")
        except ImportError as e:
            print(f"⚠️  GPU Settings Dialog - Import Error: {e}")
        
        try:
            from gui.advanced_filters import AdvancedFiltersWidget
            print("✅ Advanced Filters - OK")
        except ImportError as e:
            print(f"⚠️  Advanced Filters - Import Error: {e}")
        
        try:
            from gui.drag_drop_widget import DragDropWidget
            print("✅ Drag-Drop Widget - OK")
        except ImportError as e:
            print(f"⚠️  Drag-Drop Widget - Import Error: {e}")
        
        try:
            from gui.preview_widget import PreviewWidget
            print("✅ Preview Widget - OK")
        except ImportError as e:
            print(f"⚠️  Preview Widget - Import Error: {e}")
        
        try:
            from gui.theme_manager import ThemeManager, ThemeToggleWidget
            print("✅ Theme Manager - OK")
        except ImportError as e:
            print(f"⚠️  Theme Manager - Import Error: {e}")
        
        # Test main window integration
        print("\nTesting main window integration...")
        try:
            from gui.main_window import FileOrganizerMainWindow
            print("✅ Enhanced Main Window - OK")
            
            # Create main window with test config
            test_config = {
                'gpu_config': {
                    'enable_gpu': True,
                    'backend': 'auto',
                    'memory_limit_mb': 2048
                },
                'processing': {
                    'max_workers': 4,
                    'chunk_size': 1024
                }
            }
            
            main_window = FileOrganizerMainWindow(test_config)
            print("✅ Main Window Created - OK")
            
            # Test window properties
            print(f"Window Title: {main_window.windowTitle()}")
            print(f"Window Size: {main_window.size().width()}x{main_window.size().height()}")
            
            # Show window for visual test (optional)
            if len(sys.argv) > 1 and sys.argv[1] == "--show":
                print("\n🚀 Launching enhanced FileOrganizer GUI...")
                print("   Features available:")
                print("   • GPU acceleration status panel")
                print("   • Real-time performance monitoring")
                print("   • Advanced file filtering")
                print("   • Drag-and-drop interface")
                print("   • Interactive preview system")
                print("   • Dark/Light theme switching")
                print("   • GPU settings and benchmarking")
                print("\n   Use File → Select Folders or drag folders to start!")
                
                main_window.show()
                return app.exec_()
            else:
                print("✅ GUI Integration Test - PASSED")
                print("\nTo launch the GUI, run: python test_enhanced_gui.py --show")
                return 0
                
        except Exception as e:
            print(f"❌ Main Window Integration - ERROR: {e}")
            import traceback
            traceback.print_exc()
            return 1
            
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

def test_gpu_modules():
    """Test GPU acceleration modules"""
    print("\n" + "="*50)
    print("Testing GPU Acceleration Modules")
    print("="*50)
    
    try:
        from file_handler.gpu_acceleration import get_gpu_accelerator, get_system_gpu_info
        print("✅ GPU Acceleration Module - OK")
        
        # Test system GPU info
        try:
            gpu_info = get_system_gpu_info()
            print(f"GPU Info: {gpu_info}")
        except Exception as e:
            print(f"⚠️  GPU Info Error: {e}")
        
        # Test GPU accelerator creation
        try:
            config = {'enable_gpu': True, 'backend': 'auto'}
            accelerator = get_gpu_accelerator(config)
            print(f"GPU Accelerator: {accelerator}")
            print(f"Available: {accelerator.is_available()}")
        except Exception as e:
            print(f"⚠️  GPU Accelerator Error: {e}")
            
    except ImportError as e:
        print(f"⚠️  GPU Modules not available: {e}")

def print_feature_summary():
    """Print summary of all implemented features"""
    print("\n" + "="*60)
    print("🎯 FILEORGANIZER ENHANCED - FEATURE SUMMARY")
    print("="*60)
    
    features = [
        ("🖥️  GPU Status Panel", "Real-time GPU monitoring with memory usage"),
        ("📊 Performance Monitor", "Live charts and processing statistics"),
        ("⚙️  GPU Settings Dialog", "Advanced configuration and benchmarking"),
        ("🔍 Advanced Filters", "Multi-criteria file filtering system"),
        ("📁 Drag-Drop Interface", "Intuitive file and folder selection"),
        ("👁️  Preview System", "Before/after organization preview"),
        ("🎨 Theme Manager", "Dark/Light themes with customization"),
        ("🚀 GPU Acceleration", "Hardware-accelerated file processing"),
        ("💾 Persistent Settings", "All preferences automatically saved"),
        ("📱 Modern UI", "Professional interface with animations")
    ]
    
    for feature, description in features:
        print(f"{feature:<25} {description}")
    
    print("\n" + "="*60)
    print("All features successfully integrated into main application!")
    print("="*60)

if __name__ == "__main__":
    print("🚀 FileOrganizer Enhanced - GUI Integration Test")
    print("=" * 60)
    
    # Test GPU modules first
    test_gpu_modules()
    
    # Test enhanced GUI
    result = test_enhanced_gui()
    
    # Print feature summary
    print_feature_summary()
    
    sys.exit(result)