import pytest
from command_parser.parser import Command, CommandParser

@pytest.mark.asyncio
async def test_click_command(command_parser):
    """Test parsing of click commands."""
    # Test basic click command
    command = await command_parser.parse("click the save button")
    assert command.intent == "click"
    assert command.target == "the save button"
    assert command.confidence >= 0.8
    
    # Test click command with no target
    command = await command_parser.parse("click")
    assert command.intent == "click"
    assert command.confidence >= 0.8

@pytest.mark.asyncio
async def test_scroll_command(command_parser):
    """Test parsing of scroll commands."""
    # Test scroll down command
    command = await command_parser.parse("scroll down")
    assert command.intent == "scroll"
    assert command.parameters["direction"] == "down"
    assert command.confidence >= 0.8
    
    # Test scroll up command
    command = await command_parser.parse("scroll up")
    assert command.intent == "scroll"
    assert command.parameters["direction"] == "up"
    assert command.confidence >= 0.8

@pytest.mark.asyncio
async def test_type_command(command_parser):
    """Test parsing of type commands."""
    # Test basic type command
    text = "Hello, World!"
    command = await command_parser.parse(f"type {text}")
    assert command.intent == "type"
    assert command.parameters["text"] == text
    assert command.confidence >= 0.8

@pytest.mark.asyncio
async def test_unknown_command(command_parser):
    """Test handling of unknown commands."""
    command = await command_parser.parse("do something invalid")
    assert command.intent == "unknown"
    assert command.confidence == 0.0

@pytest.mark.asyncio
async def test_complex_commands(command_parser):
    """Test parsing of more complex commands."""
    # Test command with multiple actions
    command = await command_parser.parse("click the button and type hello")
    assert command.intent in ["click", "type"]  # Should handle first action
    assert command.confidence >= 0.8
    
    # Test command with location
    command = await command_parser.parse("click the button at the top")
    assert command.intent == "click"
    assert "top" in command.target.lower()
    assert command.confidence >= 0.8 