"""Common error types used across all domains."""

class BaseError(Exception):
    """Base class for all ScreenCommander errors."""
    
    def __init__(self, message: str, *args, **kwargs):
        self.message = message
        super().__init__(message, *args)

class ConfigError(BaseError):
    """Raised when there is a configuration-related error."""
    pass

class ValidationError(BaseError):
    """Raised when data validation fails."""
    pass

class ResourceError(BaseError):
    """Raised when there is a resource-related error (memory, disk, etc.)."""
    pass

class APIError(BaseError):
    """Raised when there is an error communicating with external APIs."""
    
    def __init__(self, message: str, service: str, *args, **kwargs):
        self.service = service
        super().__init__(f"{service}: {message}", *args)

class PermissionError(BaseError):
    """Raised when there are insufficient permissions."""
    pass

class TimeoutError(BaseError):
    """Raised when an operation times out."""
    
    def __init__(self, message: str, timeout: float, *args, **kwargs):
        self.timeout = timeout
        super().__init__(f"{message} (timeout: {timeout}s)", *args)

class StateError(BaseError):
    """Raised when an operation fails due to invalid state."""
    pass

# Domain-specific base errors
class CommandError(BaseError):
    """Base class for command-related errors."""
    pass

class ScreenError(BaseError):
    """Base class for screen analysis errors."""
    pass

class ActionError(BaseError):
    """Base class for action execution errors."""
    pass

class LLMError(BaseError):
    """Base class for LLM-related errors."""
    pass

class ContextError(BaseError):
    """Base class for context-related errors."""
    pass 