import cv2
import numpy as np
from PIL import Image
import pytesseract
from typing import List, Tuple, Optional

from screen_analyzer.capture import ScreenCaptureError, capture_screen

class ScreenElement:
    """Represents an element detected on the screen."""
    
    def __init__(
        self,
        element_type: str,
        bounds: Tuple[int, int, int, int],
        text: Optional[str] = None,
        confidence: float = 0.0
    ):
        """Initialize a screen element.
        
        Args:
            element_type: Type of element (button, text, input, etc.)
            bounds: (x1, y1, x2, y2) coordinates of element
            text: Text content of the element
            confidence: Confidence score of detection
        """
        self.element_type = element_type
        self.bounds = bounds
        self.text = text
        self.confidence = confidence
    
    @property
    def center(self) -> Tuple[int, int]:
        """Get the center coordinates of the element."""
        x1, y1, x2, y2 = self.bounds
        return ((x2 + x1) // 2, (y2 + y1) // 2)

class ScreenAnalyzer:
    """Analyzes screen content to detect and locate UI elements."""
    
    def __init__(self, config_manager=None):
        """Initialize the screen analyzer.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config = config_manager
        self._last_screenshot = None
        self._last_elements = []
    
    def capture_screen(self) -> Image.Image:
        """Capture the current screen state.
        
        Returns:
            PIL Image of the screen
        """
        try:
            image = capture_screen()
        except ScreenCaptureError as exc:
            raise RuntimeError(str(exc)) from exc
        self._last_screenshot = image
        return image
    
    def detect_elements(self, image: Image.Image) -> List[ScreenElement]:
        """Detect UI elements in the given image.
        
        Args:
            image: PIL Image to analyze
            
        Returns:
            List of detected ScreenElement objects
        """
        elements = []
        
        # Convert PIL Image to OpenCV format
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # TODO: Implement element detection using computer vision
        # This is a placeholder implementation
        
        # Perform OCR to detect text
        text_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
        
        for i in range(len(text_data['text'])):
            if int(text_data['conf'][i]) > 0:  # Filter low confidence results
                x = text_data['left'][i]
                y = text_data['top'][i]
                w = text_data['width'][i]
                h = text_data['height'][i]
                text = text_data['text'][i].strip()
                conf = float(text_data['conf'][i]) / 100.0
                
                if text:  # Only add elements with text
                    elements.append(ScreenElement(
                        element_type='text',
                        bounds=(x, y, x + w, y + h),
                        text=text,
                        confidence=conf
                    ))
        
        return elements
    
    def find_element(self, query: str) -> Optional[ScreenElement]:
        """Find a specific element on the screen.
        
        Args:
            query: Text or description to search for
            
        Returns:
            ScreenElement if found, None otherwise
        """
        # Capture current screen if needed
        if not self._last_screenshot:
            self._last_screenshot = self.capture_screen()
            self._last_elements = self.detect_elements(self._last_screenshot)
        
        # Search for element matching query
        query = query.lower()
        best_match = None
        best_score = 0.0
        
        for element in self._last_elements:
            if element.text and query in element.text.lower():
                score = element.confidence * (len(query) / len(element.text))
                if score > best_score:
                    best_match = element
                    best_score = score
        
        return best_match if best_score > 0.5 else None 