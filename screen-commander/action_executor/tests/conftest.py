"""Test fixtures for the Action Executor domain."""
import pytest
from unittest.mock import MagicMock
from executor import ActionExecutor

@pytest.fixture
def mock_config():
    """Create a mock configuration manager."""
    config = MagicMock()
    
    def get_side_effect(key, default=None):
        if key == "action.click_delay":
            return 0.2
        if key == "action.type_delay":
            return 0.05
        if key == "action.scroll_speed":
            return 100
        if key == "safety.zones":
            return []  # No safety zones by default in tests
        return default
        
    config.get.side_effect = get_side_effect
    return config

@pytest.fixture
def action_executor(mock_config):
    """Create an ActionExecutor instance with mock config."""
    mock_input = MagicMock()
    return ActionExecutor(config_manager=mock_config, input_controller=mock_input)

@pytest.fixture
def mock_command():
    """Create a mock command object."""
    command = MagicMock()
    command.intent = "click"
    command.parameters = {}
    return command

@pytest.fixture
def mock_target_element():
    """Create a mock target element."""
    element = MagicMock()
    element.center = (100, 100)
    return element 