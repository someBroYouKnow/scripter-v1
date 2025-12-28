"""
Input Selector Component

Widget for selecting input source (file, URL, microphone).
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLineEdit, QLabel, QFileDialog, QGroupBox)
from PyQt6.QtCore import Qt, pyqtSignal


class InputSelector(QGroupBox):
    """Widget for selecting input source."""
    
    # Signals
    file_selected = pyqtSignal(str)
    url_entered = pyqtSignal(str)
    microphone_toggled = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        """Initialize input selector."""
        super().__init__("Input Source", parent)
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        
        # File input
        file_layout = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("No file selected")
        self.file_path_edit.setReadOnly(True)
        self.file_browse_btn = QPushButton("Browse...")
        self.file_browse_btn.clicked.connect(self.browse_file)
        file_layout.addWidget(self.file_path_edit)
        file_layout.addWidget(self.file_browse_btn)
        layout.addLayout(file_layout)
        
        # URL input
        url_layout = QHBoxLayout()
        self.url_edit = QLineEdit()
        self.url_edit.setPlaceholderText("Enter YouTube URL or video URL")
        self.url_edit.returnPressed.connect(self.on_url_entered)
        self.url_btn = QPushButton("Load URL")
        self.url_btn.clicked.connect(self.on_url_entered)
        url_layout.addWidget(self.url_edit)
        url_layout.addWidget(self.url_btn)
        layout.addLayout(url_layout)
        
        # Microphone toggle
        self.mic_btn = QPushButton("🎤 Start Microphone")
        self.mic_btn.setCheckable(True)
        self.mic_btn.clicked.connect(self.on_microphone_toggled)
        layout.addWidget(self.mic_btn)
        
        self.setLayout(layout)
    
    def browse_file(self):
        """Open file dialog to select audio/video file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio/Video File",
            "",
            "Media Files (*.mp3 *.wav *.mp4 *.avi *.mov *.mkv *.m4a *.flac);;"
            "Audio Files (*.mp3 *.wav *.m4a *.flac *.ogg);;"
            "Video Files (*.mp4 *.avi *.mov *.mkv *.wmv *.flv);;"
            "All Files (*.*)"
        )
        
        if file_path:
            self.file_path_edit.setText(file_path)
            self.file_selected.emit(file_path)
    
    def on_url_entered(self):
        """Handle URL entry."""
        url = self.url_edit.text().strip()
        if url:
            self.url_entered.emit(url)
    
    def on_microphone_toggled(self, checked: bool):
        """Handle microphone toggle."""
        if checked:
            self.mic_btn.setText("🎤 Stop Microphone")
        else:
            self.mic_btn.setText("🎤 Start Microphone")
        self.microphone_toggled.emit(checked)
    
    def get_selected_file(self) -> str:
        """Get selected file path."""
        return self.file_path_edit.text()
    
    def get_url(self) -> str:
        """Get entered URL."""
        return self.url_edit.text().strip()
    
    def is_microphone_active(self) -> bool:
        """Check if microphone is active."""
        return self.mic_btn.isChecked()
    
    def clear(self):
        """Clear all inputs."""
        self.file_path_edit.clear()
        self.url_edit.clear()
        if self.mic_btn.isChecked():
            self.mic_btn.setChecked(False)
            self.on_microphone_toggled(False)

