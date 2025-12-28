"""
Microphone Capture Module

Handles real-time audio capture from microphone for live transcription.
"""

import threading
import queue
import time
from typing import Optional, Callable
import numpy as np

try:
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except ImportError:
    SOUNDDEVICE_AVAILABLE = False
    try:
        import pyaudio
        PYAUDIO_AVAILABLE = True
    except ImportError:
        PYAUDIO_AVAILABLE = False


class MicrophoneCapture:
    """Handles real-time microphone audio capture."""
    
    def __init__(self, sample_rate: int = 16000, 
                 channels: int = 1,
                 chunk_size: int = 1024,
                 device: Optional[int] = None):
        """
        Initialize microphone capture.
        
        Args:
            sample_rate: Sample rate in Hz (default: 16000)
            channels: Number of audio channels (default: 1 for mono)
            chunk_size: Size of audio chunks (default: 1024)
            device: Audio device index (None for default)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.device = device
        
        self.is_recording = False
        self.audio_queue = queue.Queue()
        self.audio_buffer = []
        self.recording_thread = None
        self.stream = None
        
        # Use sounddevice if available, otherwise pyaudio
        self.use_sounddevice = SOUNDDEVICE_AVAILABLE
    
    def list_audio_devices(self) -> list:
        """
        List available audio input devices.
        
        Returns:
            List of device dictionaries with name and index
        """
        devices = []
        
        if self.use_sounddevice and SOUNDDEVICE_AVAILABLE:
            try:
                device_list = sd.query_devices()
                for i, device in enumerate(device_list):
                    if device['max_input_channels'] > 0:
                        devices.append({
                            'index': i,
                            'name': device['name'],
                            'channels': device['max_input_channels'],
                            'sample_rate': device['default_samplerate']
                        })
            except Exception as e:
                print(f"Error listing devices: {e}")
        elif PYAUDIO_AVAILABLE:
            try:
                import pyaudio
                p = pyaudio.PyAudio()
                for i in range(p.get_device_count()):
                    info = p.get_device_info_by_index(i)
                    if info['maxInputChannels'] > 0:
                        devices.append({
                            'index': i,
                            'name': info['name'],
                            'channels': info['maxInputChannels'],
                            'sample_rate': int(info['defaultSampleRate'])
                        })
                p.terminate()
            except Exception as e:
                print(f"Error listing devices: {e}")
        
        return devices
    
    def start_recording(self, callback: Optional[Callable[[bytes], None]] = None):
        """
        Start recording from microphone.
        
        Args:
            callback: Optional callback function for audio chunks
            
        Raises:
            RuntimeError: If recording fails to start
        """
        if self.is_recording:
            return
        
        self.is_recording = True
        self.audio_buffer = []
        self.callback = callback
        
        if self.use_sounddevice and SOUNDDEVICE_AVAILABLE:
            self._start_sounddevice_recording()
        elif PYAUDIO_AVAILABLE:
            self._start_pyaudio_recording()
        else:
            raise RuntimeError("No audio library available (sounddevice or pyaudio)")
    
    def _start_sounddevice_recording(self):
        """Start recording using sounddevice."""
        def audio_callback(indata, frames, time_info, status):
            if status:
                print(f"Audio callback status: {status}")
            
            if self.is_recording:
                # Convert to bytes
                audio_bytes = (indata * 32767).astype(np.int16).tobytes()
                self.audio_queue.put(audio_bytes)
                self.audio_buffer.append(indata.copy())
                
                if self.callback:
                    self.callback(audio_bytes)
        
        try:
            self.stream = sd.InputStream(
                device=self.device,
                channels=self.channels,
                samplerate=self.sample_rate,
                blocksize=self.chunk_size,
                callback=audio_callback,
                dtype='float32'
            )
            self.stream.start()
        except Exception as e:
            self.is_recording = False
            raise RuntimeError(f"Failed to start recording: {e}")
    
    def _start_pyaudio_recording(self):
        """Start recording using pyaudio."""
        import pyaudio
        
        def audio_callback(in_data, frame_count, time_info, status):
            if self.is_recording:
                self.audio_queue.put(in_data)
                self.audio_buffer.append(in_data)
                
                if self.callback:
                    self.callback(in_data)
            
            return (None, pyaudio.paContinue)
        
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            self.stream = self.pyaudio_instance.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device,
                frames_per_buffer=self.chunk_size,
                stream_callback=audio_callback
            )
            self.stream.start_stream()
        except Exception as e:
            self.is_recording = False
            raise RuntimeError(f"Failed to start recording: {e}")
    
    def stop_recording(self) -> bytes:
        """
        Stop recording and return all captured audio.
        
        Returns:
            Combined audio data as bytes
        """
        if not self.is_recording:
            return b''
        
        self.is_recording = False
        
        # Stop stream
        if self.stream:
            if self.use_sounddevice and SOUNDDEVICE_AVAILABLE:
                self.stream.stop()
                self.stream.close()
            elif PYAUDIO_AVAILABLE:
                self.stream.stop_stream()
                self.stream.close()
                self.pyaudio_instance.terminate()
            self.stream = None
        
        # Combine all audio chunks
        if self.use_sounddevice and self.audio_buffer:
            # Convert numpy arrays to bytes
            combined = np.concatenate(self.audio_buffer)
            return combined.astype(np.int16).tobytes()
        else:
            # Combine bytes
            return b''.join(self.audio_buffer)
    
    def get_audio_chunk(self, timeout: float = 1.0) -> Optional[bytes]:
        """
        Get next audio chunk from queue.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Audio chunk bytes or None if timeout
        """
        try:
            return self.audio_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def clear_buffer(self):
        """Clear audio buffer."""
        self.audio_buffer = []
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break
    
    def is_available(self) -> bool:
        """Check if microphone capture is available."""
        return SOUNDDEVICE_AVAILABLE or PYAUDIO_AVAILABLE
    
    def get_default_device(self) -> Optional[int]:
        """
        Get default input device index.
        
        Returns:
            Device index or None
        """
        if self.use_sounddevice and SOUNDDEVICE_AVAILABLE:
            try:
                return sd.default.device[0]  # Input device
            except:
                return None
        elif PYAUDIO_AVAILABLE:
            try:
                import pyaudio
                p = pyaudio.PyAudio()
                default = p.get_default_input_device_info()
                device_index = default['index']
                p.terminate()
                return device_index
            except:
                return None
        return None

