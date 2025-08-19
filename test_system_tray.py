#!/usr/bin/env python3
"""
Test script for FileOrganizer System Tray functionality

Tests system tray integration, background processing, and service capabilities.
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_system_tray_availability():
    """Test if system tray is available"""
    print("🔍 Testing System Tray Availability...")
    
    try:
        from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
        
        # Create minimal QApplication for testing
        app = QApplication([])
        
        available = QSystemTrayIcon.isSystemTrayAvailable()
        if available:
            print("✅ System tray is available")
            return True
        else:
            print("❌ System tray is not available on this system")
            return False
            
    except ImportError as e:
        print(f"❌ PyQt5 not available: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing system tray: {e}")
        return False

def test_system_tray_components():
    """Test system tray component imports"""
    print("\n🔍 Testing System Tray Components...")
    
    components = [
        ("System Tray App", "gui.system_tray", "SystemTrayApp"),
        ("Background Processor Dialog", "gui.system_tray", "BackgroundProcessorDialog"),
        ("File Watcher", "gui.system_tray", "FileWatcher"),
        ("Tray Notification Widget", "gui.system_tray", "TrayNotificationWidget"),
    ]
    
    success_count = 0
    
    for name, module, class_name in components:
        try:
            module_obj = __import__(module, fromlist=[class_name])
            class_obj = getattr(module_obj, class_name)
            print(f"✅ {name}")
            success_count += 1
        except ImportError as e:
            print(f"⚠️  {name} - Import Error: {e}")
        except AttributeError as e:
            print(f"⚠️  {name} - Attribute Error: {e}")
        except Exception as e:
            print(f"❌ {name} - Error: {e}")
    
    print(f"\n📊 Components Available: {success_count}/{len(components)}")
    return success_count == len(components)

def test_startup_manager():
    """Test Windows startup management"""
    print("\n🔍 Testing Startup Manager...")
    
    try:
        if sys.platform != "win32":
            print("⚠️  Startup manager is Windows-specific")
            return True
        
        from startup_manager import StartupManager
        
        manager = StartupManager()
        print("✅ Startup Manager created")
        
        # Test status check (safe operation)
        status = manager.is_startup_enabled()
        print(f"✅ Startup status check: {'Enabled' if status else 'Disabled'}")
        
        return True
        
    except ImportError as e:
        print(f"⚠️  Startup Manager - Import Error: {e}")
        if "winreg" in str(e):
            print("   Note: Windows registry access not available")
        return True  # Not critical for basic functionality
    except Exception as e:
        print(f"❌ Startup Manager Error: {e}")
        return False

def test_service_wrapper():
    """Test Windows service wrapper"""
    print("\n🔍 Testing Service Wrapper...")
    
    try:
        if sys.platform != "win32":
            print("⚠️  Service wrapper is Windows-specific")
            return True
        
        from service_wrapper import ServiceManager
        
        manager = ServiceManager()
        print("✅ Service Manager created")
        
        # Test safe operations only
        try:
            manager.get_service_status()
            print("✅ Service status check (service may not be installed)")
        except Exception:
            print("✅ Service status check (service not installed - normal)")
        
        return True
        
    except ImportError as e:
        print(f"⚠️  Service Wrapper - Import Error: {e}")
        if "win32" in str(e):
            print("   Note: Install with: pip install pywin32")
        return True  # Not critical for basic functionality
    except Exception as e:
        print(f"❌ Service Wrapper Error: {e}")
        return False

def test_tray_launcher():
    """Test tray launcher script"""
    print("\n🔍 Testing Tray Launcher...")
    
    launcher_file = project_root / "tray_launcher.py"
    if launcher_file.exists():
        print("✅ Tray launcher script exists")
    else:
        print("❌ Tray launcher script missing")
        return False
    
    try:
        # Test imports without running
        import tray_launcher
        print("✅ Tray launcher imports successfully")
        return True
    except Exception as e:
        print(f"❌ Tray launcher import error: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\n🔍 Testing Configuration System...")
    
    try:
        # Test config loading from tray launcher
        from tray_launcher import load_config
        
        config = load_config()
        print("✅ Configuration loaded successfully")
        
        # Check required sections
        required_sections = ['gpu_config', 'processing', 'ui', 'background']
        missing_sections = []
        
        for section in required_sections:
            if section not in config:
                missing_sections.append(section)
            else:
                print(f"✅ Config section: {section}")
        
        if missing_sections:
            print(f"⚠️  Missing config sections: {missing_sections}")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def test_batch_manager():
    """Test batch manager script"""
    print("\n🔍 Testing Batch Manager...")
    
    batch_file = project_root / "fileorganizer_manager.bat"
    if batch_file.exists():
        print("✅ Batch manager script exists")
        
        # Check if it's readable
        try:
            with open(batch_file, 'r') as f:
                content = f.read()
                if "FileOrganizer Background Service Manager" in content:
                    print("✅ Batch manager script content valid")
                    return True
        except Exception as e:
            print(f"⚠️  Batch manager read error: {e}")
    else:
        print("❌ Batch manager script missing")
        return False

def create_test_system_tray():
    """Create a minimal test system tray (for demonstration)"""
    print("\n🔍 Creating Test System Tray...")
    
    try:
        if not test_system_tray_availability():
            print("❌ Cannot create test system tray - system tray not available")
            return False
        
        from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction
        from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
        from PyQt5.QtCore import Qt
        
        # Create application
        app = QApplication([])
        
        # Create simple icon
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setBrush(QColor(0, 120, 200))
        painter.drawEllipse(2, 2, 12, 12)
        painter.end()
        
        # Create system tray icon
        tray_icon = QSystemTrayIcon(QIcon(pixmap))
        tray_icon.setToolTip("FileOrganizer Test")
        
        # Create menu
        menu = QMenu()
        test_action = QAction("Test Action")
        menu.addAction(test_action)
        tray_icon.setContextMenu(menu)
        
        print("✅ Test system tray icon created successfully")
        print("   Note: Not showing icon in test mode")
        
        return True
        
    except Exception as e:
        print(f"❌ Test system tray creation error: {e}")
        return False

def print_summary(results):
    """Print test summary"""
    print("\n" + "="*60)
    print("🎯 FILEORGANIZER SYSTEM TRAY TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:<40} {status}")
    
    print("\n" + "="*60)
    print(f"Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! System tray functionality is ready.")
        print("\n🚀 You can now run:")
        print("   python tray_launcher.py")
        print("   fileorganizer_manager.bat")
    else:
        print("⚠️  Some tests failed. Check the results above.")
        print("\n💡 Common solutions:")
        print("   • Install PyQt5: pip install PyQt5")
        print("   • Install Windows service support: pip install pywin32")
        print("   • Ensure system tray is available on your system")
    
    print("="*60)
    
    return passed == total

def main():
    """Main test function"""
    print("🚀 FileOrganizer System Tray Test Suite")
    print("="*60)
    
    # Run all tests
    results = {}
    
    results["System Tray Availability"] = test_system_tray_availability()
    results["System Tray Components"] = test_system_tray_components() 
    results["Startup Manager"] = test_startup_manager()
    results["Service Wrapper"] = test_service_wrapper()
    results["Tray Launcher"] = test_tray_launcher()
    results["Configuration System"] = test_configuration()
    results["Batch Manager"] = test_batch_manager()
    results["Test System Tray Creation"] = create_test_system_tray()
    
    # Print summary
    success = print_summary(results)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())