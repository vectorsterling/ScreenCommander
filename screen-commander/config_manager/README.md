# Config Manager Domain

## Overview

The Config Manager domain handles configuration management across the ScreenCommander system. It provides centralized configuration handling, validation, and distribution to ensure consistent system behavior and easy maintenance.

## Responsibilities

- Configuration loading and parsing
- Environment management
- Configuration validation
- Dynamic updates
- Default value management
- Configuration distribution
- Security enforcement

## Key Components

### ConfigManager Class
- Configuration loading
- Environment handling
- Validation coordination
- Update management
- Security enforcement

### ConfigSchema Class
```python
@dataclass
class ConfigSchema:
    name: str
    version: str
    settings: Dict[str, ConfigSetting]
    validators: List[Callable]
    dependencies: List[str]
```

### ConfigSetting Class
```python
@dataclass
class ConfigSetting:
    key: str
    type: Type
    default: Any
    description: str
    validators: List[Callable]
    is_secret: bool = False
```

### ConfigValidator Class
- Schema validation
- Type checking
- Dependency validation
- Security validation
- Custom rules

## Dependencies

Required packages:
- `pyyaml`: YAML parsing
- `jsonschema`: Schema validation
- `python-dotenv`: Environment handling
- `cryptography`: Secret management
- Domain-specific types

## Testing

The domain includes comprehensive tests in the `tests` directory:
```
config_manager/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Test fixtures
│   ├── test_manager.py       # Core manager tests
│   ├── test_validation.py    # Validation tests
│   ├── test_security.py      # Security tests
│   └── test_updates.py       # Update tests
```

## Usage Example

```python
manager = ConfigManager()

# Load configuration
config = manager.load_config("app_config.yaml")

# Get configuration value
db_url = config.get("database.url")

# Update configuration
manager.update_setting("api.timeout", 30)

# Validate configuration
validation_result = manager.validate_config()

# Export configuration
manager.export_config("config_backup.yaml")
```

## Extension Points

1. Configuration Sources
   - Custom file formats
   - Remote sources
   - Dynamic providers

2. Validation Rules
   - Custom validators
   - Domain-specific rules
   - Security policies

3. Update Handlers
   - Custom handlers
   - Change notifications
   - Rollback strategies

## For AI Agent Maintainers

This domain is maintained by the Config Manager Agent. When contributing:

1. Document schema changes
2. Update validation rules
3. Maintain security policies
4. Test configuration paths
5. Consider dependencies

## Shared Utilities

Common utilities from `shared_utils`:
- YAML handling
- Type validation
- Security utilities
- Error handling

## Error Handling

Standardized error types:
- `ConfigError`: Base configuration error
- `ValidationError`: Schema validation issues
- `SecurityError`: Security policy violations
- `UpdateError`: Configuration update failures
- `SchemaError`: Schema definition issues

## Configuration

Domain settings include:
1. File locations
2. Schema versions
3. Validation rules
4. Security policies
5. Update policies

## Performance Considerations

1. Loading
   - Lazy loading
   - Caching
   - Partial updates

2. Validation
   - Incremental validation
   - Parallel validation
   - Cache invalidation

3. Distribution
   - Change notification
   - Update propagation
   - Consistency checks

## Security Features

1. Secret Management
   - Encryption
   - Access control
   - Audit logging

2. Validation
   - Input sanitization
   - Type safety
   - Permission checks

3. Updates
   - Change verification
   - Rollback support
   - Audit trail

## Schema Management

1. Versioning
   - Schema evolution
   - Migration support
   - Compatibility checks

2. Validation
   - Type checking
   - Dependency validation
   - Custom rules

3. Documentation
   - Schema docs
   - Change history
   - Usage examples

## Integration Points

1. All Domains
   - Configuration access
   - Update notifications
   - Validation hooks

2. Security
   - Access control
   - Secret management
   - Audit logging

3. Monitoring
   - Change tracking
   - Usage metrics
   - Error reporting

## File Formats

1. YAML Support
   - Schema definition
   - Configuration files
   - Export format

2. Environment Files
   - .env support
   - Variable mapping
   - Override handling

3. JSON Support
   - Schema format
   - API configuration
   - Export format

## Update Management

1. Change Detection
   - File monitoring
   - API updates
   - Manual changes

2. Distribution
   - Change notification
   - Update propagation
   - Consistency checks

3. Rollback
   - Version tracking
   - State restoration
   - Error recovery

## Documentation

1. Schema Documentation
   - Type definitions
   - Validation rules
   - Usage examples

2. Configuration Guide
   - Setup instructions
   - Best practices
   - Security guidelines

3. API Documentation
   - Method signatures
   - Usage examples
   - Error handling 