"""
File Handler Module

Handles saving and loading transcripts in various formats (txt, srt, vtt).
"""

import os
from pathlib import Path
from typing import Optional, List, Tuple
from datetime import timedelta


class FileHandler:
    """Handles transcript file operations."""
    
    # Supported export formats
    SUPPORTED_FORMATS = ['txt', 'srt', 'vtt']
    
    def __init__(self, default_format: str = 'txt'):
        """
        Initialize file handler.
        
        Args:
            default_format: Default export format (default: 'txt')
        """
        if default_format not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported format. Must be one of {self.SUPPORTED_FORMATS}")
        
        self.default_format = default_format
    
    def save_transcript(self, transcript: str, output_path: str,
                      format: Optional[str] = None) -> str:
        """
        Save transcript to file.
        
        Args:
            transcript: Transcript text
            output_path: Output file path
            format: File format (default: inferred from extension or default_format)
            
        Returns:
            Path to saved file
        """
        format = format or self._get_format_from_path(output_path) or self.default_format
        
        # Ensure directory exists
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # Ensure correct extension
        if not output_path.endswith(f'.{format}'):
            output_path = f"{output_path}.{format}"
        
        # Save based on format
        if format == 'txt':
            self._save_txt(transcript, output_path)
        elif format == 'srt':
            self._save_srt(transcript, output_path)
        elif format == 'vtt':
            self._save_vtt(transcript, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        return output_path
    
    def load_transcript(self, file_path: str) -> str:
        """
        Load transcript from file.
        
        Args:
            file_path: Path to transcript file
            
        Returns:
            Transcript text
            
        Raises:
            FileNotFoundError: If file doesn't exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Transcript file not found: {file_path}")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to load transcript: {e}")
    
    def validate_file(self, file_path: str) -> bool:
        """
        Validate that file exists and is readable.
        
        Args:
            file_path: Path to file
            
        Returns:
            True if valid, False otherwise
        """
        return os.path.exists(file_path) and os.path.isfile(file_path)
    
    def _save_txt(self, transcript: str, output_path: str):
        """Save transcript as plain text."""
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(transcript)
    
    def _save_srt(self, transcript: str, output_path: str):
        """
        Save transcript as SRT subtitle format.
        
        Note: This is a simple implementation. For proper SRT with timestamps,
        you would need word-level timestamps from the transcription model.
        """
        # Simple SRT: single subtitle entry
        # In a real implementation, you'd parse timestamps from the model
        srt_content = "1\n"
        srt_content += "00:00:00,000 --> 99:59:59,999\n"
        srt_content += f"{transcript}\n\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(srt_content)
    
    def _save_vtt(self, transcript: str, output_path: str):
        """
        Save transcript as WebVTT format.
        
        Note: This is a simple implementation. For proper VTT with timestamps,
        you would need word-level timestamps from the transcription model.
        """
        vtt_content = "WEBVTT\n\n"
        vtt_content += "00:00:00.000 --> 99:59:59.999\n"
        vtt_content += f"{transcript}\n"
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(vtt_content)
    
    def _get_format_from_path(self, file_path: str) -> Optional[str]:
        """
        Get format from file path extension.
        
        Args:
            file_path: File path
            
        Returns:
            Format string or None
        """
        ext = Path(file_path).suffix.lower().lstrip('.')
        return ext if ext in self.SUPPORTED_FORMATS else None
    
    def create_output_path(self, base_name: str, format: Optional[str] = None,
                          output_dir: Optional[str] = None) -> str:
        """
        Create output file path.
        
        Args:
            base_name: Base name for file (without extension)
            format: File format (default: default_format)
            output_dir: Output directory (default: current directory)
            
        Returns:
            Full output path
        """
        format = format or self.default_format
        output_dir = output_dir or os.getcwd()
        
        filename = f"{base_name}.{format}"
        return os.path.join(output_dir, filename)
    
    def parse_srt_timestamps(self, srt_content: str) -> List[Tuple[str, float, float]]:
        """
        Parse SRT file to extract subtitles with timestamps.
        
        Args:
            srt_content: SRT file content
            
        Returns:
            List of (text, start_time, end_time) tuples
        """
        subtitles = []
        blocks = srt_content.strip().split('\n\n')
        
        for block in blocks:
            lines = block.strip().split('\n')
            if len(lines) >= 3:
                # Parse timestamp line (e.g., "00:00:00,000 --> 00:00:05,000")
                time_line = lines[1]
                if '-->' in time_line:
                    start_str, end_str = time_line.split('-->')
                    start_time = self._parse_srt_time(start_str.strip())
                    end_time = self._parse_srt_time(end_str.strip())
                    text = '\n'.join(lines[2:])
                    subtitles.append((text, start_time, end_time))
        
        return subtitles
    
    def _parse_srt_time(self, time_str: str) -> float:
        """
        Parse SRT time string to seconds.
        
        Args:
            time_str: Time string (e.g., "00:00:05,000")
            
        Returns:
            Time in seconds
        """
        # Replace comma with dot for milliseconds
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        
        return hours * 3600 + minutes * 60 + seconds

