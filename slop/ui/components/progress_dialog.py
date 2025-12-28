"""
Progress Dialog Component

Dialog for showing transcription progress.
"""

from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QProgressBar,
                             QPushButton)
from PyQt6.QtCore import Qt, pyqtSignal, QThread


class ProgressDialog(QDialog):
    """Progress dialog for transcription operations."""
    
    # Signals
    cancelled = pyqtSignal()
    
    def __init__(self, parent=None, title: str = "Processing"):
        """Initialize progress dialog."""
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(400)
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        
        # Status label
        self.status_label = QLabel("Initializing...")
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate by default
        layout.addWidget(self.progress_bar)
        
        # Cancel button
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.on_cancel)
        layout.addWidget(self.cancel_btn)
        
        self.setLayout(layout)
    
    def set_status(self, message: str):
        """
        Update status message.
        
        Args:
            message: Status message
        """
        self.status_label.setText(message)
    
    def set_progress(self, value: int, maximum: int = 100):
        """
        Set progress value.
        
        Args:
            value: Current progress value
            maximum: Maximum progress value
        """
        self.progress_bar.setRange(0, maximum)
        self.progress_bar.setValue(value)
    
    def set_indeterminate(self, indeterminate: bool = True):
        """
        Set progress bar to indeterminate mode.
        
        Args:
            indeterminate: True for indeterminate, False for determinate
        """
        if indeterminate:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, 100)
    
    def on_cancel(self):
        """Handle cancel button click."""
        self.cancelled.emit()
        self.reject()
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        self.cancelled.emit()
        super().closeEvent(event)

