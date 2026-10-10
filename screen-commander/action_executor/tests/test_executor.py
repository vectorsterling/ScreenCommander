"""Tests for the ActionExecutor class."""
import pytest
from unittest.mock import MagicMock, patch
from executor import ActionExecutor
from errors import ValidationError, InputError, ActionError


@pytest.mark.asyncio
async def test_execute_click_success(action_executor, mock_command, mock_target_element):
    with patch.object(action_executor.input, "click") as mock_click:
        result = await action_executor.execute(mock_command, mock_target_element)
        assert result is True
        mock_click.assert_called_once()


@pytest.mark.asyncio
async def test_execute_click_invalid_target(action_executor, mock_command):
    with pytest.raises(ValidationError):
        await action_executor.execute(mock_command, None)


@pytest.mark.asyncio
async def test_execute_type_success(action_executor):
    command = MagicMock()
    command.intent = "type"
    command.parameters = {"text": "Hello"}

    with patch.object(action_executor.input, "type_text") as mock_type:
        result = await action_executor.execute(command)
        assert result is True
        mock_type.assert_called_once_with("Hello")


@pytest.mark.asyncio
async def test_execute_type_invalid_text(action_executor):
    command = MagicMock()
    command.intent = "type"
    command.parameters = {"text": ""}

    with pytest.raises(ValidationError):
        await action_executor.execute(command)


@pytest.mark.asyncio
async def test_execute_scroll_success(action_executor):
    command = MagicMock()
    command.intent = "scroll"
    command.parameters = {"direction": "down"}

    with patch("executor.capture_screen") as mock_capture, patch.object(
        action_executor.input, "scroll"
    ) as mock_scroll:
        mock_capture.return_value.height = 900
        result = await action_executor.execute(command)
        assert result is True
        mock_scroll.assert_called_once()


@pytest.mark.asyncio
async def test_execute_scroll_invalid_direction(action_executor):
    command = MagicMock()
    command.intent = "scroll"
    command.parameters = {"direction": "invalid"}

    with pytest.raises(InputError):
        await action_executor.execute(command)


@pytest.mark.asyncio
async def test_execute_unsupported_intent(action_executor):
    command = MagicMock()
    command.intent = "unsupported"

    with pytest.raises(InputError):
        await action_executor.execute(command)
