"""
Windows Service Wrapper for FileOrganizer

Allows FileOrganizer to run as a Windows service for true background operation.
"""

import sys
import os
import logging
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import win32serviceutil
    import win32service
    import win32event
    import servicemanager
    WINDOWS_SERVICE_AVAILABLE = True
except ImportError:
    WINDOWS_SERVICE_AVAILABLE = False

class FileOrganizerService(win32serviceutil.ServiceFramework):
    """Windows service for FileOrganizer"""
    
    _svc_name_ = "FileOrganizerService"
    _svc_display_name_ = "FileOrganizer Background Service"
    _svc_description_ = "Background file organization service with GPU acceleration"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.logger = self._setup_logging()
        self.is_running = False
        
    def _setup_logging(self):
        """Setup service logging"""
        log_dir = project_root / "logs"
        log_dir.mkdir(exist_ok=True)
        
        logger = logging.getLogger('FileOrganizerService')
        logger.setLevel(logging.INFO)
        
        # File handler
        handler = logging.FileHandler(log_dir / "service.log")
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def SvcStop(self):
        """Service stop handler"""
        self.logger.info("Service stop requested")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)
        self.is_running = False
        
    def SvcDoRun(self):
        """Service main execution"""
        self.logger.info("FileOrganizer Service starting...")
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                            servicemanager.PYS_SERVICE_STARTED,
                            (self._svc_name_, ''))
        
        self.is_running = True
        
        try:
            self.main_loop()
        except Exception as e:
            self.logger.error(f"Service error: {e}")
            servicemanager.LogMsg(servicemanager.EVENTLOG_ERROR_TYPE,
                                servicemanager.PYS_SERVICE_STOPPED,
                                (self._svc_name_, f'Error: {str(e)}'))
        
        self.logger.info("FileOrganizer Service stopped")
    
    def main_loop(self):
        """Main service loop"""
        self.logger.info("Starting main service loop...")
        
        # Initialize configuration
        config = self._load_config()
        
        # Initialize background processor
        from gui.system_tray import FileWatcher
        
        # Get watch folders from config
        watch_folders = config.get('background', {}).get('watch_folders', [])
        if not watch_folders:
            self.logger.warning("No watch folders configured")
            # Default to common folders if none specified
            watch_folders = [
                os.path.expanduser("~/Downloads"),
                os.path.expanduser("~/Desktop"),
            ]
            # Filter to existing folders
            watch_folders = [f for f in watch_folders if os.path.exists(f)]
        
        if watch_folders:
            self.logger.info(f"Watching folders: {watch_folders}")
            
            # Start file watcher
            watcher_config = config.get('background', {})
            file_watcher = FileWatcher(watch_folders, watcher_config)
            file_watcher.start()
            
            try:
                # Main service loop
                while self.is_running:
                    # Wait for stop event or timeout
                    rc = win32event.WaitForSingleObject(self.hWaitStop, 5000)  # 5 second timeout
                    
                    if rc == win32event.WAIT_OBJECT_0:
                        # Stop event was signaled
                        break
                    
                    # Perform periodic tasks here
                    self._periodic_maintenance()
                    
            finally:
                # Clean shutdown
                if file_watcher.isRunning():
                    file_watcher.stop()
                    file_watcher.wait(5000)
                    
        else:
            self.logger.error("No valid watch folders found")
            
        self.logger.info("Main service loop ended")
    
    def _load_config(self):
        """Load service configuration"""
        config_file = project_root / "service_config.json"
        
        default_config = {
            'background': {
                'watch_folders': [],
                'check_interval': 5,
                'min_age': 30,
                'auto_process': True,
                'show_notifications': False  # No GUI in service mode
            },
            'gpu_config': {
                'enable_gpu': True,
                'backend': 'auto',
                'memory_limit_mb': 1024
            },
            'processing': {
                'max_workers': 2,  # Conservative for service
                'chunk_size_mb': 16.0
            }
        }
        
        if config_file.exists():
            try:
                import json
                with open(config_file, 'r') as f:
                    saved_config = json.load(f)
                    default_config.update(saved_config)
                    self.logger.info("Loaded configuration from file")
            except Exception as e:
                self.logger.error(f"Error loading config: {e}")
        
        return default_config
    
    def _periodic_maintenance(self):
        """Perform periodic maintenance tasks"""
        # This could include:
        # - Log rotation
        # - Memory cleanup
        # - Health checks
        # - Statistics reporting
        pass

class ServiceManager:
    """Helper class for managing the FileOrganizer service"""
    
    def __init__(self):
        self.service_name = FileOrganizerService._svc_name_
        self.logger = logging.getLogger(__name__)
    
    def install_service(self):
        """Install the service"""
        try:
            win32serviceutil.InstallService(
                FileOrganizerService.__module__ + "." + FileOrganizerService.__name__,
                FileOrganizerService._svc_name_,
                FileOrganizerService._svc_display_name_,
                description=FileOrganizerService._svc_description_
            )
            print(f"✅ Service '{self.service_name}' installed successfully")
            return True
        except Exception as e:
            print(f"❌ Error installing service: {e}")
            return False
    
    def remove_service(self):
        """Remove the service"""
        try:
            win32serviceutil.RemoveService(self.service_name)
            print(f"✅ Service '{self.service_name}' removed successfully")
            return True
        except Exception as e:
            print(f"❌ Error removing service: {e}")
            return False
    
    def start_service(self):
        """Start the service"""
        try:
            win32serviceutil.StartService(self.service_name)
            print(f"✅ Service '{self.service_name}' started successfully")
            return True
        except Exception as e:
            print(f"❌ Error starting service: {e}")
            return False
    
    def stop_service(self):
        """Stop the service"""
        try:
            win32serviceutil.StopService(self.service_name)
            print(f"✅ Service '{self.service_name}' stopped successfully")
            return True
        except Exception as e:
            print(f"❌ Error stopping service: {e}")
            return False
    
    def restart_service(self):
        """Restart the service"""
        try:
            win32serviceutil.RestartService(self.service_name)
            print(f"✅ Service '{self.service_name}' restarted successfully")
            return True
        except Exception as e:
            print(f"❌ Error restarting service: {e}")
            return False
    
    def get_service_status(self):
        """Get service status"""
        try:
            status = win32serviceutil.QueryServiceStatus(self.service_name)
            state = status[1]
            
            state_names = {
                win32service.SERVICE_STOPPED: "Stopped",
                win32service.SERVICE_START_PENDING: "Starting",
                win32service.SERVICE_STOP_PENDING: "Stopping", 
                win32service.SERVICE_RUNNING: "Running",
                win32service.SERVICE_CONTINUE_PENDING: "Continue Pending",
                win32service.SERVICE_PAUSE_PENDING: "Pause Pending",
                win32service.SERVICE_PAUSED: "Paused"
            }
            
            state_name = state_names.get(state, f"Unknown ({state})")
            print(f"Service '{self.service_name}' status: {state_name}")
            return state
            
        except Exception as e:
            print(f"❌ Error checking service status: {e}")
            return None

def create_service_config():
    """Create default service configuration file"""
    config_file = project_root / "service_config.json"
    
    config = {
        "background": {
            "watch_folders": [
                os.path.expanduser("~/Downloads").replace('\\', '/'),
                os.path.expanduser("~/Desktop").replace('\\', '/'),
                os.path.expanduser("~/Documents").replace('\\', '/')
            ],
            "check_interval": 5,
            "min_age": 30,
            "auto_process": True,
            "show_notifications": False
        },
        "gpu_config": {
            "enable_gpu": True,
            "backend": "auto",
            "memory_limit_mb": 1024,
            "fallback_to_cpu": True
        },
        "processing": {
            "max_workers": 2,
            "chunk_size_mb": 16.0,
            "recursive": True,
            "handle_duplicates": True
        },
        "logging": {
            "level": "INFO",
            "max_log_size_mb": 10,
            "backup_count": 5
        }
    }
    
    try:
        import json
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Service configuration created: {config_file}")
        print("Edit this file to customize service behavior")
        return True
        
    except Exception as e:
        print(f"❌ Error creating service config: {e}")
        return False

def main():
    """Main function for service management"""
    if not WINDOWS_SERVICE_AVAILABLE:
        print("❌ Error: Windows service modules not available")
        print("Install with: pip install pywin32")
        sys.exit(1)
    
    if len(sys.argv) == 1:
        # Running as service
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(FileOrganizerService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        # Command line management
        action = sys.argv[1].lower()
        manager = ServiceManager()
        
        if action == "install":
            if manager.install_service():
                print("💡 You can now start the service with: python service_wrapper.py start")
        
        elif action == "remove" or action == "uninstall":
            manager.remove_service()
        
        elif action == "start":
            manager.start_service()
        
        elif action == "stop":
            manager.stop_service()
        
        elif action == "restart":
            manager.restart_service()
        
        elif action == "status":
            manager.get_service_status()
        
        elif action == "config":
            create_service_config()
        
        else:
            print("FileOrganizer Windows Service Manager")
            print("=" * 40)
            print()
            print("Usage: python service_wrapper.py [command]")
            print()
            print("Commands:")
            print("  install    Install the service")
            print("  remove     Remove the service")
            print("  start      Start the service")
            print("  stop       Stop the service")
            print("  restart    Restart the service")
            print("  status     Check service status")
            print("  config     Create default config file")
            print()
            print("Run without arguments to start as service")
            print()
            print("Note: Service management requires administrator privileges")

if __name__ == "__main__":
    main()