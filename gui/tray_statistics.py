"""
System Tray Statistics Manager for FileOrganizer

Tracks and displays real-time statistics in the system tray tooltip.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from PyQt5.QtWidgets import QApplication
import logging


@dataclass
class ProcessingEvent:
    """Single file processing event"""
    timestamp: str
    file_path: str
    action: str  # "organized", "skipped", "error"
    source_folder: str
    destination_folder: Optional[str] = None
    file_size: int = 0
    processing_time: float = 0.0


@dataclass
class DailyStats:
    """Daily processing statistics"""
    date: str
    files_organized: int = 0
    files_skipped: int = 0
    files_error: int = 0
    total_size_mb: float = 0.0
    processing_time: float = 0.0
    folders_processed: int = 0


class StatisticsManager(QObject):
    """Manages processing statistics and tooltip updates"""
    
    tooltip_updated = pyqtSignal(str)  # New tooltip text
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        
        # Statistics storage
        self.stats_file = Path("data/statistics.json")
        self.stats_file.parent.mkdir(exist_ok=True)
        
        # Current session data
        self.session_start = datetime.now()
        self.current_activity = "Idle"
        self.current_file = ""
        self.current_folders = []
        self.is_monitoring = False
        
        # Statistics data
        self.daily_stats: Dict[str, DailyStats] = {}
        self.recent_events: List[ProcessingEvent] = []
        self.total_stats = {
            'total_files_organized': 0,
            'total_files_processed': 0,
            'total_size_mb': 0.0,
            'total_folders_processed': 0,
            'first_run_date': None
        }
        
        # Load existing statistics
        self.load_statistics()
        
        # Setup update timer
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_tooltip)
        self.update_timer.start(2000)  # Update every 2 seconds
    
    def load_statistics(self):
        """Load statistics from persistent storage"""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    data = json.load(f)
                
                # Load daily stats
                if 'daily_stats' in data:
                    for date_str, stats_dict in data['daily_stats'].items():
                        self.daily_stats[date_str] = DailyStats(**stats_dict)
                
                # Load total stats
                if 'total_stats' in data:
                    self.total_stats.update(data['total_stats'])
                
                # Load recent events
                if 'recent_events' in data:
                    for event_dict in data['recent_events'][-100:]:  # Keep last 100 events
                        self.recent_events.append(ProcessingEvent(**event_dict))
                
                self.logger.info("Statistics loaded successfully")
            else:
                # First run - set first run date
                self.total_stats['first_run_date'] = datetime.now().isoformat()
                
        except Exception as e:
            self.logger.error(f"Error loading statistics: {e}")
    
    def save_statistics(self):
        """Save statistics to persistent storage"""
        try:
            data = {
                'daily_stats': {
                    date_str: asdict(stats) for date_str, stats in self.daily_stats.items()
                },
                'total_stats': self.total_stats,
                'recent_events': [
                    asdict(event) for event in self.recent_events[-100:]  # Keep last 100
                ],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.stats_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving statistics: {e}")
    
    def record_processing_event(self, file_path: str, action: str, 
                              source_folder: str, destination_folder: Optional[str] = None,
                              file_size: int = 0, processing_time: float = 0.0):
        """Record a file processing event"""
        try:
            # Create event
            event = ProcessingEvent(
                timestamp=datetime.now().isoformat(),
                file_path=file_path,
                action=action,
                source_folder=source_folder,
                destination_folder=destination_folder,
                file_size=file_size,
                processing_time=processing_time
            )
            
            # Add to recent events
            self.recent_events.append(event)
            
            # Update daily stats
            today = datetime.now().strftime('%Y-%m-%d')
            if today not in self.daily_stats:
                self.daily_stats[today] = DailyStats(date=today)
            
            daily = self.daily_stats[today]
            
            if action == "organized":
                daily.files_organized += 1
                self.total_stats['total_files_organized'] += 1
            elif action == "skipped":
                daily.files_skipped += 1
            elif action == "error":
                daily.files_error += 1
            
            daily.total_size_mb += file_size / (1024 * 1024)
            daily.processing_time += processing_time
            
            # Update totals
            self.total_stats['total_files_processed'] += 1
            self.total_stats['total_size_mb'] += file_size / (1024 * 1024)
            
            # Cleanup old data (keep last 90 days)
            self.cleanup_old_data()
            
            # Save periodically
            if len(self.recent_events) % 10 == 0:  # Save every 10 events
                self.save_statistics()
            
            self.logger.debug(f"Recorded event: {action} - {os.path.basename(file_path)}")
            
        except Exception as e:
            self.logger.error(f"Error recording processing event: {e}")
    
    def set_current_activity(self, activity: str, file_path: str = "", folders: List[str] = None):
        """Update current activity status"""
        self.current_activity = activity
        self.current_file = file_path
        self.current_folders = folders or []
        
        # Trigger immediate tooltip update for activity changes
        self.update_tooltip()
    
    def set_monitoring_status(self, is_monitoring: bool, folders: List[str] = None):
        """Update monitoring status"""
        self.is_monitoring = is_monitoring
        if folders:
            self.current_folders = folders
        
        if is_monitoring:
            self.set_current_activity("Monitoring folders", folders=folders)
        else:
            self.set_current_activity("Idle")
    
    def get_today_stats(self) -> DailyStats:
        """Get today's statistics"""
        today = datetime.now().strftime('%Y-%m-%d')
        return self.daily_stats.get(today, DailyStats(date=today))
    
    def get_last_30_days_stats(self) -> Dict[str, int]:
        """Get statistics for the last 30 days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=30)
        
        total_organized = 0
        total_processed = 0
        total_size_mb = 0.0
        total_errors = 0
        
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            if date_str in self.daily_stats:
                stats = self.daily_stats[date_str]
                total_organized += stats.files_organized
                total_processed += stats.files_organized + stats.files_skipped + stats.files_error
                total_size_mb += stats.total_size_mb
                total_errors += stats.files_error
            
            current_date += timedelta(days=1)
        
        return {
            'files_organized': total_organized,
            'files_processed': total_processed,
            'total_size_mb': total_size_mb,
            'errors': total_errors
        }
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get current session statistics"""
        session_events = [
            event for event in self.recent_events
            if datetime.fromisoformat(event.timestamp) >= self.session_start
        ]
        
        organized = sum(1 for e in session_events if e.action == "organized")
        errors = sum(1 for e in session_events if e.action == "error")
        total_size = sum(e.file_size for e in session_events)
        
        return {
            'files_organized': organized,
            'files_processed': len(session_events),
            'errors': errors,
            'total_size_mb': total_size / (1024 * 1024),
            'duration': datetime.now() - self.session_start
        }
    
    def update_tooltip(self):
        """Update the system tray tooltip with current information"""
        try:
            # Get statistics
            today_stats = self.get_today_stats()
            last_30_days = self.get_last_30_days_stats()
            session_stats = self.get_session_stats()
            
            # Build tooltip text
            tooltip_lines = []
            
            # Header
            tooltip_lines.append("📁 FileOrganizer")
            
            # Current status
            status_icon = "🟢" if self.is_monitoring else "⏸️"
            tooltip_lines.append(f"{status_icon} Status: {self.current_activity}")
            
            # Current file being processed
            if self.current_file and self.current_activity not in ["Idle", "Monitoring folders"]:
                filename = os.path.basename(self.current_file)
                if len(filename) > 30:
                    filename = filename[:27] + "..."
                tooltip_lines.append(f"🔄 Processing: {filename}")
            
            # Monitored folders
            if self.is_monitoring and self.current_folders:
                folder_count = len(self.current_folders)
                if folder_count == 1:
                    folder_name = os.path.basename(self.current_folders[0])
                    tooltip_lines.append(f"👁️ Watching: {folder_name}")
                else:
                    tooltip_lines.append(f"👁️ Watching: {folder_count} folders")
            
            # Add separator
            tooltip_lines.append("─" * 25)
            
            # Today's statistics
            tooltip_lines.append(f"📅 Today: {today_stats.files_organized} organized")
            if today_stats.files_error > 0:
                tooltip_lines.append(f"⚠️ Today: {today_stats.files_error} errors")
            
            # Last 30 days
            tooltip_lines.append(f"📊 30 days: {last_30_days['files_organized']} organized")
            
            # Total statistics  
            total_organized = self.total_stats['total_files_organized']
            if total_organized > 0:
                tooltip_lines.append(f"🎯 Total: {total_organized:,} files organized")
            
            # Data size information
            total_size_gb = self.total_stats['total_size_mb'] / 1024
            if total_size_gb > 0.1:
                if total_size_gb >= 1:
                    tooltip_lines.append(f"💾 Total: {total_size_gb:.1f} GB processed")
                else:
                    tooltip_lines.append(f"💾 Total: {self.total_stats['total_size_mb']:.0f} MB processed")
            
            # Session information
            if session_stats['files_organized'] > 0:
                duration = session_stats['duration']
                hours = int(duration.total_seconds() // 3600)
                minutes = int((duration.total_seconds() % 3600) // 60)
                
                if hours > 0:
                    session_time = f"{hours}h {minutes}m"
                else:
                    session_time = f"{minutes}m"
                
                tooltip_lines.append(f"⏱️ Session: {session_stats['files_organized']} files ({session_time})")
            
            # First run information
            if self.total_stats['first_run_date']:
                try:
                    first_run = datetime.fromisoformat(self.total_stats['first_run_date'])
                    days_active = (datetime.now() - first_run).days
                    if days_active > 0:
                        tooltip_lines.append(f"📈 Active: {days_active} days")
                except:
                    pass
            
            # Join all lines
            tooltip_text = '\n'.join(tooltip_lines)
            
            # Emit the updated tooltip
            self.tooltip_updated.emit(tooltip_text)
            
        except Exception as e:
            self.logger.error(f"Error updating tooltip: {e}")
            # Fallback tooltip
            self.tooltip_updated.emit("📁 FileOrganizer\n⚠️ Error loading statistics")
    
    def cleanup_old_data(self):
        """Remove old data to keep storage size manageable"""
        try:
            # Remove daily stats older than 90 days
            cutoff_date = datetime.now() - timedelta(days=90)
            cutoff_str = cutoff_date.strftime('%Y-%m-%d')
            
            old_dates = [
                date for date in self.daily_stats.keys()
                if date < cutoff_str
            ]
            
            for date in old_dates:
                del self.daily_stats[date]
            
            # Keep only last 1000 events
            if len(self.recent_events) > 1000:
                self.recent_events = self.recent_events[-1000:]
            
            if old_dates:
                self.logger.info(f"Cleaned up {len(old_dates)} old daily records")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")
    
    def get_statistics_summary(self) -> Dict[str, Any]:
        """Get a comprehensive statistics summary"""
        today_stats = self.get_today_stats()
        last_30_days = self.get_last_30_days_stats()
        session_stats = self.get_session_stats()
        
        return {
            'current_status': {
                'activity': self.current_activity,
                'monitoring': self.is_monitoring,
                'folders_watched': len(self.current_folders),
                'current_file': os.path.basename(self.current_file) if self.current_file else None
            },
            'today': {
                'files_organized': today_stats.files_organized,
                'files_skipped': today_stats.files_skipped,
                'errors': today_stats.files_error,
                'size_mb': today_stats.total_size_mb
            },
            'last_30_days': last_30_days,
            'session': session_stats,
            'total': self.total_stats,
            'recent_activity': [
                {
                    'file': os.path.basename(event.file_path),
                    'action': event.action,
                    'time': event.timestamp
                }
                for event in self.recent_events[-5:]  # Last 5 events
            ]
        }
    
    def __del__(self):
        """Ensure statistics are saved on cleanup"""
        try:
            self.save_statistics()
        except:
            pass


class TooltipFormatter:
    """Helper class for formatting tooltip text"""
    
    @staticmethod
    def format_file_size(size_bytes: float) -> str:
        """Format file size for display"""
        if size_bytes < 1024:
            return f"{size_bytes:.0f} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes/(1024*1024):.1f} MB"
        else:
            return f"{size_bytes/(1024*1024*1024):.1f} GB"
    
    @staticmethod
    def format_duration(duration: timedelta) -> str:
        """Format duration for display"""
        total_seconds = int(duration.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}m"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    @staticmethod
    def format_number(number: int) -> str:
        """Format number with commas for display"""
        return f"{number:,}"


if __name__ == "__main__":
    # Test the statistics manager
    import sys
    from PyQt5.QtWidgets import QApplication, QSystemTrayIcon
    from PyQt5.QtCore import QTimer
    
    app = QApplication(sys.argv)
    
    # Create statistics manager
    stats_manager = StatisticsManager()
    
    # Simulate some processing events
    def simulate_processing():
        import random
        from pathlib import Path

        actions = ["organized", "organized", "organized", "skipped", "error"]
        # Use platform-independent paths for testing
        home = Path.home()
        folders = [str(home / "Downloads"), str(home / "Desktop"), str(home / "Documents")]

        action = random.choice(actions)
        folder = random.choice(folders)
        filename = f"test_file_{random.randint(1, 1000)}.txt"
        file_path = os.path.join(folder, filename)

        stats_manager.record_processing_event(
            file_path=file_path,
            action=action,
            source_folder=folder,
            destination_folder=str(home / "Organized") if action == "organized" else None,
            file_size=random.randint(1024, 10*1024*1024),
            processing_time=random.uniform(0.1, 2.0)
        )

        if random.random() > 0.7:
            stats_manager.set_current_activity("Processing files", file_path, [folder])
        else:
            stats_manager.set_monitoring_status(True, folders)
    
    # Set up test timer
    test_timer = QTimer()
    test_timer.timeout.connect(simulate_processing)
    test_timer.start(3000)  # Simulate processing every 3 seconds
    
    # Set up tooltip display
    def on_tooltip_updated(text):
        print("=" * 50)
        print("TOOLTIP CONTENT:")
        print("=" * 50)
        print(text)
        print("=" * 50)
        print()
    
    stats_manager.tooltip_updated.connect(on_tooltip_updated)
    
    # Start monitoring
    from pathlib import Path
    home = Path.home()
    stats_manager.set_monitoring_status(True, [str(home / "Downloads"), str(home / "Desktop")])
    
    print("Testing statistics manager...")
    print("Tooltip will update every 2 seconds")
    print("Processing events simulated every 3 seconds")
    print("Press Ctrl+C to exit")
    
    try:
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print("\nTest completed")
        stats_manager.save_statistics()
        print("Statistics saved")