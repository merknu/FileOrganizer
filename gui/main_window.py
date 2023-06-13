# gui/main_window.py
import os
import logging
from PyQt5.QtWidgets import (QMainWindow, QFileDialog, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel,
                             QProgressBar, QMessageBox, QTextEdit, QSplitter)
from PyQt5.QtCore import Qt
from gui.processing_thread import ProcessingThread


class FileOrganizerMainWindow(QMainWindow):
    def __init__(self, app_config, process_folders_function):
        super().__init__()
        self.app_config = app_config
        self.process_folders = process_folders_function
        self.select_folders_button = None
        self.start_processing_button = None
        self.preview_button = None
        self.before_text_edit = None
        self.after_text_edit = None
        self.status_label = None
        self.progress_bar = None
        self.selected_folders = None
        self.processing_thread = None
        self.on_error_occurred = None
        self.preview_text_edit = None  # add this line to initialize preview_text_edit
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('File Organizer')
        self.resize(800, 600)

        # Create central widget
        central_widget = QWidget(self)
        central_widget.setAcceptDrops(True)
        self.setCentralWidget(central_widget)

        # Create layout
        layout = QVBoxLayout()

        # Create buttons
        self.select_folders_button = QPushButton("Select Folders", self)
        self.select_folders_button.clicked.connect(self.on_select_folders_button_clicked)

        self.start_processing_button = QPushButton("Start Processing", self)
        self.start_processing_button.clicked.connect(self.on_start_processing_button_clicked)
        self.start_processing_button.setEnabled(False)

        self.preview_button = QPushButton("Preview", self)
        self.preview_button.clicked.connect(self.on_preview_button_clicked)
        self.preview_button.setEnabled(False)

        # Status label
        self.status_label = QLabel("Select folders to process")

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)

        # Add buttons and progress bar to layout
        layout.addWidget(self.select_folders_button)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.start_processing_button)
        button_layout.addWidget(self.progress_bar)
        button_layout.addWidget(self.preview_button)

        layout.addLayout(button_layout)
        layout.addWidget(self.status_label)

        # Add a QSplitter widget to split the preview section
        splitter = QSplitter(Qt.Horizontal)

        # Add QTextEdit widgets to display the before and after states
        self.before_text_edit = QTextEdit(self)
        self.before_text_edit.setReadOnly(True)
        splitter.addWidget(self.before_text_edit)

        self.after_text_edit = QTextEdit(self)
        self.after_text_edit.setReadOnly(True)
        splitter.addWidget(self.after_text_edit)

        layout.addWidget(splitter)

        # Add a QTextEdit widget to display the preview state
        self.preview_text_edit = QTextEdit(self)
        self.preview_text_edit.setReadOnly(True)
        layout.addWidget(self.preview_text_edit)

        # Set layout for central widget
        central_widget.setLayout(layout)

        # Add a status bar
        self.statusBar()

    def on_progress_changed(self, progress):
        self.progress_bar.setValue(progress)

    def update_preview(self, summary):
        summary_str = "\n".join(f"{k}: {v}" for k, v in summary.items())
        self.preview_text_edit.setPlainText(summary_str)

    def on_select_folders_button_clicked(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DirectoryOnly
        options |= QFileDialog.ShowDirsOnly
        options |= QFileDialog.ReadOnly

        try:
            folder = QFileDialog.getExistingDirectoryUrl(self, "Select Folder", options=options)
            if folder.isValid():
                self.selected_folders = [folder.toLocalFile()]
                self.start_processing_button.setEnabled(True)
                self.preview_button.setEnabled(True)  # Enable the preview button
                self.status_label.setText(f"Selected folder: {', '.join(self.selected_folders)}")
            else:
                self.status_label.setText("No folder selected")
        except Exception as e:
            logging.error(f"Error in on_select_folders_button_clicked: {e}")
            self.status_label.setText("Error occurred while selecting folders")

    def on_start_processing_button_clicked(self):
        try:
            self.start_processing_button.setEnabled(False)
            self.select_folders_button.setEnabled(False)
            self.status_label.setText("Processing started")
            self.progress_bar.setVisible(True)

            self.processing_thread = ProcessingThread(self.selected_folders, self.app_config, self.process_folders,
                                                      preview_mode=False,
                                                      callback=lambda: self.processing_thread.file_processed.emit())
            self.processing_thread.processing_finished.connect(self.on_processing_finished)
            self.processing_thread.file_processed.connect(self.update_progress_bar)
            self.processing_thread.error_occurred.connect(self.on_error_occurred)
            self.processing_thread.start()

        except Exception as e:
            logging.error(f"Error in on_start_processing_button_clicked: {e}")
            self.start_processing_button.setEnabled(True)
            self.select_folders_button.setEnabled(True)
            self.status_label.setText("Error occurred")
            self.progress_bar.setVisible(False)

    def on_preview_button_clicked(self):
        try:
            self.processing_thread = ProcessingThread(self.selected_folders, self.app_config, self.process_folders,
                                                      preview_mode=True,
                                                      callback=self.update_preview)  # Pass update_preview as callback
            self.processing_thread.processing_finished.connect(self.on_processing_finished)
            self.processing_thread.file_processed.connect(self.update_progress_bar)
            self.processing_thread.error_occurred.connect(self.on_error_occurred)
            self.processing_thread.start()  # Start the thread
        except Exception as e:
            logging.error(f"Error in on_preview_button_clicked: {e}")
            self.status_label.setText("Error occurred while previewing")

    def update_progress_bar(self, progress):
        self.progress_bar.setValue(progress)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        event.acceptProposedAction()

    def dropEvent(self, event):
        urls = [url.toLocalFile() for url in event.mimeData().urls()]
        self.selected_folders = [url for url in urls if os.path.isdir(url)]
        self.start_processing_button.setEnabled(len(self.selected_folders) > 0)
        self.preview_button.setEnabled(len(self.selected_folders) > 0)
        self.status_label.setText(f"Selected folder(s): {', '.join(self.selected_folders)}")
        event.acceptProposedAction()

    def on_processing_finished(self, summary):
        try:
            self.start_processing_button.setEnabled(True)
            self.select_folders_button.setEnabled(True)
            if not summary:
                self.status_label.setText("Processing finished")
            else:
                error_message = "Error(s) occurred during processing:"
                for key, value in summary.items():
                    error_message += f"\n{key}: {value}"
                self.status_label.setText(error_message)
            self.progress_bar.setVisible(False)

        except Exception as e:
            logging.error(f"Error in on_processing_finished: {e}")
            self.status_label.setText("Error occurred while finishing processing")

    def on_error_occurred(self, error_message):
        self.status_label.setText(f"Error occurred: {error_message}")

    def closeEvent(self, event):
        reply = QMessageBox.question(self, "Confirm Exit", "Are you sure you want to exit the application?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            if self.processing_thread.isRunning():
                self.processing_thread.terminate()
            event.accept()
        else:
            event.ignore()
