"""
Audio Processing Module

Handles audio extraction from video files, format conversion,
and audio preprocessing for transcription.
"""

import os
import tempfile
import subprocess
import warnings
from pathlib import Path
from typing import Optional, Tuple
from pydub import AudioSegment
from moviepy.editor import VideoFileClip


class AudioProcessor:
    """Handles audio extraction and processing."""
    
    # Supported audio formats
    AUDIO_FORMATS = ['.mp3', '.wav', '.m4a', '.flac', '.ogg', '.aac']
    
    # Supported video formats
    VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm']
    
    def __init__(self, output_format: str = 'wav', sample_rate: int = 16000):
        """
        Initialize audio processor.
        
        Args:
            output_format: Output audio format (default: 'wav')
            sample_rate: Target sample rate in Hz (default: 16000)
        """
        self.output_format = output_format
        self.sample_rate = sample_rate
        self._ffmpeg_available = self._check_ffmpeg()
    
    def _check_ffmpeg(self) -> bool:
        """
        Check if ffmpeg is available on the system.
        
        Returns:
            True if ffmpeg is available, False otherwise
        """
        try:
            # Suppress warnings during check
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                result = subprocess.run(
                    ['ffmpeg', '-version'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def is_ffmpeg_available(self) -> bool:
        """
        Check if ffmpeg is available for video processing.
        
        Returns:
            True if ffmpeg is available
        """
        return self._ffmpeg_available
    
    def is_audio_file(self, file_path: str) -> bool:
        """
        Check if file is an audio file.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file is audio, False otherwise
        """
        ext = Path(file_path).suffix.lower()
        return ext in self.AUDIO_FORMATS
    
    def is_video_file(self, file_path: str) -> bool:
        """
        Check if file is a video file.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if file is video, False otherwise
        """
        ext = Path(file_path).suffix.lower()
        return ext in self.VIDEO_FORMATS
    
    def extract_audio_from_video(self, video_path: str, 
                                 output_path: Optional[str] = None) -> str:
        """
        Extract audio from video file.
        
        Args:
            video_path: Path to video file
            output_path: Optional output path. If None, creates temp file.
            
        Returns:
            Path to extracted audio file
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If file is not a video
            RuntimeError: If extraction fails or ffmpeg is not available
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        if not self.is_video_file(video_path):
            raise ValueError(f"File is not a video: {video_path}")
        
        # Check for ffmpeg
        if not self.is_ffmpeg_available():
            raise RuntimeError(
                "FFmpeg is required for video processing but was not found.\n"
                "Please install FFmpeg:\n"
                "  Windows: Download from https://ffmpeg.org/download.html\n"
                "  Or use: choco install ffmpeg (if Chocolatey is installed)\n"
                "  Or use: winget install ffmpeg"
            )
        
        try:
            # Create output path if not provided
            if output_path is None:
                output_path = self._create_temp_audio_file()
            
            # Suppress moviepy warnings about ffmpeg
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                
                # Extract audio using moviepy
                video = VideoFileClip(video_path)
                audio = video.audio
                
                if audio is None:
                    raise RuntimeError("No audio track found in video")
                
                # Write audio to file
                audio.write_audiofile(
                    output_path,
                    codec='pcm_s16le' if self.output_format == 'wav' else None,
                    fps=self.sample_rate,
                    verbose=False,
                    logger=None
                )
                
                # Clean up
                audio.close()
                video.close()
            
            return output_path
        except Exception as e:
            raise RuntimeError(f"Failed to extract audio from video: {e}")
    
    def convert_audio_format(self, input_path: str, 
                            output_path: Optional[str] = None,
                            target_format: Optional[str] = None) -> str:
        """
        Convert audio file to target format.
        
        Args:
            input_path: Path to input audio file
            output_path: Optional output path. If None, creates temp file.
            target_format: Target format (default: self.output_format)
            
        Returns:
            Path to converted audio file
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Audio file not found: {input_path}")
        
        target_format = target_format or self.output_format
        
        try:
            # Load audio
            audio = AudioSegment.from_file(input_path)
            
            # Resample if needed
            if audio.frame_rate != self.sample_rate:
                audio = audio.set_frame_rate(self.sample_rate)
            
            # Set to mono if stereo
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # Create output path if not provided
            if output_path is None:
                output_path = self._create_temp_audio_file(target_format)
            
            # Export audio
            audio.export(output_path, format=target_format)
            
            return output_path
        except Exception as e:
            raise RuntimeError(f"Failed to convert audio: {e}")
    
    def normalize_audio(self, audio_path: str, 
                       output_path: Optional[str] = None) -> str:
        """
        Normalize audio levels.
        
        Args:
            audio_path: Path to audio file
            output_path: Optional output path. If None, creates temp file.
            
        Returns:
            Path to normalized audio file
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            # Load audio
            audio = AudioSegment.from_file(audio_path)
            
            # Normalize
            normalized = audio.normalize()
            
            # Create output path if not provided
            if output_path is None:
                output_path = self._create_temp_audio_file()
            
            # Export
            normalized.export(output_path, format=self.output_format)
            
            return output_path
        except Exception as e:
            raise RuntimeError(f"Failed to normalize audio: {e}")
    
    def prepare_audio_for_transcription(self, input_path: str,
                                       is_video: bool = False) -> str:
        """
        Prepare audio file for transcription (extract if video, convert format).
        
        Args:
            input_path: Path to audio or video file
            is_video: Whether input is a video file
            
        Returns:
            Path to prepared audio file
        """
        if is_video or self.is_video_file(input_path):
            # Extract audio from video
            audio_path = self.extract_audio_from_video(input_path)
        else:
            # Convert audio format if needed
            ext = Path(input_path).suffix.lower()
            if ext != f'.{self.output_format}':
                audio_path = self.convert_audio_format(input_path)
            else:
                # Just normalize if already in correct format
                audio_path = self.normalize_audio(input_path)
        
        return audio_path
    
    def get_audio_info(self, audio_path: str) -> dict:
        """
        Get information about audio file.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Dictionary with audio information
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            audio = AudioSegment.from_file(audio_path)
            return {
                'duration_seconds': len(audio) / 1000.0,
                'sample_rate': audio.frame_rate,
                'channels': audio.channels,
                'format': Path(audio_path).suffix.lower(),
                'file_size': os.path.getsize(audio_path)
            }
        except Exception as e:
            raise RuntimeError(f"Failed to get audio info: {e}")
    
    def _create_temp_audio_file(self, format: Optional[str] = None) -> str:
        """
        Create a temporary audio file path.
        
        Args:
            format: Audio format (default: self.output_format)
            
        Returns:
            Path to temporary file
        """
        format = format or self.output_format
        fd, path = tempfile.mkstemp(suffix=f'.{format}', prefix='transcribe_')
        os.close(fd)
        return path
    
    def cleanup_temp_file(self, file_path: str):
        """
        Clean up temporary file.
        
        Args:
            file_path: Path to file to delete
        """
        try:
            if os.path.exists(file_path) and 'transcribe_' in file_path:
                os.unlink(file_path)
        except Exception as e:
            print(f"Warning: Failed to cleanup temp file {file_path}: {e}")

