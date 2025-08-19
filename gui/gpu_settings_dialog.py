"""
GPU Settings Dialog for FileOrganizer

Advanced GPU configuration and benchmark interface.
"""

import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                           QComboBox, QSpinBox, QCheckBox, QGroupBox, 
                           QPushButton, QGridLayout, QTabWidget, QTextEdit,
                           QProgressBar, QMessageBox, QSlider, QDoubleSpinBox,
                           QTableWidget, QTableWidgetItem, QHeaderView,
                           QFrame, QSizePolicy)
from PyQt5.QtCore import QTimer, pyqtSignal, QThread, pyqtSlot, Qt
from PyQt5.QtGui import QFont, QPixmap, QPainter, QColor
from typing import Dict, Any, List, Optional
import logging
import json
import os
import time
from datetime import datetime

# Import GPU modules
try:
    from file_handler.gpu_acceleration import get_gpu_accelerator, get_system_gpu_info, GPUBackend
    from file_handler.gpu_monitor import GPUMonitor
    from benchmarks.gpu_benchmark import GPUBenchmarkSuite, BenchmarkConfig
    HAS_GPU_MODULES = True
except ImportError:
    HAS_GPU_MODULES = False


class BenchmarkWorker(QThread):
    """Worker thread for running GPU benchmarks"""
    
    progress_updated = pyqtSignal(int, str)
    benchmark_completed = pyqtSignal(dict)
    benchmark_failed = pyqtSignal(str)
    
    def __init__(self, benchmark_config: 'BenchmarkConfig'):
        super().__init__()
        self.benchmark_config = benchmark_config
        self.logger = logging.getLogger(__name__)
    
    def run(self):
        """Run the benchmark in background thread"""
        try:
            self.progress_updated.emit(10, "Initializing GPU benchmark suite...")
            
            if not HAS_GPU_MODULES:
                self.benchmark_failed.emit("GPU modules not available")
                return
            
            # Create benchmark suite
            benchmark_suite = GPUBenchmarkSuite(self.benchmark_config)
            
            self.progress_updated.emit(30, "Running hardware detection...")
            
            # Run comprehensive benchmark
            self.progress_updated.emit(50, "Running performance tests...")
            
            result = benchmark_suite.run_complete_benchmark()
            
            self.progress_updated.emit(90, "Analyzing results...")
            
            if result:
                self.progress_updated.emit(100, "Benchmark completed successfully")
                self.benchmark_completed.emit(result)
            else:
                self.benchmark_failed.emit("Benchmark returned empty results")
                
        except Exception as e:
            self.logger.error(f"Benchmark error: {e}")
            self.benchmark_failed.emit(f"Benchmark failed: {str(e)}")


class GPUDeviceTable(QTableWidget):
    """Table widget showing available GPU devices"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_table()
        self.populate_devices()
    
    def setup_table(self):
        """Setup the device table"""
        self.setColumnCount(6)
        self.setHorizontalHeaderLabels([
            "Device", "Backend", "Memory (MB)", "Status", "Temperature", "Utilization"
        ])
        
        # Set column widths
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
    
    def populate_devices(self):
        """Populate the table with GPU device information"""
        if not HAS_GPU_MODULES:
            self.setRowCount(1)
            self.setItem(0, 0, QTableWidgetItem("GPU modules not available"))
            for col in range(1, self.columnCount()):
                self.setItem(0, col, QTableWidgetItem("N/A"))
            return
        
        try:
            gpu_info = get_system_gpu_info()
            devices = gpu_info.get('devices', [])
            
            if not devices:
                self.setRowCount(1)
                self.setItem(0, 0, QTableWidgetItem("No GPU devices found"))
                self.setItem(0, 1, QTableWidgetItem("CPU fallback"))
                self.setItem(0, 2, QTableWidgetItem("N/A"))
                self.setItem(0, 3, QTableWidgetItem("Available"))
                self.setItem(0, 4, QTableWidgetItem("N/A"))
                self.setItem(0, 5, QTableWidgetItem("N/A"))
                return
            
            self.setRowCount(len(devices))
            
            for row, device in enumerate(devices):
                self.setItem(row, 0, QTableWidgetItem(device.get('name', 'Unknown')))
                self.setItem(row, 1, QTableWidgetItem(device.get('backend', 'Unknown')))
                self.setItem(row, 2, QTableWidgetItem(str(device.get('memory_total', 0))))
                
                status = "Available" if device.get('is_available', False) else "Unavailable"
                self.setItem(row, 3, QTableWidgetItem(status))
                
                # Temperature and utilization would come from monitoring
                self.setItem(row, 4, QTableWidgetItem("N/A"))
                self.setItem(row, 5, QTableWidgetItem("N/A"))
                
        except Exception as e:
            self.setRowCount(1)
            self.setItem(0, 0, QTableWidgetItem(f"Error: {str(e)}"))
            for col in range(1, self.columnCount()):
                self.setItem(0, col, QTableWidgetItem("Error"))


class GPUSettingsDialog(QDialog):
    """Advanced GPU settings and configuration dialog"""
    
    settings_applied = pyqtSignal(dict)
    
    def __init__(self, current_config: Dict[str, Any] = None, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.current_config = current_config or {}
        self.benchmark_worker = None
        
        self.setWindowTitle("GPU Settings & Configuration")
        self.setMinimumSize(700, 600)
        self.setup_ui()
        self.load_current_settings()
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # General Settings Tab
        self.setup_general_tab()
        
        # Performance Tab
        self.setup_performance_tab()
        
        # Hardware Info Tab
        self.setup_hardware_tab()
        
        # Benchmark Tab
        self.setup_benchmark_tab()
        
        layout.addWidget(self.tab_widget)
        
        # Dialog buttons
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Apply Settings")
        self.benchmark_button = QPushButton("Run Benchmark")
        self.reset_button = QPushButton("Reset to Defaults")
        self.cancel_button = QPushButton("Cancel")
        self.ok_button = QPushButton("OK")
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.benchmark_button)
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch()
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.ok_button)
        
        layout.addLayout(button_layout)
        
        # Connect signals
        self.apply_button.clicked.connect(self.apply_settings)
        self.benchmark_button.clicked.connect(self.run_benchmark)
        self.reset_button.clicked.connect(self.reset_to_defaults)
        self.cancel_button.clicked.connect(self.reject)
        self.ok_button.clicked.connect(self.accept_settings)
    
    def setup_general_tab(self):
        """Setup general GPU settings tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # GPU Backend Selection
        backend_group = QGroupBox("GPU Backend Configuration")
        backend_layout = QGridLayout(backend_group)
        
        backend_layout.addWidget(QLabel("Preferred Backend:"), 0, 0)
        self.backend_combo = QComboBox()
        self.backend_combo.addItems(["Auto", "CUDA", "OpenCL"])
        backend_layout.addWidget(self.backend_combo, 0, 1)
        
        backend_layout.addWidget(QLabel("Fallback to CPU:"), 1, 0)
        self.fallback_checkbox = QCheckBox("Enable CPU fallback when GPU fails")
        self.fallback_checkbox.setChecked(True)
        backend_layout.addWidget(self.fallback_checkbox, 1, 1)
        
        layout.addWidget(backend_group)
        
        # Memory Management
        memory_group = QGroupBox("Memory Management")
        memory_layout = QGridLayout(memory_group)
        
        memory_layout.addWidget(QLabel("GPU Memory Limit (MB):"), 0, 0)
        self.memory_limit_spin = QSpinBox()
        self.memory_limit_spin.setRange(256, 32768)
        self.memory_limit_spin.setValue(2048)
        self.memory_limit_spin.setSuffix(" MB")
        memory_layout.addWidget(self.memory_limit_spin, 0, 1)
        
        memory_layout.addWidget(QLabel("Memory Usage Mode:"), 1, 0)
        self.memory_mode_combo = QComboBox()
        self.memory_mode_combo.addItems(["Conservative", "Balanced", "Aggressive"])
        self.memory_mode_combo.setCurrentText("Balanced")
        memory_layout.addWidget(self.memory_mode_combo, 1, 1)
        
        memory_layout.addWidget(QLabel("Auto Memory Cleanup:"), 2, 0)
        self.auto_cleanup_checkbox = QCheckBox("Automatically cleanup GPU memory")
        self.auto_cleanup_checkbox.setChecked(True)
        memory_layout.addWidget(self.auto_cleanup_checkbox, 2, 1)
        
        layout.addWidget(memory_group)
        
        # Processing Options
        processing_group = QGroupBox("Processing Configuration")
        processing_layout = QGridLayout(processing_group)
        
        processing_layout.addWidget(QLabel("Batch Size:"), 0, 0)
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 100)
        self.batch_size_spin.setValue(10)
        processing_layout.addWidget(self.batch_size_spin, 0, 1)
        
        processing_layout.addWidget(QLabel("Max Concurrent Operations:"), 1, 0)
        self.max_concurrent_spin = QSpinBox()
        self.max_concurrent_spin.setRange(1, 16)
        self.max_concurrent_spin.setValue(4)
        processing_layout.addWidget(self.max_concurrent_spin, 1, 1)
        
        processing_layout.addWidget(QLabel("Enable GPU Monitoring:"), 2, 0)
        self.monitoring_checkbox = QCheckBox("Monitor GPU performance during operations")
        self.monitoring_checkbox.setChecked(True)
        processing_layout.addWidget(self.monitoring_checkbox, 2, 1)
        
        layout.addWidget(processing_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "General")
    
    def setup_performance_tab(self):
        """Setup performance optimization tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Performance Tuning
        perf_group = QGroupBox("Performance Optimization")
        perf_layout = QGridLayout(perf_group)
        
        perf_layout.addWidget(QLabel("Processing Priority:"), 0, 0)
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["Low", "Normal", "High", "Critical"])
        self.priority_combo.setCurrentText("Normal")
        perf_layout.addWidget(self.priority_combo, 0, 1)
        
        perf_layout.addWidget(QLabel("GPU Utilization Target (%):"), 1, 0)
        self.utilization_slider = QSlider(Qt.Horizontal)
        self.utilization_slider.setRange(10, 95)
        self.utilization_slider.setValue(80)
        self.utilization_label = QLabel("80%")
        
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.utilization_slider)
        slider_layout.addWidget(self.utilization_label)
        perf_layout.addLayout(slider_layout, 1, 1)
        
        self.utilization_slider.valueChanged.connect(
            lambda v: self.utilization_label.setText(f"{v}%")
        )
        
        perf_layout.addWidget(QLabel("Chunk Size (MB):"), 2, 0)
        self.chunk_size_spin = QDoubleSpinBox()
        self.chunk_size_spin.setRange(0.1, 100.0)
        self.chunk_size_spin.setValue(32.0)
        self.chunk_size_spin.setSuffix(" MB")
        self.chunk_size_spin.setDecimals(1)
        perf_layout.addWidget(self.chunk_size_spin, 2, 1)
        
        layout.addWidget(perf_group)
        
        # Advanced Options
        advanced_group = QGroupBox("Advanced Options")
        advanced_layout = QGridLayout(advanced_group)
        
        self.enable_profiling_checkbox = QCheckBox("Enable detailed performance profiling")
        advanced_layout.addWidget(self.enable_profiling_checkbox, 0, 0, 1, 2)
        
        self.use_memory_pool_checkbox = QCheckBox("Use GPU memory pooling")
        self.use_memory_pool_checkbox.setChecked(True)
        advanced_layout.addWidget(self.use_memory_pool_checkbox, 1, 0, 1, 2)
        
        self.optimize_for_throughput_checkbox = QCheckBox("Optimize for maximum throughput")
        advanced_layout.addWidget(self.optimize_for_throughput_checkbox, 2, 0, 1, 2)
        
        self.enable_async_processing_checkbox = QCheckBox("Enable asynchronous processing")
        self.enable_async_processing_checkbox.setChecked(True)
        advanced_layout.addWidget(self.enable_async_processing_checkbox, 3, 0, 1, 2)
        
        layout.addWidget(advanced_group)
        layout.addStretch()
        
        self.tab_widget.addTab(tab, "Performance")
    
    def setup_hardware_tab(self):
        """Setup hardware information tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # System Information
        sys_group = QGroupBox("System Information")
        sys_layout = QGridLayout(sys_group)
        
        if HAS_GPU_MODULES:
            try:
                gpu_info = get_system_gpu_info()
                
                sys_layout.addWidget(QLabel("Platform:"), 0, 0)
                sys_layout.addWidget(QLabel(gpu_info.get('platform', 'Unknown')), 0, 1)
                
                sys_layout.addWidget(QLabel("CUDA Available:"), 1, 0)
                cuda_available = "Yes" if gpu_info.get('cuda_available', False) else "No"
                sys_layout.addWidget(QLabel(cuda_available), 1, 1)
                
                sys_layout.addWidget(QLabel("OpenCL Available:"), 2, 0)
                opencl_available = "Yes" if gpu_info.get('opencl_available', False) else "No"
                sys_layout.addWidget(QLabel(opencl_available), 2, 1)
                
                sys_layout.addWidget(QLabel("GPU Libraries:"), 3, 0)
                libraries = gpu_info.get('libraries', {})
                lib_text = ", ".join([lib for lib, available in libraries.items() if available])
                if not lib_text:
                    lib_text = "None available"
                sys_layout.addWidget(QLabel(lib_text), 3, 1)
                
            except Exception as e:
                sys_layout.addWidget(QLabel("Error:"), 0, 0)
                sys_layout.addWidget(QLabel(str(e)), 0, 1)
        else:
            sys_layout.addWidget(QLabel("GPU modules not available"), 0, 0, 1, 2)
        
        layout.addWidget(sys_group)
        
        # GPU Devices Table
        devices_group = QGroupBox("Available GPU Devices")
        devices_layout = QVBoxLayout(devices_group)
        
        self.device_table = GPUDeviceTable()
        devices_layout.addWidget(self.device_table)
        
        # Refresh button
        refresh_button = QPushButton("Refresh Device List")
        refresh_button.clicked.connect(self.device_table.populate_devices)
        devices_layout.addWidget(refresh_button)
        
        layout.addWidget(devices_group)
        
        self.tab_widget.addTab(tab, "Hardware Info")
    
    def setup_benchmark_tab(self):
        """Setup benchmark tab"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Benchmark Options
        benchmark_group = QGroupBox("Benchmark Configuration")
        benchmark_layout = QGridLayout(benchmark_group)
        
        benchmark_layout.addWidget(QLabel("Benchmark Type:"), 0, 0)
        self.benchmark_type_combo = QComboBox()
        self.benchmark_type_combo.addItems(["Quick", "Comprehensive", "Custom"])
        benchmark_layout.addWidget(self.benchmark_type_combo, 0, 1)
        
        benchmark_layout.addWidget(QLabel("Iterations:"), 1, 0)
        self.iterations_spin = QSpinBox()
        self.iterations_spin.setRange(1, 10)
        self.iterations_spin.setValue(3)
        benchmark_layout.addWidget(self.iterations_spin, 1, 1)
        
        benchmark_layout.addWidget(QLabel("Timeout (seconds):"), 2, 0)
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(30, 600)
        self.timeout_spin.setValue(300)
        self.timeout_spin.setSuffix(" sec")
        benchmark_layout.addWidget(self.timeout_spin, 2, 1)
        
        layout.addWidget(benchmark_group)
        
        # Benchmark Progress
        progress_group = QGroupBox("Benchmark Progress")
        progress_layout = QVBoxLayout(progress_group)
        
        self.benchmark_progress = QProgressBar()
        self.benchmark_progress.setVisible(False)
        progress_layout.addWidget(self.benchmark_progress)
        
        self.benchmark_status_label = QLabel("Ready to run benchmark")
        progress_layout.addWidget(self.benchmark_status_label)
        
        layout.addWidget(progress_group)
        
        # Benchmark Results
        results_group = QGroupBox("Benchmark Results")
        results_layout = QVBoxLayout(results_group)
        
        self.benchmark_results = QTextEdit()
        self.benchmark_results.setReadOnly(True)
        self.benchmark_results.setFont(QFont("Courier", 9))
        self.benchmark_results.setPlainText("No benchmark results available. Click 'Run Benchmark' to start.")
        results_layout.addWidget(self.benchmark_results)
        
        # Export results button
        export_button = QPushButton("Export Results to JSON")
        export_button.clicked.connect(self.export_benchmark_results)
        export_button.setEnabled(False)
        self.export_results_button = export_button
        results_layout.addWidget(export_button)
        
        layout.addWidget(results_group)
        
        self.tab_widget.addTab(tab, "Benchmark")
    
    def load_current_settings(self):
        """Load current settings into the UI"""
        if not self.current_config:
            return
        
        # General settings
        self.backend_combo.setCurrentText(self.current_config.get('backend', 'Auto').title())
        self.fallback_checkbox.setChecked(self.current_config.get('fallback_to_cpu', True))
        self.memory_limit_spin.setValue(self.current_config.get('memory_limit_mb', 2048))
        self.batch_size_spin.setValue(self.current_config.get('batch_size', 10))
        self.max_concurrent_spin.setValue(self.current_config.get('max_concurrent', 4))
        self.monitoring_checkbox.setChecked(self.current_config.get('enable_monitoring', True))
        
        # Performance settings
        self.utilization_slider.setValue(self.current_config.get('utilization_target', 80))
        self.chunk_size_spin.setValue(self.current_config.get('chunk_size_mb', 32.0))
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current settings from the UI"""
        return {
            # General settings
            'enable_gpu': True,
            'backend': self.backend_combo.currentText().lower(),
            'fallback_to_cpu': self.fallback_checkbox.isChecked(),
            'memory_limit_mb': self.memory_limit_spin.value(),
            'memory_mode': self.memory_mode_combo.currentText().lower(),
            'auto_cleanup': self.auto_cleanup_checkbox.isChecked(),
            'batch_size': self.batch_size_spin.value(),
            'max_concurrent': self.max_concurrent_spin.value(),
            'enable_monitoring': self.monitoring_checkbox.isChecked(),
            
            # Performance settings
            'priority': self.priority_combo.currentText().lower(),
            'utilization_target': self.utilization_slider.value(),
            'chunk_size_mb': self.chunk_size_spin.value(),
            'enable_profiling': self.enable_profiling_checkbox.isChecked(),
            'use_memory_pool': self.use_memory_pool_checkbox.isChecked(),
            'optimize_for_throughput': self.optimize_for_throughput_checkbox.isChecked(),
            'enable_async': self.enable_async_processing_checkbox.isChecked(),
        }
    
    @pyqtSlot()
    def apply_settings(self):
        """Apply current settings"""
        settings = self.get_settings()
        self.settings_applied.emit(settings)
        
        QMessageBox.information(self, "Settings Applied", 
                              "GPU settings have been applied successfully.")
    
    @pyqtSlot()
    def accept_settings(self):
        """Accept settings and close dialog"""
        self.apply_settings()
        self.accept()
    
    @pyqtSlot()
    def reset_to_defaults(self):
        """Reset all settings to defaults"""
        reply = QMessageBox.question(self, "Reset Settings", 
                                   "Reset all GPU settings to defaults?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # Reset to default values
            self.backend_combo.setCurrentText("Auto")
            self.fallback_checkbox.setChecked(True)
            self.memory_limit_spin.setValue(2048)
            self.memory_mode_combo.setCurrentText("Balanced")
            self.auto_cleanup_checkbox.setChecked(True)
            self.batch_size_spin.setValue(10)
            self.max_concurrent_spin.setValue(4)
            self.monitoring_checkbox.setChecked(True)
            self.priority_combo.setCurrentText("Normal")
            self.utilization_slider.setValue(80)
            self.chunk_size_spin.setValue(32.0)
            self.enable_profiling_checkbox.setChecked(False)
            self.use_memory_pool_checkbox.setChecked(True)
            self.optimize_for_throughput_checkbox.setChecked(False)
            self.enable_async_processing_checkbox.setChecked(True)
    
    @pyqtSlot()
    def run_benchmark(self):
        """Run GPU benchmark"""
        if self.benchmark_worker and self.benchmark_worker.isRunning():
            QMessageBox.warning(self, "Benchmark Running", 
                              "A benchmark is already running. Please wait for it to complete.")
            return
        
        # Create benchmark config
        benchmark_type = self.benchmark_type_combo.currentText().lower()
        config = BenchmarkConfig(
            quick=(benchmark_type == "quick"),
            full=(benchmark_type == "comprehensive"),
            iterations=self.iterations_spin.value(),
            timeout_seconds=self.timeout_spin.value()
        )
        
        # Start benchmark
        self.benchmark_worker = BenchmarkWorker(config)
        self.benchmark_worker.progress_updated.connect(self.on_benchmark_progress)
        self.benchmark_worker.benchmark_completed.connect(self.on_benchmark_completed)
        self.benchmark_worker.benchmark_failed.connect(self.on_benchmark_failed)
        
        self.benchmark_progress.setVisible(True)
        self.benchmark_progress.setValue(0)
        self.benchmark_button.setEnabled(False)
        self.benchmark_results.setPlainText("Running benchmark...\n")
        
        self.benchmark_worker.start()
    
    @pyqtSlot(int, str)
    def on_benchmark_progress(self, percent: int, message: str):
        """Handle benchmark progress updates"""
        self.benchmark_progress.setValue(percent)
        self.benchmark_status_label.setText(message)
    
    @pyqtSlot(dict)
    def on_benchmark_completed(self, results: Dict[str, Any]):
        """Handle benchmark completion"""
        self.benchmark_progress.setVisible(False)
        self.benchmark_button.setEnabled(True)
        self.export_results_button.setEnabled(True)
        self.benchmark_status_label.setText("Benchmark completed successfully")
        
        # Format and display results
        formatted_results = self.format_benchmark_results(results)
        self.benchmark_results.setPlainText(formatted_results)
        
        # Store results for export
        self.last_benchmark_results = results
    
    @pyqtSlot(str)
    def on_benchmark_failed(self, error: str):
        """Handle benchmark failure"""
        self.benchmark_progress.setVisible(False)
        self.benchmark_button.setEnabled(True)
        self.benchmark_status_label.setText("Benchmark failed")
        
        self.benchmark_results.setPlainText(f"Benchmark failed with error:\n{error}")
        
        QMessageBox.warning(self, "Benchmark Failed", 
                          f"The benchmark failed to complete:\n\n{error}")
    
    def format_benchmark_results(self, results: Dict[str, Any]) -> str:
        """Format benchmark results for display"""
        if not results:
            return "No benchmark results available."
        
        output = []
        output.append("GPU BENCHMARK RESULTS")
        output.append("=" * 50)
        output.append("")
        
        # System information
        if 'system_info' in results:
            sys_info = results['system_info']
            output.append("SYSTEM INFORMATION:")
            output.append(f"  Platform: {sys_info.get('platform', 'Unknown')}")
            output.append(f"  CPU Cores: {sys_info.get('cpu_count', 'Unknown')}")
            output.append(f"  Memory: {sys_info.get('total_memory_gb', 'Unknown')} GB")
            output.append("")
        
        # Benchmark info
        if 'benchmark_info' in results:
            bench_info = results['benchmark_info']
            output.append("BENCHMARK CONFIGURATION:")
            output.append(f"  Duration: {bench_info.get('total_duration', 0):.2f} seconds")
            output.append(f"  Timestamp: {bench_info.get('timestamp', 'Unknown')}")
            output.append("")
        
        # Results summary
        if 'summary' in results:
            summary = results['summary']
            output.append("PERFORMANCE SUMMARY:")
            output.append(f"  Overall Score: {summary.get('overall_score', 0):.1f}")
            output.append(f"  GPU Acceleration: {'Available' if summary.get('gpu_available') else 'Not Available'}")
            if 'average_speedup' in summary:
                output.append(f"  Average Speedup: {summary['average_speedup']:.2f}x")
            output.append("")
        
        # Detailed results
        if 'results' in results and results['results']:
            output.append("DETAILED RESULTS:")
            for category, result in results['results'].items():
                if isinstance(result, dict):
                    output.append(f"  {category.title()}:")
                    for key, value in result.items():
                        if isinstance(value, (int, float)):
                            output.append(f"    {key}: {value:.2f}")
                        else:
                            output.append(f"    {key}: {value}")
                    output.append("")
        
        return "\n".join(output)
    
    @pyqtSlot()
    def export_benchmark_results(self):
        """Export benchmark results to JSON file"""
        if not hasattr(self, 'last_benchmark_results'):
            QMessageBox.warning(self, "No Results", "No benchmark results to export.")
            return
        
        from PyQt5.QtWidgets import QFileDialog
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Benchmark Results", 
            f"gpu_benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON files (*.json)"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.last_benchmark_results, f, indent=2, default=str)
                
                QMessageBox.information(self, "Export Successful", 
                                      f"Benchmark results exported to:\n{filename}")
            except Exception as e:
                QMessageBox.warning(self, "Export Failed", 
                                  f"Failed to export results:\n{str(e)}")


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Sample current config
    current_config = {
        'backend': 'auto',
        'memory_limit_mb': 2048,
        'batch_size': 10,
        'enable_monitoring': True
    }
    
    dialog = GPUSettingsDialog(current_config)
    dialog.show()
    
    sys.exit(app.exec_())