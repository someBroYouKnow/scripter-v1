"""
Configuration Management Module

Handles application settings, user preferences, and secure API key storage.
"""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from dotenv import load_dotenv


class Config:
    """Manages application configuration and settings."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Configuration directory (default: user home/.scripter)
        """
        # Set config directory
        if config_dir is None:
            home = Path.home()
            self.config_dir = home / '.scripter'
        else:
            self.config_dir = Path(config_dir)
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        # Config file paths
        self.config_file = self.config_dir / 'config.json'
        self.key_file = self.config_dir / '.key'
        self.env_file = self.config_dir / '.env'
        
        # Load environment variables
        load_dotenv(self.env_file)
        
        # Initialize encryption key
        self._init_encryption_key()
        
        # Load configuration
        self.settings = self._load_config()
    
    def _init_encryption_key(self):
        """Initialize or load encryption key for API keys."""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                self.encryption_key = f.read()
        else:
            self.encryption_key = Fernet.generate_key()
            with open(self.key_file, 'wb') as f:
                f.write(self.encryption_key)
        
        self.cipher = Fernet(self.encryption_key)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        default_config = {
            'default_model': 'whisper',
            'whisper_model_size': 'base',
            'google_language_code': 'en-US',
            'output_format': 'txt',
            'output_directory': str(Path.home() / 'Documents' / 'Transcripts'),
            'audio_sample_rate': 16000,
            'auto_save': True,
            'theme': 'default'
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # Merge with defaults
                    default_config.update(user_config)
            except Exception as e:
                print(f"Error loading config: {e}")
        
        return default_config
    
    def save_config(self):
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            raise RuntimeError(f"Failed to save config: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.settings.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self.settings[key] = value
    
    def save_api_key(self, service: str, api_key: str):
        """
        Save API key securely (encrypted).
        
        Args:
            service: Service name (e.g., 'google', 'openai')
            api_key: API key to encrypt and save
        """
        encrypted_key = self.cipher.encrypt(api_key.encode())
        
        # Store in settings
        if 'api_keys' not in self.settings:
            self.settings['api_keys'] = {}
        
        self.settings['api_keys'][service] = encrypted_key.decode()
        self.save_config()
    
    def get_api_key(self, service: str) -> Optional[str]:
        """
        Get decrypted API key.
        
        Args:
            service: Service name
            
        Returns:
            Decrypted API key or None if not found
        """
        api_keys = self.settings.get('api_keys', {})
        encrypted_key = api_keys.get(service)
        
        if not encrypted_key:
            # Try environment variable
            env_key = os.getenv(f'{service.upper()}_API_KEY')
            if env_key:
                return env_key
            return None
        
        try:
            return self.cipher.decrypt(encrypted_key.encode()).decode()
        except Exception as e:
            print(f"Error decrypting API key: {e}")
            return None
    
    def delete_api_key(self, service: str):
        """
        Delete stored API key.
        
        Args:
            service: Service name
        """
        if 'api_keys' in self.settings:
            self.settings['api_keys'].pop(service, None)
            self.save_config()
    
    def get_google_credentials_path(self) -> Optional[str]:
        """Get path to Google Cloud credentials file."""
        # Check config
        creds_path = self.settings.get('google_credentials_path')
        if creds_path and os.path.exists(creds_path):
            return creds_path
        
        # Check environment variable
        env_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if env_path and os.path.exists(env_path):
            return env_path
        
        return None
    
    def set_google_credentials_path(self, path: str):
        """
        Set path to Google Cloud credentials file.
        
        Args:
            path: Path to credentials JSON file
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Credentials file not found: {path}")
        
        self.settings['google_credentials_path'] = path
        self.save_config()
    
    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.settings = {
            'default_model': 'whisper',
            'whisper_model_size': 'base',
            'google_language_code': 'en-US',
            'output_format': 'txt',
            'output_directory': str(Path.home() / 'Documents' / 'Transcripts'),
            'audio_sample_rate': 16000,
            'auto_save': True,
            'theme': 'default'
        }
        self.save_config()

