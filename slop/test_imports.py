"""
Simple import test to verify all modules can be imported correctly.
This is a basic integration test.
"""

import sys
import os

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_imports():
    """Test that all modules can be imported."""
    errors = []
    
    print("Testing module imports...")
    
    # Test core modules
    try:
        from core.audio_processor import AudioProcessor
        print("[OK] AudioProcessor imported")
    except Exception as e:
        errors.append(f"AudioProcessor: {e}")
        print(f"[FAIL] AudioProcessor: {e}")
    
    try:
        from core.youtube_downloader import YouTubeDownloader
        print("[OK] YouTubeDownloader imported")
    except Exception as e:
        errors.append(f"YouTubeDownloader: {e}")
        print(f"[FAIL] YouTubeDownloader: {e}")
    
    try:
        from core.microphone_capture import MicrophoneCapture
        print("[OK] MicrophoneCapture imported")
    except Exception as e:
        errors.append(f"MicrophoneCapture: {e}")
        print(f"[FAIL] MicrophoneCapture: {e}")
    
    try:
        from core.file_handler import FileHandler
        print("[OK] FileHandler imported")
    except Exception as e:
        errors.append(f"FileHandler: {e}")
        print(f"[FAIL] FileHandler: {e}")
    
    # Test model modules
    model_dir = os.path.join(project_root, 'speech-to-text-model')
    if model_dir not in sys.path:
        sys.path.insert(0, model_dir)
    
    try:
        from base_model import BaseModel
        print("[OK] BaseModel imported")
    except Exception as e:
        errors.append(f"BaseModel: {e}")
        print(f"[FAIL] BaseModel: {e}")
    
    try:
        from whisper_model import WhisperModel
        print("[OK] WhisperModel imported")
    except Exception as e:
        errors.append(f"WhisperModel: {e}")
        print(f"[FAIL] WhisperModel: {e}")
    
    try:
        from google_model import GoogleModel
        print("[OK] GoogleModel imported")
    except Exception as e:
        errors.append(f"GoogleModel: {e}")
        print(f"[FAIL] GoogleModel: {e}")
    
    # Test utils
    try:
        from utils.config import Config
        print("[OK] Config imported")
    except Exception as e:
        errors.append(f"Config: {e}")
        print(f"[FAIL] Config: {e}")
    
    try:
        from utils.logger import setup_logger
        print("[OK] Logger imported")
    except Exception as e:
        errors.append(f"Logger: {e}")
        print(f"[FAIL] Logger: {e}")
    
    # Test UI components (may fail if PyQt6 not installed, that's OK)
    try:
        from ui.components.input_selector import InputSelector
        print("[OK] InputSelector imported")
    except Exception as e:
        print(f"[WARN] InputSelector: {e} (PyQt6 may not be installed)")
    
    print("\n" + "="*50)
    if errors:
        print(f"Found {len(errors)} import errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("All core modules imported successfully!")
        print("\nNote: UI components require PyQt6 to be installed.")
        print("Run: pip install -r requirements.txt")
        return True

if __name__ == '__main__':
    success = test_imports()
    sys.exit(0 if success else 1)

