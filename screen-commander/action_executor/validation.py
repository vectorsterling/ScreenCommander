"""Validation and safety check functions for the Action Executor domain."""
import platform
from typing import Tuple, Optional
from errors import ValidationError, SafetyError

def validate_coordinates(x: int, y: int, screen_bounds: Optional[Tuple[int, int]] = None) -> None:
    """Validate that coordinates are within screen bounds.
    
    Args:
        x: X coordinate
        y: Y coordinate
        screen_bounds: Optional tuple of (width, height)
        
    Raises:
        ValidationError: If coordinates are invalid
    """
    if x < 0 or y < 0:
        raise ValidationError("Coordinates cannot be negative")
        
    if screen_bounds:
        width, height = screen_bounds
        if x >= width or y >= height:
            raise ValidationError(f"Coordinates ({x}, {y}) outside screen bounds ({width}x{height})")

def validate_text_input(text: str, max_length: int = 1000) -> None:
    """Validate text input parameters.
    
    Args:
        text: Text to validate
        max_length: Maximum allowed length
        
    Raises:
        ValidationError: If text is invalid
    """
    if not isinstance(text, str):
        raise ValidationError("Text must be a string")
        
    if not text:
        raise ValidationError("Text cannot be empty")
        
    if len(text) > max_length:
        raise ValidationError(f"Text exceeds maximum length of {max_length}")

def validate_platform() -> None:
    """Validate that the current platform is supported.
    
    Raises:
        PlatformError: If platform is not supported
    """
    system = platform.system().lower()
    if system not in ['darwin', 'linux', 'windows']:
        raise PlatformError(f"Unsupported platform: {system}")

def validate_safety_zone(x: int, y: int, safe_zones: list) -> None:
    """Validate that coordinates are within safe zones.
    
    Args:
        x: X coordinate
        y: Y coordinate
        safe_zones: List of (x1, y1, x2, y2) tuples defining safe zones
        
    Raises:
        SafetyError: If coordinates are outside safe zones
    """
    for zone in safe_zones:
        x1, y1, x2, y2 = zone
        if x1 <= x <= x2 and y1 <= y <= y2:
            return
            
    raise SafetyError(f"Coordinates ({x}, {y}) outside defined safe zones") 