"""Custom error classes for the Action Executor domain."""

class ActionError(Exception):
    """Base class for all action execution errors."""
    pass

class InputError(ActionError):
    """Raised when input parameters are invalid."""
    pass

class PlatformError(ActionError):
    """Raised when platform-specific issues occur."""
    pass

class SafetyError(ActionError):
    """Raised when safety checks fail."""
    pass

class ValidationError(ActionError):
    """Raised when action validation fails."""
    pass

class ExecutionError(ActionError):
    """Raised when action execution fails."""
    pass 