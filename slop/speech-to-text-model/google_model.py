"""
Google Cloud Speech-to-Text Model Implementation

Cloud-based speech-to-text using Google Cloud Speech-to-Text API.
Requires Google Cloud credentials and API key.
"""

import os
import sys
from typing import Dict, Any, Optional
from pathlib import Path

# Handle import for hyphenated directory name
_model_dir = os.path.dirname(os.path.abspath(__file__))
if _model_dir not in sys.path:
    sys.path.insert(0, _model_dir)
from base_model import BaseModel

try:
    from google.cloud import speech
    from google.oauth2 import service_account
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False


class GoogleModel(BaseModel):
    """Google Cloud Speech-to-Text model implementation."""
    
    def __init__(self, credentials_path: Optional[str] = None, 
                 api_key: Optional[str] = None,
                 language_code: str = 'en-US'):
        """
        Initialize Google Speech-to-Text model.
        
        Args:
            credentials_path: Path to Google Cloud service account JSON file
            api_key: Alternative: API key string (for limited use)
            language_code: Language code (default: 'en-US')
        """
        super().__init__("Google Speech-to-Text")
        self.credentials_path = credentials_path
        self.api_key = api_key
        self.language_code = language_code
        self.client = None
        self._available = False
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Cloud Speech client."""
        if not GOOGLE_AVAILABLE:
            self._available = False
            return
        
        try:
            if self.credentials_path and os.path.exists(self.credentials_path):
                # Use service account credentials
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                self.client = speech.SpeechClient(credentials=credentials)
                self._available = True
            elif self.api_key:
                # Use API key (limited functionality)
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''
                # Note: API key authentication has limitations
                # For full functionality, use service account credentials
                self.client = speech.SpeechClient()
                self._available = True
            else:
                # Try default credentials
                self.client = speech.SpeechClient()
                self._available = True
        except Exception as e:
            print(f"Error initializing Google Speech client: {e}")
            self._available = False
            self.client = None
    
    def is_available(self) -> bool:
        """Check if Google Speech-to-Text is available."""
        return self._available and self.client is not None
    
    def set_credentials(self, credentials_path: Optional[str] = None,
                        api_key: Optional[str] = None):
        """
        Update credentials for the Google client.
        
        Args:
            credentials_path: Path to service account JSON file
            api_key: API key string
        """
        self.credentials_path = credentials_path
        self.api_key = api_key
        self._initialize_client()
    
    def set_language(self, language_code: str):
        """
        Set the language code for transcription.
        
        Args:
            language_code: Language code (e.g., 'en-US', 'es-ES', 'fr-FR')
        """
        self.language_code = language_code
    
    def transcribe(self, audio_path: str, language_code: Optional[str] = None,
                   enable_automatic_punctuation: bool = True,
                   enable_word_time_offsets: bool = False, **kwargs) -> str:
        """
        Transcribe audio file using Google Speech-to-Text.
        
        Args:
            audio_path: Path to audio file
            language_code: Language code (overrides default if provided)
            enable_automatic_punctuation: Enable automatic punctuation
            enable_word_time_offsets: Include word-level timestamps
            **kwargs: Additional Google Speech parameters
            
        Returns:
            Transcribed text
            
        Raises:
            FileNotFoundError: If audio file doesn't exist
            RuntimeError: If transcription fails
        """
        if not self.is_available():
            raise RuntimeError("Google Speech-to-Text is not available")
        
        if not self.validate_audio_file(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            # Read audio file
            with open(audio_path, 'rb') as audio_file:
                content = audio_file.read()
            
            # Determine audio encoding from file extension
            audio_encoding = self._get_audio_encoding(audio_path)
            
            # Configure recognition
            config = speech.RecognitionConfig(
                encoding=audio_encoding,
                sample_rate_hertz=kwargs.get('sample_rate_hertz', 16000),
                language_code=language_code or self.language_code,
                enable_automatic_punctuation=enable_automatic_punctuation,
                enable_word_time_offsets=enable_word_time_offsets,
            )
            
            audio = speech.RecognitionAudio(content=content)
            
            # Perform transcription
            response = self.client.recognize(config=config, audio=audio)
            
            # Extract transcript
            if response.results:
                transcript = ' '.join([result.alternatives[0].transcript 
                                     for result in response.results])
                return transcript.strip()
            else:
                return ""
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}")
    
    def transcribe_stream(self, audio_stream, language_code: Optional[str] = None,
                         **kwargs) -> str:
        """
        Transcribe audio stream using Google Speech-to-Text.
        
        Args:
            audio_stream: Audio stream (bytes or file-like object)
            language_code: Language code (overrides default if provided)
            **kwargs: Additional parameters
            
        Returns:
            Transcribed text
        """
        if not self.is_available():
            raise RuntimeError("Google Speech-to-Text is not available")
        
        try:
            # Read stream data
            if hasattr(audio_stream, 'read'):
                content = audio_stream.read()
            else:
                content = audio_stream
            
            # Configure recognition
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=kwargs.get('sample_rate_hertz', 16000),
                language_code=language_code or self.language_code,
                enable_automatic_punctuation=True,
            )
            
            audio = speech.RecognitionAudio(content=content)
            
            # Perform transcription
            response = self.client.recognize(config=config, audio=audio)
            
            # Extract transcript
            if response.results:
                transcript = ' '.join([result.alternatives[0].transcript 
                                     for result in response.results])
                return transcript.strip()
            else:
                return ""
        except Exception as e:
            raise RuntimeError(f"Stream transcription failed: {e}")
    
    def _get_audio_encoding(self, audio_path: str) -> speech.RecognitionConfig.AudioEncoding:
        """
        Determine audio encoding from file extension.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Google Speech AudioEncoding enum value
        """
        ext = Path(audio_path).suffix.lower()
        
        encoding_map = {
            '.wav': speech.RecognitionConfig.AudioEncoding.LINEAR16,
            '.flac': speech.RecognitionConfig.AudioEncoding.FLAC,
            '.mp3': speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED,
            '.ogg': speech.RecognitionConfig.AudioEncoding.OGG_OPUS,
        }
        
        return encoding_map.get(ext, speech.RecognitionConfig.AudioEncoding.ENCODING_UNSPECIFIED)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Google Speech-to-Text model."""
        return {
            'name': self.name,
            'type': 'Google Cloud Speech-to-Text',
            'available': self.is_available(),
            'language_code': self.language_code,
            'capabilities': {
                'streaming': True,
                'language_detection': False,  # Requires explicit language code
                'translation': False,  # Separate API
                'offline': False
            },
            'supported_formats': ['wav', 'flac', 'mp3', 'ogg'],
            'requires_credentials': True
        }

