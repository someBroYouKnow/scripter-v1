"""
Model Selector Component

Widget for selecting and configuring speech-to-text models.
"""

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox,
                             QLabel, QGroupBox, QLineEdit, QPushButton)
from PyQt6.QtCore import pyqtSignal


class ModelSelector(QGroupBox):
    """Widget for selecting STT model."""
    
    # Signals
    model_changed = pyqtSignal(str)
    config_changed = pyqtSignal(dict)
    
    def __init__(self, parent=None):
        """Initialize model selector."""
        super().__init__("Speech-to-Text Model", parent)
        self.available_models = {}
        self.init_ui()
    
    def init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        
        # Model selection
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.currentTextChanged.connect(self.on_model_changed)
        model_layout.addWidget(self.model_combo)
        layout.addLayout(model_layout)
        
        # Model status
        self.status_label = QLabel("Status: Not loaded")
        layout.addWidget(self.status_label)
        
        # Configuration area (dynamic based on model)
        self.config_widget = QWidget()
        self.config_layout = QVBoxLayout()
        self.config_widget.setLayout(self.config_layout)
        layout.addWidget(self.config_widget)
        
        self.setLayout(layout)
    
    def register_model(self, name: str, model_instance):
        """
        Register a model instance.
        
        Args:
            name: Model name
            model_instance: Model instance
        """
        self.available_models[name] = model_instance
        self.model_combo.addItem(name)
        self.update_model_status()
    
    def on_model_changed(self, model_name: str):
        """Handle model selection change."""
        self.update_config_ui(model_name)
        self.model_changed.emit(model_name)
    
    def update_config_ui(self, model_name: str):
        """Update configuration UI based on selected model."""
        # Clear existing config widgets
        while self.config_layout.count():
            child = self.config_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if model_name not in self.available_models:
            return
        
        model = self.available_models[model_name]
        model_info = model.get_model_info()
        
        # Whisper-specific config
        if 'Whisper' in model_name:
            size_layout = QHBoxLayout()
            size_layout.addWidget(QLabel("Model Size:"))
            size_combo = QComboBox()
            size_combo.addItems(['tiny', 'base', 'small', 'medium', 'large'])
            if hasattr(model, 'model_size'):
                size_combo.setCurrentText(model.model_size)
            size_combo.currentTextChanged.connect(
                lambda size: self.config_changed.emit({'model_size': size})
            )
            size_layout.addWidget(size_combo)
            self.config_layout.addLayout(size_layout)
        
        # Google-specific config
        elif 'Google' in model_name:
            lang_layout = QHBoxLayout()
            lang_layout.addWidget(QLabel("Language:"))
            lang_edit = QLineEdit()
            lang_edit.setPlaceholderText("en-US")
            if hasattr(model, 'language_code'):
                lang_edit.setText(model.language_code)
            lang_edit.textChanged.connect(
                lambda lang: self.config_changed.emit({'language_code': lang})
            )
            lang_layout.addWidget(lang_edit)
            self.config_layout.addLayout(lang_layout)
            
            # Credentials button
            creds_btn = QPushButton("Configure Credentials")
            creds_btn.clicked.connect(self.configure_credentials)
            self.config_layout.addWidget(creds_btn)
        
        self.config_layout.addStretch()
    
    def configure_credentials(self):
        """Open credentials configuration dialog."""
        # This would open a dialog for Google credentials
        # For now, emit signal
        self.config_changed.emit({'configure_credentials': True})
    
    def get_selected_model(self):
        """Get selected model instance."""
        model_name = self.model_combo.currentText()
        return self.available_models.get(model_name)
    
    def get_selected_model_name(self) -> str:
        """Get selected model name."""
        return self.model_combo.currentText()
    
    def update_model_status(self):
        """Update model availability status."""
        model_name = self.model_combo.currentText()
        if model_name in self.available_models:
            model = self.available_models[model_name]
            if model.is_available():
                self.status_label.setText(f"Status: ✓ Available")
                self.status_label.setStyleSheet("color: green;")
            else:
                self.status_label.setText(f"Status: ✗ Not Available")
                self.status_label.setStyleSheet("color: red;")
        else:
            self.status_label.setText("Status: Not loaded")
            self.status_label.setStyleSheet("")

