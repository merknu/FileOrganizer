"""
GUI tests for gui.main_window module.

Tests cover:
- Main window initialization and UI components
- Button interactions and state management
- File selection and drag/drop functionality
- Progress tracking and status updates
- Error handling and user notifications
- Threading integration with GUI
"""

import os
import time
from unittest.mock import Mock, patch, MagicMock, call

import pytest

try:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog
    from PyQt5.QtCore import Qt, QMimeData, QUrl, QPoint
    from PyQt5.QtGui import QDragEnterEvent, QDropEvent
    from PyQt5.QtTest import QTest
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False

if PYQT_AVAILABLE:
    from gui.main_window import FileOrganizerMainWindow

pytestmark = pytest.mark.skipif(not PYQT_AVAILABLE, reason="PyQt5 not available")


class TestMainWindowInitialization:
    """Test main window initialization and UI setup."""
    
    @pytest.mark.gui
    def test_main_window_creation(self, mock_pyqt_app, test_config):
        """Test successful main window creation."""
        window = FileOrganizerMainWindow(test_config)
        
        assert window.app_config == test_config
        assert window.selected_folders == []
        assert window.is_processing is False
        assert window.processed_files_count == 0
        assert window.total_files_count == 0
        assert window.processing_thread is None
    
    @pytest.mark.gui
    def test_ui_component_initialization(self, mock_pyqt_app, test_config):
        """Test that all critical UI components are initialized."""
        window = FileOrganizerMainWindow(test_config)
        
        # Check critical buttons exist
        assert window.select_folders_button is not None
        assert window.start_processing_button is not None
        assert window.preview_button is not None
        assert window.stop_button is not None
        
        # Check text displays exist
        assert window.before_text_edit is not None
        assert window.after_text_edit is not None
        assert window.preview_text_edit is not None
        
        # Check status components
        assert window.status_label is not None
        assert window.progress_bar is not None
        
        # Check options
        assert window.recursive_checkbox is not None
        assert window.auto_confirm_checkbox is not None
    
    @pytest.mark.gui
    def test_window_properties(self, mock_pyqt_app, test_config):
        """Test window properties and settings."""
        window = FileOrganizerMainWindow(test_config)
        
        assert window.windowTitle() == 'File Organizer - Enhanced'
        assert window.minimumSize().width() == 1000
        assert window.minimumSize().height() == 700
    
    @pytest.mark.gui
    def test_initial_button_states(self, mock_pyqt_app, test_config):
        """Test initial button enabled/disabled states."""
        window = FileOrganizerMainWindow(test_config)
        
        # No folders selected initially
        assert not window.preview_button.isEnabled()
        assert not window.start_processing_button.isEnabled()
        assert not window.stop_button.isEnabled()
        assert window.select_folders_button.isEnabled()
    
    @pytest.mark.gui
    def test_ui_validation_error_handling(self, mock_pyqt_app, test_config):
        """Test UI validation when components are missing."""
        # Mock a missing component scenario
        with patch('gui.main_window.QPushButton', side_effect=[None, Mock(), Mock(), Mock()]):
            # This should trigger validation errors
            window = FileOrganizerMainWindow(test_config)
            # Window should still be created but validation should log errors


class TestFolderSelection:
    """Test folder selection functionality."""
    
    @pytest.mark.gui
    @patch('PyQt5.QtWidgets.QFileDialog')
    def test_select_folders_success(self, mock_dialog_class, mock_pyqt_app, test_config):
        """Test successful folder selection."""
        # Setup mock dialog
        mock_dialog = Mock()
        mock_dialog.exec_.return_value = True
        mock_dialog.selectedFiles.return_value = ["/test/folder1", "/test/folder2"]
        mock_dialog_class.return_value = mock_dialog
        
        window = FileOrganizerMainWindow(test_config)
        
        # Mock update_before_structure to avoid file system access
        with patch.object(window, 'update_before_structure'):
            window.on_select_folders_button_clicked()
        
        assert window.selected_folders == ["/test/folder1", "/test/folder2"]
        assert "folder1, folder2" in window.status_label.text()
        assert window.preview_button.isEnabled()
        assert window.start_processing_button.isEnabled()
    
    @pytest.mark.gui
    @patch('PyQt5.QtWidgets.QFileDialog')
    def test_select_folders_cancelled(self, mock_dialog_class, mock_pyqt_app, test_config):
        """Test folder selection when user cancels."""
        mock_dialog = Mock()
        mock_dialog.exec_.return_value = False  # User cancelled
        mock_dialog_class.return_value = mock_dialog
        
        window = FileOrganizerMainWindow(test_config)
        window.on_select_folders_button_clicked()
        
        assert window.selected_folders == []
        assert not window.preview_button.isEnabled()
        assert not window.start_processing_button.isEnabled()
    
    @pytest.mark.gui
    @patch('PyQt5.QtWidgets.QFileDialog')
    def test_select_folders_no_selection(self, mock_dialog_class, mock_pyqt_app, test_config):
        """Test folder selection when no folders are selected."""
        mock_dialog = Mock()
        mock_dialog.exec_.return_value = True
        mock_dialog.selectedFiles.return_value = []  # No selection
        mock_dialog_class.return_value = mock_dialog
        
        window = FileOrganizerMainWindow(test_config)
        window.on_select_folders_button_clicked()
        
        assert window.selected_folders == []
        assert "No folders selected" in window.status_label.text()
    
    @pytest.mark.gui
    @patch('PyQt5.QtWidgets.QFileDialog')
    def test_select_folders_error_handling(self, mock_dialog_class, mock_pyqt_app, test_config):
        """Test folder selection error handling."""
        mock_dialog_class.side_effect = Exception("Dialog error")
        
        window = FileOrganizerMainWindow(test_config)
        
        # Should handle exception gracefully
        with patch.object(window, 'show_error_message') as mock_show_error:
            window.on_select_folders_button_clicked()
            mock_show_error.assert_called_once()


class TestDragAndDrop:
    """Test drag and drop functionality."""
    
    @pytest.mark.gui
    def test_drag_enter_with_urls(self, mock_pyqt_app, test_config):
        """Test drag enter event with URLs."""
        window = FileOrganizerMainWindow(test_config)
        
        # Create mock drag event with URLs
        mime_data = Mock()
        mime_data.hasUrls.return_value = True
        
        event = Mock()
        event.mimeData.return_value = mime_data
        event.acceptProposedAction = Mock()
        
        window.dragEnterEvent(event)
        
        event.acceptProposedAction.assert_called_once()
    
    @pytest.mark.gui
    def test_drag_enter_without_urls(self, mock_pyqt_app, test_config):
        """Test drag enter event without URLs."""
        window = FileOrganizerMainWindow(test_config)
        
        mime_data = Mock()
        mime_data.hasUrls.return_value = False
        
        event = Mock()
        event.mimeData.return_value = mime_data
        event.ignore = Mock()
        
        window.dragEnterEvent(event)
        
        event.ignore.assert_called_once()
    
    @pytest.mark.gui
    @patch('os.path.isdir')
    def test_drop_event_with_folders(self, mock_isdir, mock_pyqt_app, test_config):
        """Test drop event with valid folders."""
        mock_isdir.return_value = True
        
        window = FileOrganizerMainWindow(test_config)
        
        # Create mock drop event
        url1 = Mock()
        url1.toLocalFile.return_value = "/test/folder1"
        url2 = Mock()
        url2.toLocalFile.return_value = "/test/folder2"
        
        mime_data = Mock()
        mime_data.urls.return_value = [url1, url2]
        
        event = Mock()
        event.mimeData.return_value = mime_data
        event.acceptProposedAction = Mock()
        
        with patch.object(window, 'update_before_structure'), \
             patch.object(window, 'status_update') as mock_status:
            window.dropEvent(event)
        
        assert window.selected_folders == ["/test/folder1", "/test/folder2"]
        event.acceptProposedAction.assert_called_once()
        mock_status.emit.assert_called_once()
    
    @pytest.mark.gui
    @patch('os.path.isdir')
    def test_drop_event_with_files(self, mock_isdir, mock_pyqt_app, test_config):
        """Test drop event with files (should be rejected)."""
        mock_isdir.return_value = False  # Not directories
        
        window = FileOrganizerMainWindow(test_config)
        
        url = Mock()
        url.toLocalFile.return_value = "/test/file.txt"
        
        mime_data = Mock()
        mime_data.urls.return_value = [url]
        
        event = Mock()
        event.mimeData.return_value = mime_data
        event.ignore = Mock()
        
        with patch.object(window, 'show_warning_message') as mock_warning:
            window.dropEvent(event)
        
        event.ignore.assert_called_once()
        mock_warning.assert_called_once()
    
    @pytest.mark.gui
    def test_drop_event_error_handling(self, mock_pyqt_app, test_config):
        """Test drop event error handling."""
        window = FileOrganizerMainWindow(test_config)
        
        # Create event that will cause an error
        event = Mock()
        event.mimeData.side_effect = Exception("Drop error")
        event.ignore = Mock()
        
        window.dropEvent(event)
        
        event.ignore.assert_called_once()


class TestProcessingOperations:
    """Test file processing operations."""
    
    @pytest.mark.gui
    def test_preview_button_clicked_success(self, mock_pyqt_app, test_config, mock_processing_thread):
        """Test successful preview operation."""
        window = FileOrganizerMainWindow(test_config)
        window.selected_folders = ["/test/folder"]
        
        with patch('gui.main_window.ProcessingThread', return_value=mock_processing_thread):
            window.on_preview_button_clicked()
        
        assert window.is_processing is True
        assert window.progress_bar.isVisible()
        mock_processing_thread.start.assert_called_once()
    
    @pytest.mark.gui
    def test_preview_button_clicked_no_folders(self, mock_pyqt_app, test_config):
        """Test preview button clicked with no folders selected."""
        window = FileOrganizerMainWindow(test_config)
        window.selected_folders = []
        
        with patch.object(window, 'show_warning_message') as mock_warning:
            window.on_preview_button_clicked()
        
        mock_warning.assert_called_once()
        assert window.is_processing is False
    
    @pytest.mark.gui
    def test_preview_button_clicked_ui_error(self, mock_pyqt_app, test_config):
        """Test preview button clicked when UI components are missing."""
        window = FileOrganizerMainWindow(test_config)
        window.selected_folders = ["/test/folder"]
        window.recursive_checkbox = None  # Simulate missing component
        
        with patch.object(window, 'show_error_message') as mock_error:
            window.on_preview_button_clicked()
        
        mock_error.assert_called_once()
    
    @pytest.mark.gui
    @patch('PyQt5.QtWidgets.QMessageBox.question')
    def test_start_processing_button_clicked_confirmed(self, mock_question, mock_pyqt_app, test_config, mock_processing_thread):
        """Test start processing with user confirmation."""
        mock_question.return_value = QMessageBox.Yes
        
        window = FileOrganizerMainWindow(test_config)
        window.selected_folders = ["/test/folder"]
        
        with patch('gui.main_window.ProcessingThread', return_value=mock_processing_thread):
            window.on_start_processing_button_clicked()
        
        assert window.is_processing is True
        mock_processing_thread.start.assert_called_once()
    
    @pytest.mark.gui
    @patch('PyQt5.QtWidgets.QMessageBox.question')
    def test_start_processing_button_clicked_cancelled(self, mock_question, mock_pyqt_app, test_config):
        """Test start processing when user cancels confirmation."""
        mock_question.return_value = QMessageBox.No
        
        window = FileOrganizerMainWindow(test_config)
        window.selected_folders = ["/test/folder"]
        
        window.on_start_processing_button_clicked()
        
        assert window.is_processing is False
    
    @pytest.mark.gui
    @patch('PyQt5.QtWidgets.QMessageBox.question')
    def test_stop_button_clicked_confirmed(self, mock_question, mock_pyqt_app, test_config, mock_processing_thread):
        """Test stop processing with user confirmation."""
        mock_question.return_value = QMessageBox.Yes
        mock_processing_thread.isRunning.return_value = True
        
        window = FileOrganizerMainWindow(test_config)
        window.processing_thread = mock_processing_thread
        
        window.on_stop_button_clicked()
        
        mock_processing_thread.stop.assert_called_once()
    
    @pytest.mark.gui
    @patch('PyQt5.QtWidgets.QMessageBox.question')
    def test_stop_button_clicked_cancelled(self, mock_question, mock_pyqt_app, test_config, mock_processing_thread):
        """Test stop processing when user cancels."""
        mock_question.return_value = QMessageBox.No
        mock_processing_thread.isRunning.return_value = True
        
        window = FileOrganizerMainWindow(test_config)
        window.processing_thread = mock_processing_thread
        
        window.on_stop_button_clicked()
        
        mock_processing_thread.stop.assert_not_called()


class TestStatusAndProgressUpdates:
    """Test status and progress update functionality."""
    
    @pytest.mark.gui
    def test_update_status_message(self, mock_pyqt_app, test_config):
        """Test status message updates."""
        window = FileOrganizerMainWindow(test_config)
        
        window.update_status_message("Test status message")
        
        assert window.status_label.text() == "Test status message"
        assert window.status_bar.currentMessage() == "Test status message"
    
    @pytest.mark.gui
    def test_update_progress(self, mock_pyqt_app, test_config):
        """Test progress bar updates."""
        window = FileOrganizerMainWindow(test_config)
        
        window.update_progress(75)
        
        assert window.progress_bar.value() == 75
    
    @pytest.mark.gui
    def test_on_file_processed_signal(self, mock_pyqt_app, test_config):
        """Test file processed signal handling."""
        window = FileOrganizerMainWindow(test_config)
        
        window.on_file_processed_signal("test_file.txt")
        
        assert window.processed_files_count == 1
        assert "test_file.txt" in window.status_bar.currentMessage()
    
    @pytest.mark.gui
    def test_update_ui_periodic(self, mock_pyqt_app, test_config):
        """Test periodic UI updates."""
        window = FileOrganizerMainWindow(test_config)
        window.is_processing = True
        window.total_files_count = 100
        window.processed_files_count = 25
        
        with patch.object(window, 'progress_update') as mock_progress_update:
            window.update_ui()
            mock_progress_update.emit.assert_called_once_with(25)  # 25% progress
    
    @pytest.mark.gui
    def test_update_ui_error_handling(self, mock_pyqt_app, test_config):
        """Test UI update error handling."""
        window = FileOrganizerMainWindow(test_config)
        window.is_processing = True
        window.total_files_count = 0  # Will cause division by zero
        
        # Should not raise exception
        window.update_ui()


class TestProcessingCallbacks:
    """Test processing thread callback handling."""
    
    @pytest.mark.gui
    def test_on_preview_finished(self, mock_pyqt_app, test_config):
        """Test preview completion handling."""
        window = FileOrganizerMainWindow(test_config)
        window.is_processing = True
        window.progress_bar.setVisible(True)
        
        summary = {"preview": 10, "moved": 0, "errors": 2}
        
        window.on_preview_finished(summary)
        
        assert window.is_processing is False
        assert not window.progress_bar.isVisible()
        assert "preview" in window.preview_text_edit.toPlainText().lower()
    
    @pytest.mark.gui
    @patch('PyQt5.QtWidgets.QMessageBox.information')
    def test_on_processing_finished(self, mock_info, mock_pyqt_app, test_config):
        """Test processing completion handling."""
        window = FileOrganizerMainWindow(test_config)
        window.is_processing = True
        window.processed_files_count = 15
        
        summary = {"moved": 10, "duplicate_kept": 3, "errors": 2}
        
        window.on_processing_finished(summary)
        
        assert window.is_processing is False
        mock_info.assert_called_once()
        assert "moved" in window.after_text_edit.toPlainText().lower()
    
    @pytest.mark.gui
    def test_on_error_occurred(self, mock_pyqt_app, test_config):
        """Test error handling from processing thread."""
        window = FileOrganizerMainWindow(test_config)
        window.is_processing = True
        
        with patch.object(window, 'show_error_message') as mock_error:
            window.on_error_occurred("Test error message")
        
        assert window.is_processing is False
        mock_error.assert_called_once_with("Processing Error", "Test error message")
    
    @pytest.mark.gui
    def test_processing_finished_empty_summary(self, mock_pyqt_app, test_config):
        """Test processing finished with empty summary."""
        window = FileOrganizerMainWindow(test_config)
        
        window.on_processing_finished({})
        
        # Should handle empty summary gracefully
        assert "no processing results" in window.after_text_edit.toPlainText().lower()


class TestButtonStateManagement:
    """Test button state management during different operations."""
    
    @pytest.mark.gui
    def test_button_states_no_folders(self, mock_pyqt_app, test_config):
        """Test button states when no folders are selected."""
        window = FileOrganizerMainWindow(test_config)
        window.selected_folders = []
        window.is_processing = False
        
        window.update_button_states()
        
        assert not window.preview_button.isEnabled()
        assert not window.start_processing_button.isEnabled()
        assert not window.stop_button.isEnabled()
        assert window.select_folders_button.isEnabled()
    
    @pytest.mark.gui
    def test_button_states_folders_selected(self, mock_pyqt_app, test_config):
        """Test button states when folders are selected."""
        window = FileOrganizerMainWindow(test_config)
        window.selected_folders = ["/test/folder"]
        window.is_processing = False
        
        window.update_button_states()
        
        assert window.preview_button.isEnabled()
        assert window.start_processing_button.isEnabled()
        assert not window.stop_button.isEnabled()
        assert window.select_folders_button.isEnabled()
    
    @pytest.mark.gui
    def test_button_states_during_processing(self, mock_pyqt_app, test_config):
        """Test button states during processing."""
        window = FileOrganizerMainWindow(test_config)
        window.selected_folders = ["/test/folder"]
        window.is_processing = True
        
        window.update_button_states()
        
        assert not window.preview_button.isEnabled()
        assert not window.start_processing_button.isEnabled()
        assert window.stop_button.isEnabled()
        assert not window.select_folders_button.isEnabled()
    
    @pytest.mark.gui
    def test_button_states_missing_components(self, mock_pyqt_app, test_config):
        """Test button state updates with missing components."""
        window = FileOrganizerMainWindow(test_config)
        window.preview_button = None  # Simulate missing component
        
        # Should not crash
        window.update_button_states()


class TestMenuAndDialogs:
    """Test menu actions and dialog interactions."""
    
    @pytest.mark.gui
    @patch('PyQt5.QtWidgets.QMessageBox.information')
    def test_show_config_dialog(self, mock_info, mock_pyqt_app, test_config):
        """Test configuration dialog display."""
        window = FileOrganizerMainWindow(test_config)
        
        window.show_config_dialog()
        
        mock_info.assert_called_once()
    
    @pytest.mark.gui
    @patch('PyQt5.QtWidgets.QMessageBox.about')
    def test_show_about_dialog(self, mock_about, mock_pyqt_app, test_config):
        """Test about dialog display."""
        window = FileOrganizerMainWindow(test_config)
        
        window.show_about_dialog()
        
        mock_about.assert_called_once()
    
    @pytest.mark.gui
    def test_show_error_message(self, mock_pyqt_app, test_config):
        """Test error message display."""
        window = FileOrganizerMainWindow(test_config)
        
        with patch('PyQt5.QtWidgets.QMessageBox.critical') as mock_critical:
            window.show_error_message("Test Error", "Test error message")
            mock_critical.assert_called_once()
    
    @pytest.mark.gui
    def test_show_warning_message(self, mock_pyqt_app, test_config):
        """Test warning message display."""
        window = FileOrganizerMainWindow(test_config)
        
        with patch('PyQt5.QtWidgets.QMessageBox.warning') as mock_warning:
            window.show_warning_message("Test Warning", "Test warning message")
            mock_warning.assert_called_once()


class TestCloseEvent:
    """Test application close event handling."""
    
    @pytest.mark.gui
    @patch('PyQt5.QtWidgets.QMessageBox.question')
    def test_close_event_during_processing_cancelled(self, mock_question, mock_pyqt_app, test_config, mock_processing_thread):
        """Test close event when processing and user cancels."""
        mock_question.return_value = QMessageBox.No
        
        window = FileOrganizerMainWindow(test_config)
        window.is_processing = True
        window.processing_thread = mock_processing_thread
        mock_processing_thread.isRunning.return_value = True
        
        event = Mock()
        event.ignore = Mock()
        
        window.closeEvent(event)
        
        event.ignore.assert_called_once()
        mock_processing_thread.stop.assert_not_called()
    
    @pytest.mark.gui
    @patch('PyQt5.QtWidgets.QMessageBox.question')
    def test_close_event_during_processing_confirmed(self, mock_question, mock_pyqt_app, test_config, mock_processing_thread):
        """Test close event when processing and user confirms."""
        mock_question.return_value = QMessageBox.Yes
        
        window = FileOrganizerMainWindow(test_config)
        window.is_processing = True
        window.processing_thread = mock_processing_thread
        mock_processing_thread.isRunning.return_value = True
        
        event = Mock()
        event.accept = Mock()
        
        window.closeEvent(event)
        
        event.accept.assert_called_once()
        mock_processing_thread.stop.assert_called_once()
        mock_processing_thread.wait.assert_called_once()
    
    @pytest.mark.gui
    def test_close_event_not_processing(self, mock_pyqt_app, test_config):
        """Test close event when not processing."""
        window = FileOrganizerMainWindow(test_config)
        window.is_processing = False
        
        event = Mock()
        event.accept = Mock()
        
        window.closeEvent(event)
        
        event.accept.assert_called_once()
    
    @pytest.mark.gui
    def test_close_event_error_handling(self, mock_pyqt_app, test_config):
        """Test close event error handling."""
        window = FileOrganizerMainWindow(test_config)
        
        # Force an error during close
        window.update_timer = Mock()
        window.update_timer.stop.side_effect = Exception("Timer error")
        
        event = Mock()
        event.accept = Mock()
        
        # Should not raise exception
        window.closeEvent(event)
        
        event.accept.assert_called_once()


class TestUpdateBeforeStructure:
    """Test folder structure display functionality."""
    
    @pytest.mark.gui
    @patch('os.walk')
    def test_update_before_structure_success(self, mock_walk, mock_pyqt_app, test_config):
        """Test successful folder structure display."""
        mock_walk.return_value = [
            ("/test/folder", ["subdir"], ["file1.txt", "file2.jpg"]),
            ("/test/folder/subdir", [], ["file3.pdf"])
        ]
        
        window = FileOrganizerMainWindow(test_config)
        window.selected_folders = ["/test/folder"]
        
        window.update_before_structure()
        
        structure_text = window.before_text_edit.toPlainText()
        assert "/test/folder" in structure_text
        assert "file1.txt" in structure_text
        assert "subdir" in structure_text
    
    @pytest.mark.gui
    @patch('os.walk')
    def test_update_before_structure_with_many_files(self, mock_walk, mock_pyqt_app, test_config):
        """Test folder structure display with many files."""
        # Create more than 10 files to test truncation
        many_files = [f"file{i}.txt" for i in range(15)]
        mock_walk.return_value = [
            ("/test/folder", [], many_files)
        ]
        
        window = FileOrganizerMainWindow(test_config)
        window.selected_folders = ["/test/folder"]
        
        window.update_before_structure()
        
        structure_text = window.before_text_edit.toPlainText()
        assert "5 more files" in structure_text  # Should truncate and show count
    
    @pytest.mark.gui
    @patch('os.walk')
    def test_update_before_structure_error_handling(self, mock_walk, mock_pyqt_app, test_config):
        """Test folder structure display error handling."""
        mock_walk.side_effect = OSError("Permission denied")
        
        window = FileOrganizerMainWindow(test_config)
        window.selected_folders = ["/test/folder"]
        
        window.update_before_structure()
        
        structure_text = window.before_text_edit.toPlainText()
        assert "error reading folder" in structure_text.lower()
    
    @pytest.mark.gui
    def test_update_before_structure_no_folders(self, mock_pyqt_app, test_config):
        """Test folder structure display with no folders."""
        window = FileOrganizerMainWindow(test_config)
        window.selected_folders = []
        
        window.update_before_structure()
        
        # Should not crash and text should remain unchanged
        # (or be empty if it was empty before)