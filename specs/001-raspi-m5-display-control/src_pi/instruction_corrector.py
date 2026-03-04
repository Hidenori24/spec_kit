"""
Instruction Corrector for Parameter Auto-Correction

Implements FR-015: Auto-correction of ambiguous or out-of-range parameters.

Author: spec_kit implementation
Date: 2026-03-04
"""

from typing import Dict, Any
import logging


class InstructionCorrector:
    """
    Auto-corrects parameters that are out of bounds or ambiguous.
    
    Implements FR-015: Auto-correction strategy.
    """
    
    # Screen dimensions for M5StickC Plus2
    SCREEN_WIDTH = 135
    SCREEN_HEIGHT = 240
    
    # Parameter limits
    MAX_RADIUS = 120
    MIN_RADIUS = 1
    MAX_TEXT_LEN = 20
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def correct(self, instruction: str, cmd_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Correct parameters based on command type.
        
        Args:
            instruction: Original instruction (for logging)
            cmd_type: Command type
            params: Parameter dictionary
            
        Returns:
            Corrected parameter dictionary
        """
        corrected = params.copy()
        
        if cmd_type == "DRAW_CIRCLE":
            corrected = self._correct_circle_params(corrected)
        elif cmd_type == "DRAW_RECT":
            corrected = self._correct_rect_params(corrected)
        elif cmd_type == "DRAW_TEXT":
            corrected = self._correct_text_params(corrected)
        
        # Log corrections
        if corrected != params:
            self.logger.info(f"Auto-corrected: {params} -> {corrected}")
        
        return corrected
    
    def _correct_circle_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Correct DRAW_CIRCLE parameters"""
        corrected = params.copy()
        
        # Default values
        if "color" not in corrected:
            corrected["color"] = 0xFFFF  # White
        if "radius" not in corrected:
            corrected["radius"] = 25
        
        # Coordinate bounds: 0 to SCREEN_WIDTH-1, 0 to SCREEN_HEIGHT-1
        x = corrected.get("x", 67)
        y = corrected.get("y", 120)
        radius = corrected.get("radius", 25)
        
        corrected["x"] = max(0, min(self.SCREEN_WIDTH - 1, x))
        corrected["y"] = max(0, min(self.SCREEN_HEIGHT - 1, y))
        
        # Radius bounds
        corrected["radius"] = max(self.MIN_RADIUS, min(self.MAX_RADIUS, radius))
        
        # Ensure circle fits on screen
        if corrected["x"] + corrected["radius"] > self.SCREEN_WIDTH:
            corrected["radius"] = self.SCREEN_WIDTH - corrected["x"]
        if corrected["y"] + corrected["radius"] > self.SCREEN_HEIGHT:
            corrected["radius"] = self.SCREEN_HEIGHT - corrected["y"]
        
        corrected["radius"] = max(self.MIN_RADIUS, corrected["radius"])
        
        return corrected
    
    def _correct_rect_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Correct DRAW_RECT parameters"""
        corrected = params.copy()
        
        # Default values
        if "color" not in corrected:
            corrected["color"] = 0xFFFF
        if "width" not in corrected:
            corrected["width"] = 50
        if "height" not in corrected:
            corrected["height"] = 30
        
        x = corrected.get("x", 67)
        y = corrected.get("y", 120)
        w = corrected.get("width", 50)
        h = corrected.get("height", 30)
        
        # Coordinate bounds
        corrected["x"] = max(0, min(self.SCREEN_WIDTH - 1, x))
        corrected["y"] = max(0, min(self.SCREEN_HEIGHT - 1, y))
        
        # Size bounds: ensure rect fits on screen
        corrected["width"] = max(1, min(self.SCREEN_WIDTH - corrected["x"], w))
        corrected["height"] = max(1, min(self.SCREEN_HEIGHT - corrected["y"], h))
        
        return corrected
    
    def _correct_text_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Correct DRAW_TEXT parameters"""
        corrected = params.copy()
        
        # Default values
        if "color" not in corrected:
            corrected["color"] = 0xFFFF
        if "text" not in corrected:
            corrected["text"] = "TEXT"
        
        x = corrected.get("x", 67)
        y = corrected.get("y", 120)
        
        # Coordinate bounds (leave margin for text)
        corrected["x"] = max(0, min(self.SCREEN_WIDTH - 10, x))
        corrected["y"] = max(0, min(self.SCREEN_HEIGHT - 10, y))
        
        # Text length limit
        text = corrected.get("text", "TEXT")
        if len(text) > self.MAX_TEXT_LEN:
            corrected["text"] = text[:self.MAX_TEXT_LEN]
            self.logger.info(f"Text truncated to {self.MAX_TEXT_LEN} characters")
        
        return corrected
