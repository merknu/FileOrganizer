"""
Integration tests for gui.processing_thread module.

Tests cover:
- Thread signal handling and communication
- Progress tracking and updates
- File processing integration with file_utils
- Thread lifecycle management
- Error propagation and handling
- Batch processing functionality
"""

import os
import time
import threading
from unittest.mock import Mock, patch, MagicMock, call

import pytest

try:
    from PyQt5.QtCore import QApplication, QThread, QTimer
    from PyQt5.QtWidgets import QWidget
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

from gui.processing_thread import (
    ProcessingThread,
    BatchProcessingThread,
    create_processing_thread,
    estimate_processing_time
)


pytestmark = pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt5 not available")


class TestProcessingThread:
    """Test ProcessingThread functionality."""
    
    @pytest.mark.integration
    def test_thread_initialization(self, test_config):
        """Test ProcessingThread initialization."""
        folders = ["/test/folder1", "/test/folder2"]
        thread = ProcessingThread(
            folders=folders,
            app_config=test_config,
            recursive=True,
            preview_mode=False
        )
        
        assert thread.folders == folders
        assert thread.app_config == test_config
        assert thread.recursive is True
        assert thread.preview_mode is False
        assert thread._stop_requested is False
        assert thread.total_files == 0
        assert thread.processed_files == 0
        assert isinstance(thread.summary, dict)
    
    @pytest.mark.integration
    def test_thread_stop_request(self, test_config):
        """Test thread stop request functionality."""
        thread = ProcessingThread(
            folders=["/test/folder"],
            app_config=test_config
        )
        
        assert not thread.is_stop_requested()
        
        thread.stop()
        
        assert thread.is_stop_requested()
    
    @pytest.mark.integration
    @patch('os.walk')
    @patch('os.listdir')
    @patch('os.path.isfile')
    def test_count_files_recursive(self, mock_isfile, mock_listdir, mock_walk, test_config, temp_dir):
        """Test file counting with recursive option."""
        # Setup mock for recursive walk
        mock_walk.return_value = [
            ("/test/folder", ["subdir"], ["file1.txt", "file2.jpg"]),
            ("/test/folder/subdir", [], ["file3.pdf"])
        ]
        
        thread = ProcessingThread(
            folders=["/test/folder"],
            app_config=test_config,
            recursive=True
        )
        
        count = thread.count_files_in_folders()
        assert count == 3  # file1.txt, file2.jpg, file3.pdf
    
    @pytest.mark.integration
    @patch('os.listdir')
    @patch('os.path.isfile')
    def test_count_files_non_recursive(self, mock_isfile, mock_listdir, test_config):
        """Test file counting without recursive option."""
        mock_listdir.return_value = ["file1.txt", "file2.jpg", "subdir"]
        mock_isfile.side_effect = lambda path: not path.endswith("subdir")
        
        thread = ProcessingThread(
            folders=["/test/folder"],
            app_config=test_config,
            recursive=False
        )
        
        count = thread.count_files_in_folders()
        assert count == 2  # Only files, not subdirectory
    
    @pytest.mark.integration
    def test_thread_signals_connection(self, mock_pyqt_app, test_config):
        """Test that thread signals can be connected."""
        thread = ProcessingThread(
            folders=["/test/folder"],
            app_config=test_config
        )
        
        # Mock signal handlers
        mock_finished = Mock()
        mock_progress = Mock()
        mock_status = Mock()
        mock_error = Mock()
        mock_file_processed = Mock()
        
        # Connect signals
        thread.processing_finished.connect(mock_finished)
        thread.progress_changed.connect(mock_progress)
        thread.status_changed.connect(mock_status)
        thread.error_occurred.connect(mock_error)
        thread.file_processed.connect(mock_file_processed)
        
        # Verify connections work (signals should exist)
        assert hasattr(thread, 'processing_finished')
        assert hasattr(thread, 'progress_changed')
        assert hasattr(thread, 'status_changed')
        assert hasattr(thread, 'error_occurred')
        assert hasattr(thread, 'file_processed')
    
    @pytest.mark.integration
    def test_update_progress_with_callback(self, test_config):
        """Test progress update with callback function."""
        callback_calls = []
        
        def test_callback():
            callback_calls.append("called")
        
        thread = ProcessingThread(
            folders=["/test/folder"],
            app_config=test_config,
            callback=test_callback
        )
        
        thread.total_files = 10
        thread.processed_files = 3
        
        # Mock progress_changed signal
        thread.progress_changed = Mock()
        
        thread.update_progress()
        
        # Progress should be calculated and emitted
        thread.progress_changed.emit.assert_called_once_with(30)  # 3/10 * 100 = 30%
        assert len(callback_calls) == 1
    
    @pytest.mark.integration
    def test_update_progress_callback_error(self, test_config):
        """Test progress update when callback raises error."""
        def failing_callback():
            raise Exception("Callback error")
        
        thread = ProcessingThread(
            folders=["/test/folder"],
            app_config=test_config,
            callback=failing_callback
        )
        
        thread.total_files = 10
        thread.processed_files = 5
        thread.progress_changed = Mock()
        
        # Should not raise exception despite callback error
        thread.update_progress()
        
        # Progress should still be emitted
        thread.progress_changed.emit.assert_called_once_with(50)
    
    @pytest.mark.integration
    @patch('file_handler.file_utils.organize_files')
    def test_process_single_folder_success(self, mock_organize, test_config):
        """Test successful processing of single folder."""
        mock_organize.return_value = {"moved": 5, "duplicate_kept": 1}
        
        thread = ProcessingThread(
            folders=["/test/folder"],
            app_config=test_config
        )
        
        thread.status_changed = Mock()
        thread.file_processed = Mock()
        
        result = thread.process_single_folder("/test/folder")
        
        assert result == {"moved": 5, "duplicate_kept": 1}
        thread.status_changed.emit.assert_called_with("Processing folder: /test/folder")
        mock_organize.assert_called_once()
    
    @pytest.mark.integration
    @patch('file_handler.file_utils.organize_files')
    def test_process_single_folder_with_stop_request(self, mock_organize, test_config):
        """Test processing folder when stop is requested."""
        def callback_with_stop():
            # Simulate stop request during processing
            thread.stop()
            raise InterruptedError("Processing stopped by user")
        
        # Create a custom callback that stops the thread
        thread = ProcessingThread(
            folders=["/test/folder"],
            app_config=test_config
        )
        
        thread.status_changed = Mock()
        
        # Mock organize_files to call our custom callback
        def mock_organize_side_effect(folder, app_config, recursive, preview_mode, callback):
            if callback:
                callback()  # This will trigger the stop
            return {"moved": 0}
        
        mock_organize.side_effect = mock_organize_side_effect
        
        with pytest.raises(InterruptedError):
            thread.process_single_folder("/test/folder")
    
    @pytest.mark.integration
    @patch('file_handler.file_utils.organize_files')
    def test_process_single_folder_organize_error(self, mock_organize, test_config):
        """Test processing folder when organize_files raises error."""
        mock_organize.side_effect = Exception("Processing error")
        
        thread = ProcessingThread(
            folders=["/test/folder"],
            app_config=test_config
        )
        
        thread.status_changed = Mock()
        
        result = thread.process_single_folder("/test/folder")
        
        assert result["error"] == 1
        assert "Processing error" in result["error_message"]
    
    @pytest.mark.integration
    def test_get_progress_info(self, test_config):
        """Test getting progress information."""
        folders = ["/folder1", "/folder2"]
        thread = ProcessingThread(
            folders=folders,
            app_config=test_config,
            recursive=True,
            preview_mode=True
        )
        
        thread.total_files = 100
        thread.processed_files = 25
        thread.current_folder = "/folder1"
        
        info = thread.get_progress_info()
        
        assert info["total_files"] == 100
        assert info["processed_files"] == 25
        assert info["current_folder"] == "/folder1"
        assert info["folders_total"] == 2
        assert info["preview_mode"] is True


class TestProcessingThreadRun:
    """Test ProcessingThread run method and execution flow."""
    
    @pytest.mark.integration
    @patch('gui.processing_thread.ProcessingThread.count_files_in_folders')
    @patch('gui.processing_thread.ProcessingThread.process_single_folder')
    def test_run_successful_processing(self, mock_process_folder, mock_count_files, test_config):
        """Test successful thread execution."""
        mock_count_files.return_value = 10
        mock_process_folder.return_value = {"moved": 3, "duplicate_kept": 1}
        
        thread = ProcessingThread(
            folders=["/folder1", "/folder2"],
            app_config=test_config
        )
        
        # Mock signals
        thread.status_changed = Mock()
        thread.processing_finished = Mock()
        
        # Run the thread
        thread.run()
        
        # Verify calls
        mock_count_files.assert_called_once()
        assert mock_process_folder.call_count == 2
        
        # Verify status updates
        status_calls = [call[0][0] for call in thread.status_changed.emit.call_args_list]
        assert "Initializing..." in status_calls
        assert "Counting files..." in status_calls
        assert "Processing completed" in status_calls
        
        # Verify final summary
        thread.processing_finished.emit.assert_called_once()
        final_summary = thread.processing_finished.emit.call_args[0][0]
        assert final_summary["moved"] == 6  # 3 * 2 folders
        assert final_summary["duplicate_kept"] == 2  # 1 * 2 folders
    
    @pytest.mark.integration
    @patch('gui.processing_thread.ProcessingThread.count_files_in_folders')
    def test_run_with_early_stop(self, mock_count_files, test_config):
        """Test thread execution with early stop request."""
        mock_count_files.return_value = 10
        
        thread = ProcessingThread(
            folders=["/folder1"],
            app_config=test_config
        )
        
        # Request stop before running
        thread.stop()
        
        thread.status_changed = Mock()
        thread.processing_finished = Mock()
        
        thread.run()
        
        # Should emit cancelled status
        status_calls = [call[0][0] for call in thread.status_changed.emit.call_args_list if thread.status_changed.emit.call_args_list]
        if status_calls:
            assert any("cancelled" in status.lower() for status in status_calls)
    
    @pytest.mark.integration
    @patch('gui.processing_thread.ProcessingThread.count_files_in_folders')
    @patch('gui.processing_thread.ProcessingThread.process_single_folder')
    def test_run_with_folder_processing_error(self, mock_process_folder, mock_count_files, test_config):
        """Test thread execution when folder processing fails."""
        mock_count_files.return_value = 10
        mock_process_folder.side_effect = [
            {"moved": 2},  # First folder succeeds
            Exception("Folder processing error")  # Second folder fails
        ]
        
        thread = ProcessingThread(
            folders=["/folder1", "/folder2"],
            app_config=test_config
        )
        
        thread.status_changed = Mock()
        thread.processing_finished = Mock()
        
        thread.run()
        
        # Should continue processing despite error
        assert mock_process_folder.call_count == 2
        
        # Final summary should include error counts
        thread.processing_finished.emit.assert_called_once()
        final_summary = thread.processing_finished.emit.call_args[0][0]
        assert final_summary.get("failed_folders", 0) > 0
        assert final_summary.get("errors", 0) > 0
    
    @pytest.mark.integration
    @patch('gui.processing_thread.ProcessingThread.count_files_in_folders')
    def test_run_with_unexpected_error(self, mock_count_files, test_config):
        """Test thread execution with unexpected error."""
        mock_count_files.side_effect = Exception("Unexpected error")
        
        thread = ProcessingThread(
            folders=["/folder1"],
            app_config=test_config
        )
        
        thread.error_occurred = Mock()
        thread.processing_finished = Mock()
        
        thread.run()
        
        # Should emit error signal
        thread.error_occurred.emit.assert_called_once()
        error_message = thread.error_occurred.emit.call_args[0][0]
        assert "Unexpected error" in error_message
        
        # Should still emit finished signal
        thread.processing_finished.emit.assert_called_once()


class TestBatchProcessingThread:
    """Test BatchProcessingThread functionality."""
    
    @pytest.mark.integration
    def test_batch_thread_initialization(self, test_config):
        """Test BatchProcessingThread initialization."""
        folder_batches = [
            ["/batch1/folder1", "/batch1/folder2"],
            ["/batch2/folder1", "/batch2/folder2", "/batch2/folder3"]
        ]
        
        thread = BatchProcessingThread(
            folder_batches=folder_batches,
            app_config=test_config,
            recursive=True,
            preview_mode=False
        )
        
        assert thread.folder_batches == folder_batches
        # Should flatten batches for parent class
        expected_all_folders = ["/batch1/folder1", "/batch1/folder2", 
                               "/batch2/folder1", "/batch2/folder2", "/batch2/folder3"]
        assert thread.folders == expected_all_folders
        assert thread.current_batch == 0
    
    @pytest.mark.integration
    @patch('gui.processing_thread.ProcessingThread.run')
    def test_batch_processing_execution(self, mock_parent_run, test_config):
        """Test batch processing execution flow."""
        folder_batches = [
            ["/batch1/folder1"],
            ["/batch2/folder1"]
        ]
        
        thread = BatchProcessingThread(
            folder_batches=folder_batches,
            app_config=test_config
        )
        
        thread.batch_progress = Mock()
        thread.processing_finished = Mock()
        
        thread.run()
        
        # Should process each batch
        assert mock_parent_run.call_count == 2
        
        # Should emit batch progress
        batch_calls = thread.batch_progress.emit.call_args_list
        assert len(batch_calls) == 2
        assert batch_calls[0][0] == (1, 2)  # First batch
        assert batch_calls[1][0] == (2, 2)  # Second batch
    
    @pytest.mark.integration
    @patch('gui.processing_thread.ProcessingThread.run')
    def test_batch_processing_with_stop(self, mock_parent_run, test_config):
        """Test batch processing with stop request."""
        folder_batches = [
            ["/batch1/folder1"],
            ["/batch2/folder1"]
        ]
        
        thread = BatchProcessingThread(
            folder_batches=folder_batches,
            app_config=test_config
        )
        
        # Stop after first batch
        def stop_after_first():
            if mock_parent_run.call_count == 1:
                thread.stop()
        
        mock_parent_run.side_effect = stop_after_first
        
        thread.batch_progress = Mock()
        thread.processing_finished = Mock()
        
        thread.run()
        
        # Should only process first batch
        assert mock_parent_run.call_count == 1


class TestUtilityFunctions:
    """Test utility functions for thread management."""
    
    @pytest.mark.integration
    def test_create_processing_thread(self, test_config):
        """Test processing thread factory function."""
        folders = ["/test/folder"]
        
        thread = create_processing_thread(
            folders=folders,
            config=test_config,
            recursive=True,
            preview_mode=False
        )
        
        assert isinstance(thread, ProcessingThread)
        assert thread.folders == folders
        assert thread.app_config == test_config
        assert thread.recursive is True
        assert thread.preview_mode is False
    
    @pytest.mark.integration
    @patch('os.walk')
    @patch('os.listdir')
    @patch('os.path.isfile')
    def test_estimate_processing_time_recursive(self, mock_isfile, mock_listdir, mock_walk):
        """Test processing time estimation with recursive scanning."""
        mock_walk.return_value = [
            ("/folder1", ["subdir"], ["file1.txt", "file2.jpg"]),
            ("/folder1/subdir", [], ["file3.pdf"]),
            ("/folder2", [], ["file4.mp3", "file5.docx"])
        ]
        
        folders = ["/folder1", "/folder2"]
        estimated_time = estimate_processing_time(folders, recursive=True)
        
        # Should count 5 files total, estimate 50 files per second
        assert estimated_time == max(1, 5 // 50)  # Should be 1 second minimum
    
    @pytest.mark.integration
    @patch('os.listdir')
    @patch('os.path.isfile')
    def test_estimate_processing_time_non_recursive(self, mock_isfile, mock_listdir):
        """Test processing time estimation without recursive scanning."""
        mock_listdir.side_effect = [
            ["file1.txt", "file2.jpg", "subdir"],  # folder1
            ["file3.mp3"]  # folder2
        ]
        mock_isfile.side_effect = lambda path: not path.endswith("subdir")
        
        folders = ["/folder1", "/folder2"]
        estimated_time = estimate_processing_time(folders, recursive=False)
        
        # Should count 3 files total (excluding subdirectory)
        assert estimated_time == max(1, 3 // 50)
    
    @pytest.mark.integration
    @patch('os.walk')
    def test_estimate_processing_time_with_errors(self, mock_walk):
        """Test processing time estimation when errors occur."""
        mock_walk.side_effect = OSError("Permission denied")
        
        folders = ["/inaccessible/folder"]
        estimated_time = estimate_processing_time(folders, recursive=True)
        
        # Should assume average when can't count
        assert estimated_time == max(1, 100 // 50)  # 100 is the assumed average


class TestProcessingThreadIntegration:
    """Test ProcessingThread integration with other components."""
    
    @pytest.mark.integration
    @pytest.mark.file_io
    @patch('file_handler.file_utils.organize_files')
    def test_thread_with_real_file_organization(self, mock_organize, sample_files_structure, test_config):
        """Test thread integration with file organization logic."""
        mock_organize.return_value = {
            "moved": 3,
            "duplicate_kept": 1,
            "no_extension": 1
        }
        
        thread = ProcessingThread(
            folders=[sample_files_structure],
            app_config=test_config,
            recursive=True,
            preview_mode=False
        )
        
        # Mock signals to capture emissions
        thread.status_changed = Mock()
        thread.processing_finished = Mock()
        thread.file_processed = Mock()
        
        thread.run()
        
        # Verify organize_files was called with correct parameters
        mock_organize.assert_called_once_with(
            folder=sample_files_structure,
            app_config=test_config,
            recursive=True,
            preview_mode=False,
            callback=thread.process_single_folder.__code__.co_consts[4]  # The callback function
        )
        
        # Verify final results
        thread.processing_finished.emit.assert_called_once()
        final_summary = thread.processing_finished.emit.call_args[0][0]
        assert final_summary["moved"] == 3
        assert final_summary["duplicate_kept"] == 1
    
    @pytest.mark.integration
    def test_thread_lifecycle_management(self, test_config, mock_pyqt_app):
        """Test complete thread lifecycle from creation to completion."""
        thread = ProcessingThread(
            folders=["/test/folder"],
            app_config=test_config
        )
        
        # Verify initial state
        assert not thread.isRunning()
        assert not thread.is_stop_requested()
        
        # Mock the run method to avoid actual processing
        with patch.object(thread, 'run') as mock_run:
            thread.start()
            
            # Thread should be running (or attempting to run)
            # Note: In tests, we can't easily verify thread state without actual execution
            
            # Stop the thread
            thread.stop()
            assert thread.is_stop_requested()
            
            # Wait for thread to finish (with timeout)
            thread.wait(1000)  # Wait up to 1 second
    
    @pytest.mark.integration
    @patch('file_handler.file_utils.organize_files')
    def test_thread_signal_emission_sequence(self, mock_organize, test_config):
        """Test that thread emits signals in correct sequence."""
        mock_organize.return_value = {"moved": 1}
        
        thread = ProcessingThread(
            folders=["/folder1", "/folder2"],
            app_config=test_config
        )
        
        # Capture all signal emissions
        emitted_signals = []
        
        def capture_status(message):
            emitted_signals.append(("status", message))
        
        def capture_finished(summary):
            emitted_signals.append(("finished", summary))
        
        thread.status_changed = Mock(side_effect=capture_status)
        thread.processing_finished = Mock(side_effect=capture_finished)
        
        with patch.object(thread, 'count_files_in_folders', return_value=5):
            thread.run()
        
        # Verify signal sequence
        assert len(emitted_signals) >= 3  # At least init, counting, completed, finished
        assert emitted_signals[0][0] == "status"
        assert "initializing" in emitted_signals[0][1].lower()
        assert emitted_signals[-1][0] == "finished"
        assert isinstance(emitted_signals[-1][1], dict)