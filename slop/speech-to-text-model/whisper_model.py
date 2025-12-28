"""
OpenAI Whisper Model Implementation

Local speech-to-text using OpenAI's Whisper model.
Supports multiple model sizes: tiny, base, small, medium, large
"""

import os
import sys
import whisper
from typing import Dict, Any, Optional
from pathlib import Path

# Handle import for hyphenated directory name
_model_dir = os.path.dirname(os.path.abspath(__file__))
if _model_dir not in sys.path:
    sys.path.insert(0, _model_dir)
from base_model import BaseModel


class WhisperModel(BaseModel):
    """OpenAI Whisper model implementation."""
    
    # Available model sizes
    MODEL_SIZES = ['tiny', 'base', 'small', 'medium', 'large']
    
    def __init__(self, model_size: str = 'base'):
        """
        Initialize Whisper model.
        
        Args:
            model_size: Size of the model ('tiny', 'base', 'small', 'medium', 'large')
        """
        super().__init__(f"Whisper-{model_size}")
        self.model_size = model_size.lower()
        if self.model_size not in self.MODEL_SIZES:
            raise ValueError(f"Invalid model size. Must be one of {self.MODEL_SIZES}")
        
        self.model = None
        self._available = False
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model."""
        try:
            self.model = whisper.load_model(self.model_size)
            self._available = True
        except Exception as e:
            print(f"Error loading Whisper model: {e}")
            self._available = False
            self.model = None
    
    def is_available(self) -> bool:
        """Check if Whisper model is available."""
        return self._available and self.model is not None
    
    def transcribe(self, audio_path: str, language: Optional[str] = None, 
                   task: str = 'transcribe', **kwargs) -> str:
        """
        Transcribe audio file using Whisper.
        
        Args:
            audio_path: Path to audio file
            language: Language code (e.g., 'en', 'es'). If None, auto-detect
            task: 'transcribe' or 'translate'
            **kwargs: Additional Whisper parameters
            
        Returns:
            Transcribed text
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
        """
        if not self.is_available():
            raise RuntimeError("Whisper model is not available")
        
        if not self.validate_audio_file(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            # Whisper transcribe options
            options = {
                'task': task,
                'language': language,
                **kwargs
            }
            
            # Remove None values
            options = {k: v for k, v in options.items() if v is not None}
            
            result = self.model.transcribe(audio_path, **options)
            return result['text'].strip()
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}")
    
    def transcribe_stream(self, audio_stream, **kwargs) -> str:
        """
        Transcribe audio stream using Whisper.
        
        Note: Whisper doesn't natively support streaming, so we'll save
        the stream to a temporary file first.
        
        Args:
            audio_stream: Audio stream (file-like object or bytes)
            **kwargs: Additional parameters
            
        Returns:
            Transcribed text
        """
        import tempfile
        
        if not self.is_available():
            raise RuntimeError("Whisper model is not available")
        
        try:
            # Save stream to temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
                if hasattr(audio_stream, 'read'):
                    tmp_file.write(audio_stream.read())
                else:
                    tmp_file.write(audio_stream)
                tmp_path = tmp_file.name
            
            # Transcribe the temporary file
            result = self.transcribe(tmp_path, **kwargs)
            
            # Clean up
            os.unlink(tmp_path)
            
            return result
        except Exception as e:
            raise RuntimeError(f"Stream transcription failed: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Whisper model."""
        return {
            'name': self.name,
            'type': 'Whisper',
            'model_size': self.model_size,
            'available': self.is_available(),
            'capabilities': {
                'streaming': False,  # Whisper doesn't support true streaming
                'language_detection': True,
                'translation': True,
                'offline': True
            },
            'supported_formats': ['mp3', 'wav', 'm4a', 'flac', 'ogg']
        }
    
    def set_model_size(self, model_size: str):
        """
        Change the model size (requires reloading).
        
        Args:
            model_size: New model size
        """
        if model_size not in self.MODEL_SIZES:
            raise ValueError(f"Invalid model size. Must be one of {self.MODEL_SIZES}")
        
        self.model_size = model_size.lower()
        self.name = f"Whisper-{model_size}"
        self._load_model()

