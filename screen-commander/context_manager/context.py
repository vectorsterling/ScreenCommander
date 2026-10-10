from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ContextEvent:
    """Represents a single event in the context history."""
    
    timestamp: datetime
    event_type: str
    data: Dict[str, Any]
    success: bool = True
    
    def __post_init__(self):
        """Ensure timestamp is a datetime object."""
        if isinstance(self.timestamp, str):
            self.timestamp = datetime.fromisoformat(self.timestamp)

@dataclass
class Context:
    """Maintains the current state and history of interactions."""
    
    events: List[ContextEvent] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    max_history: int = 100
    
    def add_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        success: bool = True
    ) -> None:
        """Add a new event to the context history.
        
        Args:
            event_type: Type of event (command, action, error, etc.)
            data: Event-specific data
            success: Whether the event was successful
        """
        event = ContextEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            data=data,
            success=success
        )
        
        self.events.append(event)
        
        # Maintain maximum history size
        if len(self.events) > self.max_history:
            self.events = self.events[-self.max_history:]
    
    def get_last_event(
        self,
        event_type: Optional[str] = None
    ) -> Optional[ContextEvent]:
        """Get the most recent event of the specified type.
        
        Args:
            event_type: Type of event to find (or any if None)
            
        Returns:
            The most recent matching event, or None if not found
        """
        for event in reversed(self.events):
            if not event_type or event.event_type == event_type:
                return event
        return None
    
    def get_events(
        self,
        event_type: Optional[str] = None,
        limit: Optional[int] = None,
        success_only: bool = False
    ) -> List[ContextEvent]:
        """Get events matching the specified criteria.
        
        Args:
            event_type: Type of events to find (or any if None)
            limit: Maximum number of events to return
            success_only: Whether to only return successful events
            
        Returns:
            List of matching events
        """
        events = []
        
        for event in reversed(self.events):
            if event_type and event.event_type != event_type:
                continue
                
            if success_only and not event.success:
                continue
                
            events.append(event)
            
            if limit and len(events) >= limit:
                break
                
        return list(reversed(events))
    
    def set_variable(self, key: str, value: Any) -> None:
        """Set a context variable.
        
        Args:
            key: Variable name
            value: Variable value
        """
        self.variables[key] = value
    
    def get_variable(self, key: str, default: Any = None) -> Any:
        """Get a context variable.
        
        Args:
            key: Variable name
            default: Default value if not found
            
        Returns:
            Variable value or default
        """
        return self.variables.get(key, default)
    
    def clear_history(self) -> None:
        """Clear the event history."""
        self.events.clear()
    
    def clear_variables(self) -> None:
        """Clear all context variables."""
        self.variables.clear()

class ContextManager:
    """Manages application context and state."""
    
    def __init__(self, config_manager=None):
        """Initialize the context manager.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self.context = Context(
            max_history=config_manager.get("context.max_history", 100)
            if config_manager else 100
        )
    
    def add_command(self, command_text: str, parsed_command: Any) -> None:
        """Record a command event.
        
        Args:
            command_text: Original command text
            parsed_command: Parsed command object
        """
        self.context.add_event("command", {
            "text": command_text,
            "parsed": parsed_command
        })
    
    def add_action(self, action_type: str, target: Any, success: bool) -> None:
        """Record an action event.
        
        Args:
            action_type: Type of action performed
            target: Target of the action
            success: Whether the action was successful
        """
        self.context.add_event("action", {
            "type": action_type,
            "target": target
        }, success=success)
    
    def add_error(self, error_type: str, message: str) -> None:
        """Record an error event.
        
        Args:
            error_type: Type of error
            message: Error message
        """
        self.context.add_event("error", {
            "type": error_type,
            "message": message
        }, success=False)
    
    def get_recent_commands(self, limit: int = 5) -> List[ContextEvent]:
        """Get recent command events.
        
        Args:
            limit: Maximum number of commands to return
            
        Returns:
            List of recent command events
        """
        return self.context.get_events("command", limit=limit)
    
    def get_last_action(self) -> Optional[ContextEvent]:
        """Get the most recent action event.
        
        Returns:
            Most recent action event, or None if not found
        """
        return self.context.get_last_event("action")
    
    def clear(self) -> None:
        """Clear all context data."""
        self.context.clear_history()
        self.context.clear_variables()