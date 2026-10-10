# Context Manager Domain

## Overview

The Context Manager domain maintains the application's state and history, enabling context-aware decision making and providing historical information for command interpretation and error recovery.

## Responsibilities

- Track command history
- Maintain application state
- Store execution results
- Manage variables
- Track error states
- Support context-aware operations
- Provide historical analysis

## Key Components

### ContextEvent Class
```python
@dataclass
class ContextEvent:
    timestamp: datetime
    event_type: str
    data: Dict[str, Any]
    success: bool = True
```

### Context Class
```python
@dataclass
class Context:
    events: List[ContextEvent]
    variables: Dict[str, Any]
    max_history: int = 100
    
    def add_event(self, event_type: str, data: Dict[str, Any], success: bool = True)
    def get_last_event(self, event_type: Optional[str] = None) -> Optional[ContextEvent]
    def get_events(self, event_type: Optional[str] = None, limit: Optional[int] = None)
```

### ContextManager Class
- Event recording
- State management
- History tracking
- Variable storage
- Context analysis

## Dependencies

- Configuration management
- Datetime handling
- JSON serialization
- Optional persistence layer

## Testing

The domain includes its own test suite in the `tests` directory:
```
context_manager/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Domain-specific test fixtures
│   ├── test_context.py       # Context operations tests
│   ├── test_events.py        # Event handling tests
│   └── test_history.py       # History management tests
```

## Usage Example

```python
context = ContextManager(config)

# Record a command event
context.add_command("click save button", parsed_command)

# Record an action
context.add_action("click", target="save_button", success=True)

# Get recent history
recent_commands = context.get_recent_commands(limit=5)

# Check last action
last_action = context.get_last_action()
```

## Extension Points

1. Event Types
   - Add new event categories
   - Define custom event data
   - Implement event analysis

2. State Management
   - Custom state tracking
   - Variable persistence
   - State restoration

3. History Analysis
   - Pattern detection
   - Usage statistics
   - Performance metrics

## For AI Agent Maintainers

This domain is maintained by the Context Agent. When contributing:

1. Maintain data consistency
2. Optimize memory usage
3. Consider persistence needs
4. Document state changes
5. Handle edge cases

## Shared Utilities

Common utilities are available in the `shared_utils` directory:
- Event handling
- State management
- Data serialization
- Time utilities

## Error Handling

The domain uses standardized error types:
- `ContextError`: Base context-related error
- `StateError`: Invalid state transitions
- `HistoryError`: History management issues
- `PersistenceError`: Storage/retrieval errors

## Configuration

Domain-specific configuration includes:
1. History limits
2. Event filtering
3. Persistence settings
4. Analysis parameters

## Performance Considerations

1. Memory Management
   - History pruning
   - Event filtering
   - Data compression

2. State Tracking
   - Efficient updates
   - Change detection
   - State validation

3. Analysis
   - Incremental processing
   - Cached results
   - Lazy evaluation

## Data Management

1. Event Storage
   - In-memory cache
   - Persistent storage
   - Data migration

2. State Persistence
   - Serialization
   - Recovery
   - Versioning

3. History Management
   - Rotation
   - Archival
   - Cleanup

## Analysis Features

1. Pattern Detection
   - Command sequences
   - Error patterns
   - Usage trends

2. Statistics
   - Success rates
   - Error frequencies
   - Performance metrics

3. Insights
   - Usage patterns
   - Optimization opportunities
   - Error predictions

## Integration Points

1. Command Parser
   - Command history
   - Intent analysis
   - Pattern learning

2. Action Executor
   - Action results
   - State changes
   - Performance data

3. Error Handler
   - Error context
   - Recovery history
   - Failure analysis 