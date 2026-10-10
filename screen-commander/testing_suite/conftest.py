import pytest
from typing import Dict, Any
from config_manager.config import ConfigManager
from context_manager.context import ContextManager
from error_handler.handler import ErrorHandler
from command_parser.parser import CommandParser
from screen_analyzer.analyzer import ScreenAnalyzer
from action_executor.executor import ActionExecutor
from llm_integrator.integrator import LLMIntegrator

class MockConfigManager:
    """Mock configuration manager for testing."""
    
    def __init__(self, config: Dict[str, Any] = None):
        self._config = config or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        parts = key.split('.')
        value = self._config
        for part in parts:
            if not isinstance(value, dict):
                return default
            value = value.get(part, default)
        return value

@pytest.fixture
def mock_config():
    """Provide a mock configuration manager."""
    return MockConfigManager({
        'llm': {
            'default_provider': 'test',
            'temperature': 0.7,
            'max_tokens': 150,
            'api_keys': {
                'test': 'test_key'
            }
        },
        'screen': {
            'capture_interval': 0.1,
            'min_confidence': 0.8
        },
        'action': {
            'click_delay': 0.1,
            'scroll_speed': 50,
            'type_delay': 0.02
        },
        'error': {
            'max_retries': 2,
            'retry_delay': 0.5
        },
        'context': {
            'max_history': 10
        }
    })

@pytest.fixture
def context_manager(mock_config):
    """Provide a context manager instance."""
    return ContextManager(mock_config)

@pytest.fixture
def error_handler(mock_config, context_manager):
    """Provide an error handler instance."""
    return ErrorHandler(mock_config, context_manager)

@pytest.fixture
def command_parser(mock_config):
    """Provide a command parser instance."""
    return CommandParser()

@pytest.fixture
def screen_analyzer(mock_config):
    """Provide a screen analyzer instance."""
    return ScreenAnalyzer(mock_config)

@pytest.fixture
def action_executor(mock_config):
    """Provide an action executor instance."""
    return ActionExecutor(mock_config)

@pytest.fixture
def llm_integrator(mock_config):
    """Provide an LLM integrator instance."""
    return LLMIntegrator(mock_config) 