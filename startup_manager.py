"""
Startup Manager for FileOrganizer

Handles Windows startup integration and auto-start functionality.
"""

import os
import sys
import winreg
import logging
from pathlib import Path
from typing import Optional

class StartupManager:
    """Manages Windows startup integration"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.app_name = "FileOrganizer"
        self.registry_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        self.project_root = Path(__file__).parent
    
    def is_startup_enabled(self) -> bool:
        """Check if FileOrganizer is enabled for startup"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path, 0, winreg.KEY_READ) as key:
                try:
                    winreg.QueryValueEx(key, self.app_name)
                    return True
                except FileNotFoundError:
                    return False
        except Exception as e:
            self.logger.error(f"Error checking startup status: {e}")
            return False
    
    def enable_startup(self) -> bool:
        """Enable FileOrganizer to start with Windows"""
        try:
            # Create the command to run
            python_exe = sys.executable
            script_path = self.project_root / "tray_launcher.py"
            command = f'"{python_exe}" "{script_path}"'
            
            # Add to registry
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path, 0, winreg.KEY_WRITE) as key:
                winreg.SetValueEx(key, self.app_name, 0, winreg.REG_SZ, command)
            
            self.logger.info("Startup enabled successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Error enabling startup: {e}")
            return False
    
    def disable_startup(self) -> bool:
        """Disable FileOrganizer from starting with Windows"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path, 0, winreg.KEY_WRITE) as key:
                winreg.DeleteValue(key, self.app_name)
            
            self.logger.info("Startup disabled successfully")
            return True
            
        except FileNotFoundError:
            # Already not in startup
            return True
        except Exception as e:
            self.logger.error(f"Error disabling startup: {e}")
            return False
    
    def toggle_startup(self) -> bool:
        """Toggle startup state and return new state"""
        if self.is_startup_enabled():
            self.disable_startup()
            return False
        else:
            self.enable_startup()
            return True
    
    def get_startup_command(self) -> Optional[str]:
        """Get the current startup command"""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path, 0, winreg.KEY_READ) as key:
                command, _ = winreg.QueryValueEx(key, self.app_name)
                return command
        except Exception:
            return None

def create_startup_shortcut():
    """Create a startup shortcut (alternative method)"""
    try:
        import winshell
        from win32com.client import Dispatch
        
        startup_folder = winshell.startup()
        shortcut_path = os.path.join(startup_folder, "FileOrganizer.lnk")
        
        # Remove existing shortcut
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
        
        # Create new shortcut
        target = sys.executable
        arguments = str(Path(__file__).parent / "tray_launcher.py")
        working_dir = str(Path(__file__).parent)
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target
        shortcut.Arguments = arguments
        shortcut.WorkingDirectory = working_dir
        shortcut.Description = "FileOrganizer Background Service"
        shortcut.WindowStyle = 7  # Minimized
        shortcut.save()
        
        print(f"Startup shortcut created: {shortcut_path}")
        return True
        
    except ImportError:
        print("Error: winshell module not available")
        return False
    except Exception as e:
        print(f"Error creating startup shortcut: {e}")
        return False

def remove_startup_shortcut():
    """Remove startup shortcut"""
    try:
        import winshell
        
        startup_folder = winshell.startup()
        shortcut_path = os.path.join(startup_folder, "FileOrganizer.lnk")
        
        if os.path.exists(shortcut_path):
            os.remove(shortcut_path)
            print("Startup shortcut removed")
            return True
        else:
            print("No startup shortcut found")
            return True
            
    except Exception as e:
        print(f"Error removing startup shortcut: {e}")
        return False

def main():
    """Main function for testing startup manager"""
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) < 2:
        print("Usage: python startup_manager.py [enable|disable|status|toggle|shortcut-add|shortcut-remove]")
        sys.exit(1)
    
    action = sys.argv[1].lower()
    manager = StartupManager()
    
    if action == "enable":
        if manager.enable_startup():
            print("✅ FileOrganizer enabled for startup")
        else:
            print("❌ Failed to enable startup")
    
    elif action == "disable":
        if manager.disable_startup():
            print("✅ FileOrganizer disabled from startup")
        else:
            print("❌ Failed to disable startup")
    
    elif action == "status":
        if manager.is_startup_enabled():
            print("✅ FileOrganizer is enabled for startup")
            command = manager.get_startup_command()
            if command:
                print(f"Command: {command}")
        else:
            print("❌ FileOrganizer is not enabled for startup")
    
    elif action == "toggle":
        new_state = manager.toggle_startup()
        status = "enabled" if new_state else "disabled"
        print(f"✅ FileOrganizer startup {status}")
    
    elif action == "shortcut-add":
        if create_startup_shortcut():
            print("✅ Startup shortcut created")
        else:
            print("❌ Failed to create startup shortcut")
    
    elif action == "shortcut-remove":
        if remove_startup_shortcut():
            print("✅ Startup shortcut removed")
        else:
            print("❌ Failed to remove startup shortcut")
    
    else:
        print(f"Unknown action: {action}")
        sys.exit(1)

if __name__ == "__main__":
    main()