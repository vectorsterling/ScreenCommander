# Screen Analyzer Domain

## Overview

The Screen Analyzer domain is responsible for analyzing screen content, identifying UI elements, and providing accurate targeting information for automated actions. It combines computer vision, OCR, and element detection to understand and interact with on-screen content.

## Responsibilities

- Screen capture and analysis
- UI element detection
- Text recognition (OCR)
- Element targeting
- Screen region tracking
- Visual state monitoring
- Element hierarchy mapping

## Key Components

### ScreenCapture Class
- High-performance screen capture
- Region-specific capture
- Multi-monitor support
- Image preprocessing

### ElementDetector Class
- UI element identification
- Bounding box detection
- Element classification
- Hierarchy analysis

### OCREngine Class
- Text recognition
- Language detection
- Text region analysis
- Confidence scoring

### TargetResolver Class
- Element location resolution
- Coordinate calculation
- Multi-target disambiguation
- Dynamic element tracking

## Dependencies

Required packages:
- `opencv-python`: Computer vision operations
- `pytesseract`: OCR functionality
- `numpy`: Image processing
- `mss`: Fast screen capture
- `pillow`: Image manipulation

## Testing

The domain includes comprehensive tests in the `tests` directory:
```
screen_analyzer/
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Test fixtures and mocks
│   ├── test_capture.py       # Screen capture tests
│   ├── test_detection.py     # Element detection tests
│   ├── test_ocr.py          # Text recognition tests
│   └── test_targeting.py     # Target resolution tests
```

## Usage Example

```python
analyzer = ScreenAnalyzer(config)

# Capture and analyze screen region
region = {"top": 0, "left": 0, "width": 800, "height": 600}
screen_data = analyzer.capture_region(region)

# Find UI element
element = analyzer.find_element(
    target="save button",
    element_type="button",
    confidence_threshold=0.8
)

# Extract text from region
text = analyzer.extract_text(region)

# Get element coordinates
coords = analyzer.resolve_target(element)
```

## Extension Points

1. Detection Methods
   - Custom element detectors
   - New recognition algorithms
   - Alternative OCR engines

2. Analysis Features
   - Custom element types
   - Advanced targeting strategies
   - Visual state tracking

3. Performance Optimizations
   - Caching mechanisms
   - Parallel processing
   - Hardware acceleration

## For AI Agent Maintainers

This domain is maintained by the Screen Analysis Agent. When contributing:

1. Optimize performance
2. Handle platform differences
3. Consider accessibility
4. Document detection patterns
5. Maintain test fixtures

## Shared Utilities

Common utilities from `shared_utils`:
- Image processing
- Performance monitoring
- Error handling
- Type definitions

## Error Handling

Standardized error types:
- `ScreenError`: Base screen analysis error
- `CaptureError`: Screen capture issues
- `DetectionError`: Element detection failures
- `OCRError`: Text recognition problems
- `TargetingError`: Location resolution errors

## Configuration

Domain settings include:
1. Capture parameters
2. Detection thresholds
3. OCR settings
4. Performance tuning
5. Platform-specific options

## Performance Considerations

1. Screen Capture
   - Efficient region capture
   - Image compression
   - Buffer management

2. Detection
   - Parallel processing
   - Result caching
   - Optimized algorithms

3. OCR
   - Language optimization
   - Region preprocessing
   - Confidence thresholds

## Platform Support

1. Windows
   - DirectX capture
   - Win32 API integration
   - DPI awareness

2. macOS
   - Core Graphics
   - Retina display support
   - Permission handling

3. Linux
   - X11 integration
   - Wayland support
   - Compositor handling

## Detection Features

1. Element Types
   - Buttons
   - Text fields
   - Icons
   - Windows
   - Menus
   - Custom elements

2. Recognition Methods
   - Template matching
   - Feature detection
   - Text recognition
   - Color analysis
   - Shape detection

3. Targeting Strategies
   - Center targeting
   - Edge targeting
   - Dynamic offset
   - Multi-point targeting

## Integration Points

1. Action Executor
   - Target coordinates
   - Element state
   - Interaction points

2. Context Manager
   - Screen state
   - Element history
   - Visual changes

3. Error Handler
   - Detection failures
   - Targeting issues
   - OCR errors 