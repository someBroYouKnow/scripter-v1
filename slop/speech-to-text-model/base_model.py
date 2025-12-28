"""
Abstract Base Class for Speech-to-Text Models

All STT model implementations must inherit from this class and implement
the required abstract methods.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from pathlib import Path


class BaseModel(ABC):
    """Abstract base class for all speech-to-text models."""
    
    def __init__(self, name: str):
        """
        Initialize the base model.
        
        Args:
            name: Name identifier for this model
        """
        self.name = name
        self._available = False
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the model is available and ready to use.
        
        Returns:
            True if the model is available, False otherwise
        """
        pass
    
    @abstractmethod
    def transcribe(self, audio_path: str, **kwargs) -> str:
        """
        Transcribe audio from a file.
        
        Args:
            audio_path: Path to the audio file
            **kwargs: Additional model-specific parameters
            
        Returns:
            Transcribed text as a string
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
        """
        pass
    
    @abstractmethod
    def transcribe_stream(self, audio_stream, **kwargs) -> str:
        """
        Transcribe audio from a stream (for real-time transcription).
        
        Args:
            audio_stream: Audio stream object
            **kwargs: Additional model-specific parameters
            
        Returns:
            Transcribed text as a string
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.
        
        Returns:
            Dictionary containing model information (name, version, capabilities, etc.)
        """
        pass
    
    def validate_audio_file(self, audio_path: str) -> bool:
        """
        Validate that the audio file exists and is readable.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            True if file is valid, False otherwise
        """
        path = Path(audio_path)
        return path.exists() and path.is_file()
    
    def get_name(self) -> str:
        """Get the model name."""
        return self.name

