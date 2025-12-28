"""
Speech-to-Text Model Package

This package contains implementations of various speech-to-text models.
All models inherit from the BaseModel abstract class.

Note: Due to hyphenated directory name, imports use sys.path manipulation.
"""

import os
import sys

# Add directory to path for imports
_model_dir = os.path.dirname(os.path.abspath(__file__))
if _model_dir not in sys.path:
    sys.path.insert(0, _model_dir)

from base_model import BaseModel
from whisper_model import WhisperModel
from google_model import GoogleModel

__all__ = ['BaseModel', 'WhisperModel', 'GoogleModel']

