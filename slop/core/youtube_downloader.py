"""
YouTube Downloader Module

Handles downloading audio from YouTube URLs and validating YouTube links.
"""

import os
import re
from pathlib import Path
from typing import Optional, Callable
import yt_dlp


class YouTubeDownloader:
    """Handles YouTube audio downloads."""
    
    # YouTube URL patterns
    YOUTUBE_PATTERNS = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([\w-]+)',
        r'(?:https?://)?(?:www\.)?youtu\.be/([\w-]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([\w-]+)',
    ]
    
    def __init__(self, output_dir: Optional[str] = None, 
                 audio_format: str = 'wav',
                 sample_rate: int = 16000):
        """
        Initialize YouTube downloader.
        
        Args:
            output_dir: Directory to save downloaded audio (default: temp)
            audio_format: Audio format (default: 'wav')
            sample_rate: Target sample rate (default: 16000)
        """
        self.output_dir = output_dir
        self.audio_format = audio_format
        self.sample_rate = sample_rate
        
        # Create output directory if specified
        if self.output_dir and not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir, exist_ok=True)
    
    def is_youtube_url(self, url: str) -> bool:
        """
        Check if URL is a valid YouTube URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if valid YouTube URL, False otherwise
        """
        if not url:
            return False
        
        for pattern in self.YOUTUBE_PATTERNS:
            if re.match(pattern, url.strip()):
                return True
        
        return False
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL.
        
        Args:
            url: YouTube URL
            
        Returns:
            Video ID or None if invalid
        """
        for pattern in self.YOUTUBE_PATTERNS:
            match = re.match(pattern, url.strip())
            if match:
                return match.group(1)
        return None
    
    def download_audio(self, url: str, 
                      progress_callback: Optional[Callable[[float], None]] = None) -> str:
        """
        Download audio from YouTube URL.
        
        Args:
            url: YouTube URL
            progress_callback: Optional callback for progress updates (0.0-1.0)
            
        Returns:
            Path to downloaded audio file
            
        Raises:
            ValueError: If URL is not a valid YouTube URL
            RuntimeError: If download fails
        """
        if not self.is_youtube_url(url):
            raise ValueError(f"Invalid YouTube URL: {url}")
        
        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError(f"Could not extract video ID from URL: {url}")
        
        try:
            # Configure yt-dlp options
            output_template = self._get_output_path(video_id)
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_template.replace(f'.{self.audio_format}', ''),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': self.audio_format,
                    'preferredquality': '192',
                }],
                'quiet': False,
                'no_warnings': False,
            }
            
            # Add progress hook if callback provided
            if progress_callback:
                def progress_hook(d):
                    if d['status'] == 'downloading':
                        total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                        downloaded = d.get('downloaded_bytes', 0)
                        if total > 0:
                            progress = downloaded / total
                            progress_callback(progress)
                    elif d['status'] == 'finished':
                        progress_callback(1.0)
                
                ydl_opts['progress_hooks'] = [progress_hook]
            
            # Download
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            
            # Return path to downloaded file
            return output_template
        except Exception as e:
            raise RuntimeError(f"Failed to download audio from YouTube: {e}")
    
    def get_video_info(self, url: str) -> dict:
        """
        Get information about YouTube video without downloading.
        
        Args:
            url: YouTube URL
            
        Returns:
            Dictionary with video information (title, duration, etc.)
        """
        if not self.is_youtube_url(url):
            raise ValueError(f"Invalid YouTube URL: {url}")
        
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'title': info.get('title', 'Unknown'),
                    'duration': info.get('duration', 0),
                    'uploader': info.get('uploader', 'Unknown'),
                    'view_count': info.get('view_count', 0),
                    'video_id': info.get('id', ''),
                }
        except Exception as e:
            raise RuntimeError(f"Failed to get video info: {e}")
    
    def _get_output_path(self, video_id: str) -> str:
        """
        Get output path for downloaded audio.
        
        Args:
            video_id: YouTube video ID
            
        Returns:
            Full path to output file
        """
        if self.output_dir:
            return os.path.join(self.output_dir, f"{video_id}.{self.audio_format}")
        else:
            import tempfile
            fd, path = tempfile.mkstemp(
                suffix=f'.{self.audio_format}',
                prefix=f'youtube_{video_id}_',
                dir=None
            )
            os.close(fd)
            return path
    
    def cleanup_downloaded_file(self, file_path: str):
        """
        Clean up downloaded file.
        
        Args:
            file_path: Path to file to delete
        """
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except Exception as e:
            print(f"Warning: Failed to cleanup downloaded file {file_path}: {e}")

