"""
Transcript Viewer Component

Widget for displaying and exporting transcripts.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                             QPushButton, QGroupBox, QFileDialog, QComboBox,
                             QLabel)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QTextCursor


class TranscriptViewer(QGroupBox):
    """Widget for displaying and exporting transcripts."""
    
    # Signals
    export_requested = pyqtSignal(str, str)  # format, path
    
    def __init__(self, parent=None):
        """Initialize transcript viewer."""
        super().__init__("Transcript", parent)
        self.transcript_text = ""
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Copy button
        self.copy_btn = QPushButton("Copy")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        toolbar.addWidget(self.copy_btn)
        
        # Clear button
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.clear)
        toolbar.addWidget(self.clear_btn)
        
        toolbar.addStretch()
        
        # Export format selector
        toolbar.addWidget(QLabel("Export as:"))
        self.format_combo = QComboBox()
        self.format_combo.addItems(['txt', 'srt', 'vtt'])
        toolbar.addWidget(self.format_combo)
        
        # Export button
        self.export_btn = QPushButton("Export...")
        self.export_btn.clicked.connect(self.export_transcript)
        toolbar.addWidget(self.export_btn)
        
        layout.addLayout(toolbar)
        
        # Transcript text area
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(False)
        self.text_edit.setPlaceholderText("Transcript will appear here...")
        layout.addWidget(self.text_edit)
        
        # Word count label
        self.word_count_label = QLabel("Words: 0")
        layout.addWidget(self.word_count_label)
        
        self.setLayout(layout)
    
    def set_transcript(self, text: str):
        """
        Set transcript text.
        
        Args:
            text: Transcript text
        """
        self.transcript_text = text
        self.text_edit.setPlainText(text)
        self.update_word_count()
        # Scroll to top
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.Start)
        self.text_edit.setTextCursor(cursor)
    
    def append_transcript(self, text: str):
        """
        Append text to transcript.
        
        Args:
            text: Text to append
        """
        self.transcript_text += text
        self.text_edit.append(text)
        self.update_word_count()
    
    def get_transcript(self) -> str:
        """Get current transcript text."""
        return self.text_edit.toPlainText()
    
    def clear(self):
        """Clear transcript."""
        self.transcript_text = ""
        self.text_edit.clear()
        self.update_word_count()
    
    def copy_to_clipboard(self):
        """Copy transcript to clipboard."""
        text = self.text_edit.toPlainText()
        if text:
            clipboard = self.text_edit.clipboard()
            clipboard.setText(text)
    
    def export_transcript(self):
        """Export transcript to file."""
        text = self.text_edit.toPlainText()
        if not text:
            return
        
        format = self.format_combo.currentText()
        
        # Get save path
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            f"Export Transcript as {format.upper()}",
            "",
            f"{format.upper()} Files (*.{format});;All Files (*.*)"
        )
        
        if file_path:
            self.export_requested.emit(format, file_path)
    
    def update_word_count(self):
        """Update word count label."""
        text = self.text_edit.toPlainText()
        word_count = len(text.split()) if text else 0
        char_count = len(text)
        self.word_count_label.setText(f"Words: {word_count} | Characters: {char_count}")

