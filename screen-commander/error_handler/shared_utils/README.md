# Shared Utilities

## Overview

This directory contains common utilities and helpers that are shared across all domains in the ScreenCommander project. Each domain has access to these utilities through a symbolic link in their own directory.

## Structure

```
shared_utils/
├── logging/              # Logging configuration and utilities
│   ├── __init__.py
│   ├── config.py        # Common logging setup
│   └── formatters.py    # Custom log formatters
├── testing/             # Common testing utilities
│   ├── __init__.py
│   ├── fixtures.py      # Shared test fixtures
│   └── mocks.py        # Common mock objects
├── types/               # Shared type definitions
│   ├── __init__.py
│   ├── commands.py     # Command-related types
│   └── elements.py     # UI element types
├── errors/             # Common error definitions
│   ├── __init__.py
│   └── exceptions.py   # Base exceptions
└── performance/        # Performance monitoring
    ├── __init__.py
    ├── profiler.py    # Performance profiling tools
    └── metrics.py     # Metrics collection
```

## Usage in Domains

Each domain should create a symbolic link to this directory:

```bash
# From domain directory (e.g., command_parser)
ln -s ../shared_utils shared_utils
```

Then import utilities as needed:

```python
from shared_utils.logging import setup_logger
from shared_utils.errors import BaseError
from shared_utils.types import CommandType
```

## Guidelines for Shared Utilities

1. Keep It Simple
   - Utilities should be focused and minimal
   - Avoid complex dependencies
   - Maintain backward compatibility

2. Documentation
   - Clear docstrings
   - Usage examples
   - Version history

3. Testing
   - Each utility must have tests
   - Test cross-domain compatibility
   - Performance benchmarks

4. Versioning
   - Semantic versioning
   - Deprecation notices
   - Migration guides

## Adding New Utilities

When adding new shared utilities:

1. Ensure the utility is truly common
2. Document thoroughly
3. Add comprehensive tests
4. Update all affected domains
5. Consider backward compatibility

## For AI Agent Maintainers

The shared utilities are maintained collectively by all domain agents. When contributing:

1. Coordinate changes with other agents
2. Test impact across all domains
3. Update documentation
4. Consider performance implications
5. Follow versioning guidelines

## Error Handling

Shared utilities use a common error hierarchy:
```python
class BaseError(Exception): pass
class ConfigError(BaseError): pass
class ValidationError(BaseError): pass
class ResourceError(BaseError): pass
```

## Testing

Shared utilities have their own test suite:
```
shared_utils/
├── tests/
│   ├── __init__.py
│   ├── test_logging.py
│   ├── test_types.py
│   └── test_performance.py
```

## Dependencies

- Core Python standard library
- Minimal external dependencies
- Version compatibility matrix

## Contributing

1. Discuss changes in issues
2. Create detailed PRs
3. Update documentation
4. Add/update tests
5. Consider all domains 