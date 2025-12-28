"""
Main Entry Point

Application entry point for the Audio/Video Transcriber.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt
from ui.main_window import MainWindow
from utils.logger import setup_logger


def check_dependencies():
    """Check if required dependencies are available."""
    missing = []
    
    try:
        import PyQt6
    except ImportError:
        missing.append("PyQt6")
    
    try:
        import whisper
    except ImportError:
        missing.append("openai-whisper")
    
    try:
        import pydub
    except ImportError:
        missing.append("pydub")
    
    try:
        from moviepy import editor
    except ImportError:
        missing.append("moviepy")
    
    try:
        import yt_dlp
    except ImportError:
        missing.append("yt-dlp")
    
    if missing:
        return False, missing
    return True, []


def main():
    """Main application entry point."""
    # Setup logging
    logger = setup_logger()
    logger.info("Starting Audio/Video Transcriber application")
    
    # Check dependencies
    deps_ok, missing = check_dependencies()
    if not deps_ok:
        error_msg = (
            "Missing required dependencies:\n\n" +
            "\n".join(f"  - {dep}" for dep in missing) +
            "\n\nPlease install them using:\n" +
            f"  pip install -r {project_root / 'requirements.txt'}"
        )
        
        # Try to show error in GUI, fallback to console
        app = QApplication(sys.argv)
        QMessageBox.critical(None, "Missing Dependencies", error_msg)
        logger.error(f"Missing dependencies: {missing}")
        sys.exit(1)
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Audio/Video Transcriber")
    app.setOrganizationName("Scripter")
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    try:
        window = MainWindow()
        window.show()
        logger.info("Main window displayed")
    except Exception as e:
        logger.error(f"Failed to create main window: {e}", exc_info=True)
        QMessageBox.critical(None, "Startup Error", 
                           f"Failed to start application:\n{e}")
        sys.exit(1)
    
    # Run application
    try:
        exit_code = app.exec()
        logger.info(f"Application exited with code {exit_code}")
        return exit_code
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())

