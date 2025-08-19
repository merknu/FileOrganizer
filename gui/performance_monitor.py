"""
Performance Monitoring Dashboard for FileOrganizer

Real-time performance metrics, processing statistics, and visual charts.
"""

import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QProgressBar, QGroupBox, QGridLayout, QTabWidget,
                           QTextEdit, QTableWidget, QTableWidgetItem, 
                           QHeaderView, QFrame, QSizePolicy)
from PyQt5.QtCore import QTimer, pyqtSignal, QThread, pyqtSlot, Qt
from PyQt5.QtGui import QFont, QPainter, QColor, QPen
from typing import Dict, Any, List, Optional
import logging
import time
from datetime import datetime, timedelta
from collections import deque
import json

# Try to import matplotlib for charts (optional)
try:
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False


class SimpleChart(QWidget):
    """Simple chart widget for displaying performance data"""
    
    def __init__(self, title: str = "", max_points: int = 60, parent=None):
        super().__init__(parent)
        self.title = title
        self.max_points = max_points
        self.data_points = deque(maxlen=max_points)
        self.time_points = deque(maxlen=max_points)
        self.setMinimumSize(200, 100)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    
    def add_data_point(self, value: float, timestamp: Optional[datetime] = None):
        """Add a new data point to the chart"""
        if timestamp is None:
            timestamp = datetime.now()
        
        self.data_points.append(value)
        self.time_points.append(timestamp)
        self.update()
    
    def clear_data(self):
        """Clear all data points"""
        self.data_points.clear()
        self.time_points.clear()
        self.update()
    
    def paintEvent(self, event):
        """Paint the chart"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get widget dimensions
        rect = self.rect()
        margin = 20
        chart_rect = rect.adjusted(margin, margin, -margin, -margin)
        
        # Clear background
        painter.fillRect(rect, QColor(240, 240, 240))
        
        # Draw title
        if self.title:
            painter.setFont(QFont("", 10, QFont.Bold))
            painter.drawText(rect.adjusted(0, 0, 0, -rect.height() + 15), Qt.AlignCenter, self.title)
        
        if len(self.data_points) < 2:
            painter.setFont(QFont("", 9))
            painter.drawText(chart_rect, Qt.AlignCenter, "No data")
            return
        
        # Draw chart border
        painter.setPen(QPen(QColor(100, 100, 100), 1))
        painter.drawRect(chart_rect)
        
        # Calculate scales
        min_val = min(self.data_points)
        max_val = max(self.data_points)
        if max_val == min_val:
            max_val = min_val + 1
        
        # Draw data line
        painter.setPen(QPen(QColor(0, 120, 200), 2))
        
        points = []
        for i, value in enumerate(self.data_points):
            x = chart_rect.left() + (i / (len(self.data_points) - 1)) * chart_rect.width()
            y = chart_rect.bottom() - ((value - min_val) / (max_val - min_val)) * chart_rect.height()
            points.append((x, y))
        
        # Draw connecting lines
        for i in range(len(points) - 1):
            painter.drawLine(points[i][0], points[i][1], points[i+1][0], points[i+1][1])
        
        # Draw value labels
        painter.setFont(QFont("", 8))
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        
        # Max value
        painter.drawText(chart_rect.left() - 15, chart_rect.top() + 10, f"{max_val:.1f}")
        
        # Min value
        painter.drawText(chart_rect.left() - 15, chart_rect.bottom() + 5, f"{min_val:.1f}")


class PerformanceStatsWidget(QWidget):
    """Widget displaying performance statistics"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.stats = {
            'files_processed': 0,
            'total_files': 0,
            'processing_speed': 0.0,
            'average_file_size': 0.0,
            'total_processing_time': 0.0,
            'gpu_utilization': 0.0,
            'memory_usage': 0.0,
            'errors_count': 0,
            'duplicates_found': 0,
            'space_saved': 0
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the statistics display"""
        layout = QGridLayout(self)
        
        # Processing Statistics
        layout.addWidget(QLabel("Files Processed:"), 0, 0)
        self.files_processed_label = QLabel("0 / 0")
        self.files_processed_label.setFont(QFont("", 9, QFont.Bold))
        layout.addWidget(self.files_processed_label, 0, 1)
        
        layout.addWidget(QLabel("Processing Speed:"), 1, 0)
        self.speed_label = QLabel("0.0 files/sec")
        self.speed_label.setFont(QFont("", 9, QFont.Bold))
        layout.addWidget(self.speed_label, 1, 1)
        
        layout.addWidget(QLabel("Average File Size:"), 2, 0)
        self.file_size_label = QLabel("0.0 MB")
        self.file_size_label.setFont(QFont("", 9, QFont.Bold))
        layout.addWidget(self.file_size_label, 2, 1)
        
        layout.addWidget(QLabel("Total Time:"), 3, 0)
        self.total_time_label = QLabel("0:00:00")
        self.total_time_label.setFont(QFont("", 9, QFont.Bold))
        layout.addWidget(self.total_time_label, 3, 1)
        
        # System Statistics
        layout.addWidget(QLabel("GPU Utilization:"), 0, 2)
        self.gpu_util_label = QLabel("0%")
        self.gpu_util_label.setFont(QFont("", 9, QFont.Bold))
        layout.addWidget(self.gpu_util_label, 0, 3)
        
        layout.addWidget(QLabel("Memory Usage:"), 1, 2)
        self.memory_label = QLabel("0 MB")
        self.memory_label.setFont(QFont("", 9, QFont.Bold))
        layout.addWidget(self.memory_label, 1, 3)
        
        layout.addWidget(QLabel("Errors:"), 2, 2)
        self.errors_label = QLabel("0")
        self.errors_label.setFont(QFont("", 9, QFont.Bold))
        layout.addWidget(self.errors_label, 2, 3)
        
        layout.addWidget(QLabel("Duplicates:"), 3, 2)
        self.duplicates_label = QLabel("0")
        self.duplicates_label.setFont(QFont("", 9, QFont.Bold))
        layout.addWidget(self.duplicates_label, 3, 3)
        
        # Add separator
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator, 0, 4, 4, 1)
        
        # Space saved
        layout.addWidget(QLabel("Space Saved:"), 1, 5)
        self.space_saved_label = QLabel("0 MB")
        self.space_saved_label.setFont(QFont("", 10, QFont.Bold))
        self.space_saved_label.setStyleSheet("color: green;")
        layout.addWidget(self.space_saved_label, 1, 6)
        
        layout.setColumnStretch(7, 1)
    
    def update_stats(self, stats: Dict[str, Any]):
        """Update the displayed statistics"""
        self.stats.update(stats)
        
        # Update labels
        self.files_processed_label.setText(f"{self.stats['files_processed']} / {self.stats['total_files']}")
        self.speed_label.setText(f"{self.stats['processing_speed']:.1f} files/sec")
        
        # Format file size
        avg_size_mb = self.stats['average_file_size'] / (1024 * 1024) if self.stats['average_file_size'] else 0
        self.file_size_label.setText(f"{avg_size_mb:.1f} MB")
        
        # Format time
        total_time = int(self.stats['total_processing_time'])
        hours, remainder = divmod(total_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.total_time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # System stats
        self.gpu_util_label.setText(f"{self.stats['gpu_utilization']:.0f}%")
        self.memory_label.setText(f"{self.stats['memory_usage']:.0f} MB")
        self.errors_label.setText(str(self.stats['errors_count']))
        self.duplicates_label.setText(str(self.stats['duplicates_found']))
        
        # Space saved
        space_mb = self.stats['space_saved'] / (1024 * 1024) if self.stats['space_saved'] else 0
        self.space_saved_label.setText(f"{space_mb:.1f} MB")


class PerformanceMonitorWidget(QWidget):
    """Main performance monitoring widget with tabs and real-time charts"""
    
    stats_updated = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.update_timer = QTimer()
        self.start_time = None
        self.is_monitoring = False
        
        # Performance tracking
        self.performance_history = {
            'processing_speed': deque(maxlen=100),
            'gpu_utilization': deque(maxlen=100),
            'memory_usage': deque(maxlen=100),
            'queue_size': deque(maxlen=100)
        }
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Create tabs
        self.tab_widget = QTabWidget()
        
        # Overview Tab
        overview_tab = QWidget()
        overview_layout = QVBoxLayout(overview_tab)
        
        # Statistics display
        self.stats_widget = PerformanceStatsWidget()
        overview_layout.addWidget(self.stats_widget)
        
        # Progress bars
        progress_group = QGroupBox("Current Operation Progress")
        progress_layout = QGridLayout(progress_group)
        
        # Overall progress
        progress_layout.addWidget(QLabel("Overall:"), 0, 0)
        self.overall_progress = QProgressBar()
        self.overall_progress.setMaximum(100)
        progress_layout.addWidget(self.overall_progress, 0, 1)
        self.overall_progress_label = QLabel("0%")
        progress_layout.addWidget(self.overall_progress_label, 0, 2)
        
        # Current file progress
        progress_layout.addWidget(QLabel("Current File:"), 1, 0)
        self.file_progress = QProgressBar()
        self.file_progress.setMaximum(100)
        progress_layout.addWidget(self.file_progress, 1, 1)
        self.current_file_label = QLabel("Ready")
        progress_layout.addWidget(self.current_file_label, 1, 2)
        
        overview_layout.addWidget(progress_group)
        overview_layout.addStretch()
        
        self.tab_widget.addTab(overview_tab, "Overview")
        
        # Charts Tab
        charts_tab = QWidget()
        charts_layout = QGridLayout(charts_tab)
        
        # Processing Speed Chart
        self.speed_chart = SimpleChart("Processing Speed (files/sec)", max_points=60)
        charts_layout.addWidget(self.speed_chart, 0, 0)
        
        # GPU Utilization Chart
        self.gpu_chart = SimpleChart("GPU Utilization (%)", max_points=60)
        charts_layout.addWidget(self.gpu_chart, 0, 1)
        
        # Memory Usage Chart
        self.memory_chart = SimpleChart("Memory Usage (MB)", max_points=60)
        charts_layout.addWidget(self.memory_chart, 1, 0)
        
        # Queue Size Chart
        self.queue_chart = SimpleChart("Queue Size", max_points=60)
        charts_layout.addWidget(self.queue_chart, 1, 1)
        
        self.tab_widget.addTab(charts_tab, "Performance Charts")
        
        # Detailed Log Tab
        log_tab = QWidget()
        log_layout = QVBoxLayout(log_tab)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Courier", 8))
        self.log_display.setMaximumBlockCount(1000)  # Limit log size
        log_layout.addWidget(self.log_display)
        
        self.tab_widget.addTab(log_tab, "Processing Log")
        
        layout.addWidget(self.tab_widget)
    
    def setup_connections(self):
        """Setup signal connections"""
        self.update_timer.timeout.connect(self.update_performance_data)
    
    def start_monitoring(self):
        """Start performance monitoring"""
        if not self.is_monitoring:
            self.is_monitoring = True
            self.start_time = time.time()
            self.update_timer.start(1000)  # Update every second
            self.log_message("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring"""
        if self.is_monitoring:
            self.is_monitoring = False
            self.update_timer.stop()
            self.log_message("Performance monitoring stopped")
    
    def reset_statistics(self):
        """Reset all statistics and charts"""
        # Clear charts
        self.speed_chart.clear_data()
        self.gpu_chart.clear_data()
        self.memory_chart.clear_data()
        self.queue_chart.clear_data()
        
        # Clear history
        for key in self.performance_history:
            self.performance_history[key].clear()
        
        # Reset progress bars
        self.overall_progress.setValue(0)
        self.file_progress.setValue(0)
        self.overall_progress_label.setText("0%")
        self.current_file_label.setText("Ready")
        
        # Clear log
        self.log_display.clear()
        
        self.log_message("Statistics and charts reset")
    
    @pyqtSlot(dict)
    def update_performance_data(self, stats: Optional[Dict[str, Any]] = None):
        """Update performance data and charts"""
        if not self.is_monitoring:
            return
        
        current_time = datetime.now()
        
        # If no stats provided, generate sample data (for demo)
        if stats is None:
            stats = self.generate_sample_stats()
        
        # Update statistics widget
        self.stats_widget.update_stats(stats)
        
        # Update charts
        self.speed_chart.add_data_point(stats.get('processing_speed', 0), current_time)
        self.gpu_chart.add_data_point(stats.get('gpu_utilization', 0), current_time)
        self.memory_chart.add_data_point(stats.get('memory_usage', 0), current_time)
        self.queue_chart.add_data_point(stats.get('queue_size', 0), current_time)
        
        # Store in history
        self.performance_history['processing_speed'].append(stats.get('processing_speed', 0))
        self.performance_history['gpu_utilization'].append(stats.get('gpu_utilization', 0))
        self.performance_history['memory_usage'].append(stats.get('memory_usage', 0))
        self.performance_history['queue_size'].append(stats.get('queue_size', 0))
    
    def generate_sample_stats(self) -> Dict[str, Any]:
        """Generate sample statistics for demonstration"""
        import random
        
        elapsed_time = time.time() - self.start_time if self.start_time else 0
        
        return {
            'files_processed': int(elapsed_time * 2.5),
            'total_files': 1000,
            'processing_speed': random.uniform(2.0, 5.0),
            'average_file_size': random.uniform(1024*1024, 10*1024*1024),
            'total_processing_time': elapsed_time,
            'gpu_utilization': random.uniform(0, 85),
            'memory_usage': random.uniform(500, 2048),
            'queue_size': max(0, 1000 - int(elapsed_time * 2.5)),
            'errors_count': random.randint(0, 5),
            'duplicates_found': random.randint(0, 50),
            'space_saved': random.uniform(0, 100*1024*1024)
        }
    
    def update_progress(self, overall_percent: float, current_file: str = "", file_percent: float = 0):
        """Update progress indicators"""
        self.overall_progress.setValue(int(overall_percent))
        self.overall_progress_label.setText(f"{overall_percent:.1f}%")
        
        self.file_progress.setValue(int(file_percent))
        
        if current_file:
            # Truncate long filenames
            if len(current_file) > 40:
                current_file = current_file[:20] + "..." + current_file[-17:]
            self.current_file_label.setText(current_file)
    
    def log_message(self, message: str, level: str = "INFO"):
        """Add a message to the processing log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {level}: {message}"
        self.log_display.append(formatted_message)
        
        # Auto-scroll to bottom
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get a summary of current performance metrics"""
        if not self.performance_history['processing_speed']:
            return {}
        
        return {
            'avg_processing_speed': sum(self.performance_history['processing_speed']) / len(self.performance_history['processing_speed']),
            'max_processing_speed': max(self.performance_history['processing_speed']),
            'avg_gpu_utilization': sum(self.performance_history['gpu_utilization']) / len(self.performance_history['gpu_utilization']),
            'avg_memory_usage': sum(self.performance_history['memory_usage']) / len(self.performance_history['memory_usage']),
            'max_memory_usage': max(self.performance_history['memory_usage']),
            'monitoring_duration': time.time() - self.start_time if self.start_time else 0
        }


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QPushButton, QVBoxLayout
    import sys
    
    app = QApplication(sys.argv)
    
    # Create test window
    window = QWidget()
    layout = QVBoxLayout(window)
    
    # Add performance monitor
    monitor = PerformanceMonitorWidget()
    layout.addWidget(monitor)
    
    # Add control buttons
    button_layout = QHBoxLayout()
    start_button = QPushButton("Start Monitoring")
    stop_button = QPushButton("Stop Monitoring")
    reset_button = QPushButton("Reset")
    
    start_button.clicked.connect(monitor.start_monitoring)
    stop_button.clicked.connect(monitor.stop_monitoring)
    reset_button.clicked.connect(monitor.reset_statistics)
    
    button_layout.addWidget(start_button)
    button_layout.addWidget(stop_button)
    button_layout.addWidget(reset_button)
    
    layout.addLayout(button_layout)
    
    window.setWindowTitle("Performance Monitor Test")
    window.resize(800, 600)
    window.show()
    
    sys.exit(app.exec_())