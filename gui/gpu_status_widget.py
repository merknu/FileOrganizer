"""
GPU Status Widget for FileOrganizer

Provides real-time GPU status monitoring and control interface.
"""

import sys
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                           QProgressBar, QPushButton, QGroupBox, QGridLayout,
                           QComboBox, QCheckBox, QSpinBox, QFrame)
from PyQt5.QtCore import QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor
from typing import Dict, Any, Optional
import logging

# Import GPU modules
try:
    from file_handler.gpu_acceleration import get_gpu_accelerator, get_system_gpu_info, GPUBackend
    from file_handler.gpu_monitor import GPUMonitor
    HAS_GPU_MODULES = True
except ImportError:
    HAS_GPU_MODULES = False


class GPUStatusIndicator(QLabel):
    """Visual GPU status indicator with color coding"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(16, 16)
        self.status = 'unknown'  # 'available', 'unavailable', 'error', 'unknown'
        self.update_indicator()
    
    def set_status(self, status: str):
        """Update GPU status and visual indicator"""
        self.status = status
        self.update_indicator()
    
    def update_indicator(self):
        """Update the visual indicator based on status"""
        pixmap = QPixmap(16, 16)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Set color based on status
        if self.status == 'available':
            color = QColor(0, 200, 0)  # Green
        elif self.status == 'unavailable':
            color = QColor(128, 128, 128)  # Gray
        elif self.status == 'error':
            color = QColor(200, 0, 0)  # Red
        else:
            color = QColor(255, 165, 0)  # Orange for unknown
        
        painter.setBrush(color)
        painter.drawEllipse(2, 2, 12, 12)
        painter.end()
        
        self.setPixmap(pixmap)


class GPUStatusWidget(QWidget):
    """GPU status and control widget"""
    
    gpu_settings_requested = pyqtSignal()
    gpu_benchmark_requested = pyqtSignal()
    gpu_toggle_requested = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.gpu_accelerator = None
        self.gpu_monitor = None
        self.update_timer = QTimer()
        
        self.setup_ui()
        self.setup_connections()
        self.initialize_gpu()
        
        # Start periodic updates
        self.update_timer.timeout.connect(self.update_gpu_status)
        self.update_timer.start(2000)  # Update every 2 seconds
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # GPU Status Group
        status_group = QGroupBox("GPU Acceleration")
        status_layout = QGridLayout(status_group)
        
        # Status indicator and text
        self.status_indicator = GPUStatusIndicator()
        self.status_label = QLabel("Detecting GPU...")
        self.status_label.setFont(QFont("", 9))
        
        status_layout.addWidget(QLabel("Status:"), 0, 0)
        status_layout.addWidget(self.status_indicator, 0, 1)
        status_layout.addWidget(self.status_label, 0, 2, 1, 2)
        
        # GPU device info
        self.device_label = QLabel("Device: Unknown")
        self.device_label.setFont(QFont("", 8))
        status_layout.addWidget(self.device_label, 1, 0, 1, 4)
        
        # Backend selection
        status_layout.addWidget(QLabel("Backend:"), 2, 0)
        self.backend_combo = QComboBox()
        self.backend_combo.addItems(["Auto", "CUDA", "OpenCL"])
        self.backend_combo.setCurrentText("Auto")
        status_layout.addWidget(self.backend_combo, 2, 1, 1, 2)
        
        # Enable/Disable toggle
        self.enable_checkbox = QCheckBox("Enable GPU Acceleration")
        self.enable_checkbox.setChecked(True)
        status_layout.addWidget(self.enable_checkbox, 3, 0, 1, 4)
        
        layout.addWidget(status_group)
        
        # Memory Usage Group
        memory_group = QGroupBox("GPU Memory")
        memory_layout = QVBoxLayout(memory_group)
        
        # Memory usage bar
        memory_info_layout = QHBoxLayout()
        memory_info_layout.addWidget(QLabel("Usage:"))
        self.memory_bar = QProgressBar()
        self.memory_bar.setMaximum(100)
        self.memory_bar.setValue(0)
        memory_info_layout.addWidget(self.memory_bar)
        
        self.memory_label = QLabel("0 MB / 0 MB")
        self.memory_label.setFont(QFont("", 8))
        memory_info_layout.addWidget(self.memory_label)
        memory_layout.addLayout(memory_info_layout)
        
        # Memory limit control
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(QLabel("Limit (MB):"))
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(256, 16384)
        self.memory_limit_spin.setValue(2048)
        self.memory_limit_spin.setSuffix(" MB")
        limit_layout.addWidget(self.memory_limit_spin)
        limit_layout.addStretch()
        memory_layout.addLayout(limit_layout)
        
        layout.addWidget(memory_group)
        
        # Performance Group
        perf_group = QGroupBox("Performance")
        perf_layout = QVBoxLayout(perf_group)
        
        self.speedup_label = QLabel("Speedup: Not measured")
        self.speedup_label.setFont(QFont("", 9))
        perf_layout.addWidget(self.speedup_label)
        
        self.throughput_label = QLabel("Throughput: 0 files/sec")
        self.throughput_label.setFont(QFont("", 9))
        perf_layout.addWidget(self.throughput_label)
        
        layout.addWidget(perf_group)
        
        # Control buttons
        button_layout = QHBoxLayout()
        
        self.settings_button = QPushButton("GPU Settings")
        self.benchmark_button = QPushButton("Run Benchmark")
        
        button_layout.addWidget(self.settings_button)
        button_layout.addWidget(self.benchmark_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()
    
    def setup_connections(self):
        """Setup signal connections"""
        self.enable_checkbox.toggled.connect(self.on_gpu_toggle)
        self.backend_combo.currentTextChanged.connect(self.on_backend_changed)
        self.settings_button.clicked.connect(self.gpu_settings_requested.emit)
        self.benchmark_button.clicked.connect(self.gpu_benchmark_requested.emit)
        self.memory_limit_spin.valueChanged.connect(self.on_memory_limit_changed)
    
    def initialize_gpu(self):
        """Initialize GPU components"""
        if not HAS_GPU_MODULES:
            self.status_indicator.set_status('error')
            self.status_label.setText("GPU modules not available")
            self.device_label.setText("Device: GPU support not installed")
            self.enable_checkbox.setEnabled(False)
            self.backend_combo.setEnabled(False)
            self.benchmark_button.setEnabled(False)
            return
        
        try:
            # Get system GPU info
            gpu_info = get_system_gpu_info()
            self.logger.info(f"GPU system info: {gpu_info}")
            
            # Initialize GPU accelerator
            config = {
                'enable_gpu': self.enable_checkbox.isChecked(),
                'backend': self.backend_combo.currentText().lower(),
                'run_initial_benchmark': False
            }
            
            self.gpu_accelerator = get_gpu_accelerator(config)
            
            # Initialize GPU monitor
            monitor_config = {
                'enable_monitoring': True,
                'metrics_history_size': 100
            }
            self.gpu_monitor = GPUMonitor(monitor_config)
            
            self.update_gpu_status()
            
        except Exception as e:
            self.logger.error(f"GPU initialization error: {e}")
            self.status_indicator.set_status('error')
            self.status_label.setText(f"GPU Error: {str(e)[:30]}...")
    
    @pyqtSlot()
    def update_gpu_status(self):
        """Update GPU status display"""
        if not self.gpu_accelerator:
            return
        
        try:
            # Update availability status
            is_available = self.gpu_accelerator.is_available()
            
            if is_available:
                self.status_indicator.set_status('available')
                self.status_label.setText("GPU Available")
                
                # Update device info
                device = self.gpu_accelerator.get_device_info()
                if device:
                    device_text = f"Device: {device.name} ({device.backend.value.upper()})"
                    self.device_label.setText(device_text)
                
                # Update memory usage
                used, total = self.gpu_accelerator.get_memory_usage()
                if total > 0:
                    usage_percent = int((used / total) * 100)
                    self.memory_bar.setValue(usage_percent)
                    self.memory_label.setText(f"{used:.0f} MB / {total:.0f} MB")
                else:
                    self.memory_bar.setValue(0)
                    self.memory_label.setText("Memory info unavailable")
                
                # Update performance stats
                if self.gpu_monitor:
                    try:
                        current_metrics = self.gpu_monitor.get_current_metrics()
                        perf_summary = self.gpu_monitor.get_performance_summary()
                        
                        # Extract performance data
                        if perf_summary and 'average_speedup' in perf_summary:
                            speedup = perf_summary['average_speedup']
                            self.speedup_label.setText(f"Speedup: {speedup:.1f}x")
                        
                        if perf_summary and 'throughput_files_per_sec' in perf_summary:
                            throughput = perf_summary['throughput_files_per_sec']
                            self.throughput_label.setText(f"Throughput: {throughput:.1f} files/sec")
                    
                    except Exception as e:
                        self.logger.debug(f"Performance metrics error: {e}")
            
            else:
                self.status_indicator.set_status('unavailable')
                self.status_label.setText("No GPU Available")
                self.device_label.setText("Device: Using CPU fallback")
                self.memory_bar.setValue(0)
                self.memory_label.setText("GPU memory not available")
                self.speedup_label.setText("Speedup: CPU only")
                self.throughput_label.setText("Throughput: Not measured")
        
        except Exception as e:
            self.logger.error(f"Error updating GPU status: {e}")
            self.status_indicator.set_status('error')
            self.status_label.setText("Status Error")
    
    @pyqtSlot(bool)
    def on_gpu_toggle(self, enabled: bool):
        """Handle GPU enable/disable toggle"""
        self.gpu_toggle_requested.emit(enabled)
        
        if self.gpu_accelerator:
            try:
                # Reinitialize with new setting
                config = {
                    'enable_gpu': enabled,
                    'backend': self.backend_combo.currentText().lower(),
                    'run_initial_benchmark': False
                }
                self.gpu_accelerator = get_gpu_accelerator(config)
                self.update_gpu_status()
            except Exception as e:
                self.logger.error(f"GPU toggle error: {e}")
    
    @pyqtSlot(str)
    def on_backend_changed(self, backend: str):
        """Handle backend selection change"""
        if self.gpu_accelerator:
            try:
                config = {
                    'enable_gpu': self.enable_checkbox.isChecked(),
                    'backend': backend.lower(),
                    'run_initial_benchmark': False
                }
                self.gpu_accelerator = get_gpu_accelerator(config)
                self.update_gpu_status()
            except Exception as e:
                self.logger.error(f"Backend change error: {e}")
    
    @pyqtSlot(int)
    def on_memory_limit_changed(self, limit_mb: int):
        """Handle memory limit change"""
        # This would be passed to GPU operations to limit memory usage
        self.logger.info(f"GPU memory limit set to {limit_mb} MB")
    
    def get_gpu_config(self) -> Dict[str, Any]:
        """Get current GPU configuration"""
        return {
            'enable_gpu': self.enable_checkbox.isChecked(),
            'backend': self.backend_combo.currentText().lower(),
            'memory_limit_mb': self.memory_limit_spin.value()
        }
    
    def closeEvent(self, event):
        """Cleanup on widget close"""
        if self.update_timer.isActive():
            self.update_timer.stop()
        
        if self.gpu_monitor:
            try:
                self.gpu_monitor.cleanup()
            except:
                pass
        
        super().closeEvent(event)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    widget = GPUStatusWidget()
    widget.show()
    sys.exit(app.exec_())