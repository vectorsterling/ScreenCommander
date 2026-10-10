# Action Executor Domain

## Overview

The Action Executor domain is responsible for performing system-level actions based on parsed commands. It translates high-level commands into concrete mouse and keyboard operations, ensuring reliable and safe execution of user intentions.

## Responsibilities

- Execute mouse actions (clicks, movements, scrolling)
- Perform keyboard input (typing, shortcuts)
- Validate action safety and feasibility
- Handle platform-specific input methods
- Manage action timing and delays
- Provide execution feedback

## Key Components

### ActionExecutor Class
```python
class ActionExecutor:
    def __init__(self, config_manager=None):
        self.config = config_manager
        self.mouse = mouse.Controller()
        self.keyboard = keyboard.Controller()
        
    async def execute(self, command: Command, target_element=None) -> bool:
        """Execute a command with optional target element."""
```

### Supported Actions
- Click operations
- Text input
- Mouse movement
- Scrolling
- Keyboard shortcuts
- Drag and drop (planned)

## Dependencies

- `pynput`: Mouse and keyboard control
- `config_manager`: Configuration and settings
- `screen_analyzer`: Target element information
- Platform-specific input libraries

## Testing

The domain includes its own test suite in the `tests` directory:
```
action_executor/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Domain-specific test fixtures
│   ├── test_mouse.py        # Mouse action tests
│   ├── test_keyboard.py     # Keyboard action tests
│   └── test_validation.py   # Action validation tests
```

## Usage Example

```python
executor = ActionExecutor(config)

# Click operation
success = await executor.execute(
    Command(intent="click", target="save button"),
    target_element=screen_element
)

# Type operation
success = await executor.execute(
    Command(intent="type", parameters={"text": "Hello, World!"})
)
```

## Extension Points

1. Action Types
   - Add new action types
   - Implement custom input methods
   - Define action sequences

2. Platform Support
   - Add platform-specific implementations
   - Optimize for different environments
   - Handle special input methods

3. Safety Features
   - Input validation rules
   - Action restrictions
   - Safe zones

## For AI Agent Maintainers

This domain is maintained by the Executor Agent. When contributing:

1. Ensure action reliability
2. Consider platform differences
3. Implement safety checks
4. Optimize timing
5. Handle edge cases

## Shared Utilities

Common utilities are available in the `shared_utils` directory:
- Input validation
- Platform detection
- Safety checks
- Performance monitoring

## Error Handling

The domain uses standardized error types:
- `ActionError`: Base action execution error
- `InputError`: Invalid input parameters
- `PlatformError`: Platform-specific issues
- `SafetyError`: Safety check failures

## Configuration

Domain-specific configuration includes:
1. Input delays and timing
2. Safety thresholds
3. Platform-specific settings
4. Action restrictions

## Performance Considerations

1. Input Timing
   - Delay management
   - Action queuing
   - Rate limiting

2. Resource Usage
   - Input device access
   - System API calls
   - Event handling

3. Safety Checks
   - Pre-execution validation
   - Runtime monitoring
   - Post-execution verification

## Platform Support

The domain handles platform-specific input methods:
- Windows: Win32 API
- macOS: Quartz/CoreGraphics
- Linux: X11/Wayland

## Safety Guidelines

1. Action Validation
   - Verify target existence
   - Check coordinates
   - Validate input content

2. Execution Safety
   - Respect system restrictions
   - Handle permissions
   - Implement timeouts

3. Error Recovery
   - Graceful failure
   - State restoration
   - User notification 