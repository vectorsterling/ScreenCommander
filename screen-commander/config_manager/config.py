import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv

class ConfigManager:
    """Manages application configuration and settings."""
    
    _instance = None
    
    def __new__(cls):
        """Implement singleton pattern for configuration."""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the configuration manager."""
        if self._initialized:
            return
            
        self._initialized = True
        self._config = {}
        self.load_config()
    
    def load_config(self):
        """Load configuration from environment variables."""
        load_dotenv()
        
        # LLM Configuration
        self._config.update({
            'llm': {
                'default_provider': os.getenv('DEFAULT_LLM_PROVIDER', 'openai'),
                'max_tokens': int(os.getenv('MAX_TOKENS', '150')),
                'temperature': float(os.getenv('TEMPERATURE', '0.7')),
                'api_keys': {
                    'openai': os.getenv('OPENAI_API_KEY'),
                    'anthropic': os.getenv('ANTHROPIC_API_KEY'),
                }
            },
            'screen': {
                'capture_interval': float(os.getenv('SCREEN_CAPTURE_INTERVAL', '0.5')),
                'min_confidence': float(os.getenv('MIN_CONFIDENCE_SCORE', '0.8')),
                'ocr_language': os.getenv('OCR_LANGUAGE', 'eng'),
            },
            'action': {
                'click_delay': float(os.getenv('CLICK_DELAY', '0.2')),
                'scroll_speed': int(os.getenv('SCROLL_SPEED', '100')),
                'type_delay': float(os.getenv('TYPE_DELAY', '0.05')),
            },
            'error': {
                'max_retries': int(os.getenv('MAX_RETRIES', '3')),
                'retry_delay': float(os.getenv('RETRY_DELAY', '1.0')),
            }
        })
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Dot-notation key (e.g., 'llm.temperature')
            default: Default value if key not found
            
        Returns:
            The configuration value or default
        """
        try:
            value = self._config
            for part in key.split('.'):
                value = value[part]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """Set a configuration value.
        
        Args:
            key: Dot-notation key (e.g., 'llm.temperature')
            value: Value to set
        """
        parts = key.split('.')
        config = self._config
        
        for part in parts[:-1]:
            if part not in config:
                config[part] = {}
            config = config[part]
            
        config[parts[-1]] = value
    
    @property
    def all(self) -> Dict[str, Any]:
        """Get all configuration values.
        
        Returns:
            Dict containing all configuration values
        """
        return self._config.copy() 