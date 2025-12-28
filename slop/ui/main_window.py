"""
Main Window

Main application window that integrates all components.
"""

import os
import sys
from pathlib import Path
from typing import Optional
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QMessageBox, QStatusBar)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt6.QtGui import QIcon

# Import components
from .components.input_selector import InputSelector
from .components.model_selector import ModelSelector
from .components.progress_dialog import ProgressDialog
from .components.transcript_viewer import TranscriptViewer

# Import core modules
from core.audio_processor import AudioProcessor
from core.youtube_downloader import YouTubeDownloader
from core.microphone_capture import MicrophoneCapture
from core.file_handler import FileHandler

# Import models
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model_dir = os.path.join(project_root, 'speech-to-text-model')
if model_dir not in sys.path:
    sys.path.insert(0, model_dir)

from whisper_model import WhisperModel
from google_model import GoogleModel

# Import utils
from utils.config import Config
from utils.logger import get_logger


class TranscriptionWorker(QObject):
    """Worker thread for transcription."""
    
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(str, int, int)  # message, value, max
    
    def __init__(self, model, audio_path: str, config: dict):
        """Initialize worker."""
        super().__init__()
        self.model = model
        self.audio_path = audio_path
        self.config = config
        self.cancelled = False
    
    def cancel(self):
        """Cancel transcription."""
        self.cancelled = True
    
    def run(self):
        """Run transcription."""
        try:
            self.progress.emit("Transcribing audio...", 0, 100)
            
            # Transcribe
            transcript = self.model.transcribe(self.audio_path, **self.config)
            
            if not self.cancelled:
                self.progress.emit("Transcription complete!", 100, 100)
                self.finished.emit(transcript)
        except Exception as e:
            if not self.cancelled:
                self.error.emit(str(e))


class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        """Initialize main window."""
        super().__init__()
        
        # Initialize logger and config
        self.logger = get_logger()
        self.config = Config()
        
        # Initialize core components
        self.audio_processor = AudioProcessor(
            output_format='wav',
            sample_rate=self.config.get('audio_sample_rate', 16000)
        )
        self.youtube_downloader = YouTubeDownloader(
            audio_format='wav',
            sample_rate=self.config.get('audio_sample_rate', 16000)
        )
        self.microphone_capture = MicrophoneCapture(
            sample_rate=self.config.get('audio_sample_rate', 16000)
        )
        self.file_handler = FileHandler(
            default_format=self.config.get('output_format', 'txt')
        )
        
        # Initialize models
        self.models = {}
        self.current_model = None
        self._init_models()
        
        # Worker thread
        self.worker_thread = None
        self.worker = None
        
        # Current audio file (temp file that may need cleanup)
        self.current_audio_file = None
        
        # Initialize UI
        self.init_ui()
        
        # Connect signals
        self.connect_signals()
    
    def _init_models(self):
        """Initialize available models."""
        try:
            # Whisper model
            whisper_size = self.config.get('whisper_model_size', 'base')
            whisper_model = WhisperModel(model_size=whisper_size)
            self.models['Whisper'] = whisper_model
            self.logger.info(f"Whisper model initialized: {whisper_size}")
        except Exception as e:
            self.logger.error(f"Failed to initialize Whisper: {e}")
        
        try:
            # Google model
            google_creds = self.config.get_google_credentials_path()
            google_lang = self.config.get('google_language_code', 'en-US')
            google_model = GoogleModel(
                credentials_path=google_creds,
                language_code=google_lang
            )
            if google_model.is_available():
                self.models['Google'] = google_model
                self.logger.info("Google Speech-to-Text model initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize Google model: {e}")
    
    def init_ui(self):
        """Initialize UI."""
        self.setWindowTitle("Audio/Video Transcriber")
        self.setMinimumSize(800, 600)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)
        
        # Input selector
        self.input_selector = InputSelector()
        main_layout.addWidget(self.input_selector)
        
        # Model selector
        self.model_selector = ModelSelector()
        for name, model in self.models.items():
            self.model_selector.register_model(name, model)
        main_layout.addWidget(self.model_selector)
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.transcribe_btn = QPushButton("Transcribe")
        self.transcribe_btn.clicked.connect(self.start_transcription)
        self.transcribe_btn.setEnabled(False)
        control_layout.addWidget(self.transcribe_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_transcription)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        control_layout.addStretch()
        main_layout.addLayout(control_layout)
        
        # Transcript viewer
        self.transcript_viewer = TranscriptViewer()
        main_layout.addWidget(self.transcript_viewer)
        
        # Status bar
        self.statusBar().showMessage("Ready")
    
    def connect_signals(self):
        """Connect component signals."""
        # Input selector
        self.input_selector.file_selected.connect(self.on_file_selected)
        self.input_selector.url_entered.connect(self.on_url_entered)
        self.input_selector.microphone_toggled.connect(self.on_microphone_toggled)
        
        # Model selector
        self.model_selector.model_changed.connect(self.on_model_changed)
        self.model_selector.config_changed.connect(self.on_model_config_changed)
        
        # Transcript viewer
        self.transcript_viewer.export_requested.connect(self.export_transcript)
    
    def on_file_selected(self, file_path: str):
        """Handle file selection."""
        self.statusBar().showMessage(f"File selected: {os.path.basename(file_path)}")
        self.transcribe_btn.setEnabled(True)
        self.input_selector.url_edit.clear()
        if self.input_selector.mic_btn.isChecked():
            self.input_selector.mic_btn.setChecked(False)
    
    def on_url_entered(self, url: str):
        """Handle URL entry."""
        if not self.youtube_downloader.is_youtube_url(url):
            QMessageBox.warning(self, "Invalid URL", "Please enter a valid YouTube URL")
            return
        
        self.statusBar().showMessage("Downloading audio from YouTube...")
        self.transcribe_btn.setEnabled(False)
        
        # Download in background
        self.download_youtube_audio(url)
    
    def download_youtube_audio(self, url: str):
        """Download audio from YouTube."""
        try:
            progress_dialog = ProgressDialog(self, "Downloading Audio")
            progress_dialog.show()
            
            def progress_callback(progress):
                progress_dialog.set_progress(int(progress * 100), 100)
                progress_dialog.set_status(f"Downloading... {int(progress * 100)}%")
            
            audio_path = self.youtube_downloader.download_audio(url, progress_callback)
            progress_dialog.close()
            
            self.current_audio_file = audio_path
            self.statusBar().showMessage("Audio downloaded. Ready to transcribe.")
            self.transcribe_btn.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(self, "Download Error", f"Failed to download audio: {e}")
            self.statusBar().showMessage("Download failed")
    
    def on_microphone_toggled(self, active: bool):
        """Handle microphone toggle."""
        if active:
            try:
                self.microphone_capture.start_recording()
                self.statusBar().showMessage("Microphone recording started")
                self.transcribe_btn.setEnabled(True)
            except Exception as e:
                QMessageBox.critical(self, "Microphone Error", f"Failed to start recording: {e}")
                self.input_selector.mic_btn.setChecked(False)
        else:
            # Stop and transcribe
            audio_data = self.microphone_capture.stop_recording()
            if audio_data:
                # Save to temp file
                import tempfile
                fd, temp_path = tempfile.mkstemp(suffix='.wav', prefix='mic_')
                os.close(fd)
                with open(temp_path, 'wb') as f:
                    f.write(audio_data)
                self.current_audio_file = temp_path
                self.statusBar().showMessage("Recording stopped. Ready to transcribe.")
    
    def on_model_changed(self, model_name: str):
        """Handle model selection change."""
        self.current_model = self.model_selector.get_selected_model()
        self.statusBar().showMessage(f"Model changed to: {model_name}")
    
    def on_model_config_changed(self, config: dict):
        """Handle model configuration change."""
        # Update model configuration if needed
        if 'model_size' in config and hasattr(self.current_model, 'set_model_size'):
            self.current_model.set_model_size(config['model_size'])
        if 'language_code' in config and hasattr(self.current_model, 'set_language'):
            self.current_model.set_language(config['language_code'])
    
    def start_transcription(self):
        """Start transcription process."""
        # Get input source
        file_path = self.input_selector.get_selected_file()
        url = self.input_selector.get_url()
        mic_active = self.input_selector.is_microphone_active()
        
        # Get model
        model = self.model_selector.get_selected_model()
        if not model or not model.is_available():
            QMessageBox.warning(self, "Model Error", "Please select an available model")
            return
        
        # Prepare audio
        try:
            if mic_active:
                # Already handled in on_microphone_toggled
                audio_path = self.current_audio_file
            elif url:
                audio_path = self.current_audio_file
            elif file_path:
                # Check if video or audio
                is_video = self.audio_processor.is_video_file(file_path)
                audio_path = self.audio_processor.prepare_audio_for_transcription(
                    file_path, is_video=is_video
                )
                self.current_audio_file = audio_path
            else:
                QMessageBox.warning(self, "No Input", "Please select an input source")
                return
            
            if not audio_path or not os.path.exists(audio_path):
                raise FileNotFoundError("Audio file not found")
            
            # Show progress dialog
            self.progress_dialog = ProgressDialog(self, "Transcribing")
            self.progress_dialog.cancelled.connect(self.stop_transcription)
            self.progress_dialog.show()
            
            # Disable controls
            self.transcribe_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            
            # Start transcription in worker thread
            self.worker_thread = QThread()
            self.worker = TranscriptionWorker(model, audio_path, {})
            self.worker.moveToThread(self.worker_thread)
            
            self.worker_thread.started.connect(self.worker.run)
            self.worker.finished.connect(self.on_transcription_finished)
            self.worker.error.connect(self.on_transcription_error)
            self.worker.progress.connect(self.on_transcription_progress)
            self.worker.finished.connect(self.worker_thread.quit)
            self.worker.error.connect(self.worker_thread.quit)
            
            self.worker_thread.start()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start transcription: {e}")
            self.transcribe_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
    
    def stop_transcription(self):
        """Stop transcription."""
        if self.worker:
            self.worker.cancel()
        if self.worker_thread and self.worker_thread.isRunning():
            self.worker_thread.quit()
            self.worker_thread.wait()
        
        if self.progress_dialog:
            self.progress_dialog.close()
        
        self.transcribe_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.statusBar().showMessage("Transcription cancelled")
    
    def on_transcription_progress(self, message: str, value: int, max_value: int):
        """Handle transcription progress update."""
        if self.progress_dialog:
            self.progress_dialog.set_status(message)
            self.progress_dialog.set_progress(value, max_value)
    
    def on_transcription_finished(self, transcript: str):
        """Handle transcription completion."""
        self.transcript_viewer.set_transcript(transcript)
        self.progress_dialog.close()
        self.transcribe_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.statusBar().showMessage("Transcription complete")
        
        # Cleanup temp audio file
        if self.current_audio_file and 'transcribe_' in self.current_audio_file:
            self.audio_processor.cleanup_temp_file(self.current_audio_file)
    
    def on_transcription_error(self, error: str):
        """Handle transcription error."""
        self.progress_dialog.close()
        QMessageBox.critical(self, "Transcription Error", f"Transcription failed: {error}")
        self.transcribe_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.statusBar().showMessage("Transcription failed")
    
    def export_transcript(self, format: str, file_path: str):
        """Export transcript to file."""
        transcript = self.transcript_viewer.get_transcript()
        if not transcript:
            QMessageBox.warning(self, "No Transcript", "No transcript to export")
            return
        
        try:
            saved_path = self.file_handler.save_transcript(transcript, file_path, format)
            QMessageBox.information(self, "Export Success", f"Transcript saved to:\n{saved_path}")
            self.statusBar().showMessage(f"Transcript exported to {saved_path}")
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export transcript: {e}")
    
    def closeEvent(self, event):
        """Handle window close event."""
        # Stop any ongoing operations
        if self.input_selector.is_microphone_active():
            self.microphone_capture.stop_recording()
        
        if self.worker_thread and self.worker_thread.isRunning():
            self.stop_transcription()
        
        # Cleanup temp files
        if self.current_audio_file:
            if 'transcribe_' in self.current_audio_file:
                self.audio_processor.cleanup_temp_file(self.current_audio_file)
            elif 'youtube_' in self.current_audio_file:
                self.youtube_downloader.cleanup_downloaded_file(self.current_audio_file)
        
        event.accept()

