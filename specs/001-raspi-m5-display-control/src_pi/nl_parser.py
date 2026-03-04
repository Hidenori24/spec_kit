"""
Natural Language Parser for Display Commands

Translates Japanese natural language instructions to M5Stick commands.
Uses keyword dictionaries for color, position, and size extraction.

Author: spec_kit implementation
Date: 2026-03-04
"""

from typing import Tuple, Dict, Any
import re


class NLParser:
    """
    Natural language parser for display commands.
    
    Translates instructions like "赤い円を中央に" to command parameters.
    """
    
    # Color keyword dictionary (RGB565)
    COLOR_DICT = {
        "赤": 0xF800,
        "青": 0x001F,
        "緑": 0x07E0,
        "黄": 0xFFE0,
        "黄色": 0xFFE0,
        "白": 0xFFFF,
        "黒": 0x0000,
        "紫": 0xF81F,
        "茶": 0x8410,
        "グレー": 0x8410,
        "灰色": 0x8410,
        "オレンジ": 0xFC00,
        "ピンク": 0xF81F,
    }
    
    # Position keyword dictionary (x, y coordinates for 135x240 screen)
    POSITION_DICT = {
        "中央": (67, 120),
        "中心": (67, 120),
        "左上": (10, 10),
        "右下": (125, 230),
        "右上": (125, 10),
        "左下": (10, 230),
        "上": (67, 40),
        "下": (67, 200),
        "左": (20, 120),
        "右": (115, 120),
    }
    
    # Size keyword dictionary (radius for circles, default size for rects)
    SIZE_DICT = {
        "大きい": 40,
        "大": 40,
        "中": 25,
        "小さい": 15,
        "小": 15,
        "超大きい": 50,
        "極小": 10,
    }
    
    # Command type keywords
    COMMAND_KEYWORDS = {
        "DRAW_CIRCLE": {
            "primary": ["円", "丸", "サークル"],
            "secondary": ["描く", "描画"],
        },
        "DRAW_RECT": {
            "primary": ["矩形", "四角", "長方形", "正方形", "□"],
            "secondary": ["描く", "描画"],
        },
        "DRAW_TEXT": {
            "primary": ["テキスト", "文字", "文"],
            "secondary": ["描く", "書く", "表示"],
        },
        "CLEAR_SCREEN": {
            "primary": ["消す", "クリア", "リセット", "削除"],
            "secondary": ["画面", "全部"],
        },
    }
    
    def parse(self, instruction: str) -> Tuple[str, Dict[str, Any]]:
        """
        Parse natural language instruction.
        
        Args:
            instruction: Natural language string (Japanese)
            
        Returns:
            Tuple of (command_type: str, params: dict)
            
        Raises:
            ValueError: If command cannot be recognized
        """
        # Tokenize
        tokens = self._tokenize(instruction)
        
        # Detect command type
        cmd_type = self._detect_command(tokens)
        
        # Extract parameters based on command type
        params = {}
        
        if cmd_type == "DRAW_CIRCLE":
            params = self._extract_circle_params(tokens, instruction)
        elif cmd_type == "DRAW_RECT":
            params = self._extract_rect_params(tokens, instruction)
        elif cmd_type == "DRAW_TEXT":
            params = self._extract_text_params(tokens, instruction)
        elif cmd_type == "CLEAR_SCREEN":
            params = {}
        else:
            raise ValueError(f"Unsupported command type: {cmd_type}")
        
        return cmd_type, params
    
    def _tokenize(self, text: str) -> list:
        """
        Tokenize Japanese text into words.
        
        Args:
            text: Input text
            
        Returns:
            List of tokens
        """
        # Simple tokenization: split by common delimiters
        tokens = []
        current = ""
        
        for char in text:
            if char in "、。！？ 　":
                if current:
                    tokens.append(current)
                    current = ""
            else:
                current += char
        
        if current:
            tokens.append(current)
        
        return tokens
    
    def _detect_command(self, tokens: list) -> str:
        """
        Detect command type from tokens.
        
        Args:
            tokens: List of tokens
            
        Returns:
            Command type string
            
        Raises:
            ValueError: If command not recognized
        """
        # Try primary keywords first
        for cmd_type, keywords in self.COMMAND_KEYWORDS.items():
            for token in tokens:
                for primary_kw in keywords["primary"]:
                    if primary_kw in token:
                        return cmd_type
        
        # Try secondary keywords
        for cmd_type, keywords in self.COMMAND_KEYWORDS.items():
            for token in tokens:
                for secondary_kw in keywords["secondary"]:
                    if secondary_kw in token:
                        return cmd_type
        
        raise ValueError("Command not recognized")
    
    def _extract_circle_params(self, tokens: list, instruction: str) -> Dict[str, Any]:
        """Extract parameters for DRAW_CIRCLE command"""
        params = {}
        
        # Extract color
        params["color"] = self._extract_color(tokens)
        
        # Extract position
        x, y = self._extract_position(tokens)
        params["x"] = x
        params["y"] = y
        
        # Extract size (radius)
        params["radius"] = self._extract_size(tokens)
        
        return params
    
    def _extract_rect_params(self, tokens: list, instruction: str) -> Dict[str, Any]:
        """Extract parameters for DRAW_RECT command"""
        params = {}
        
        # Extract color
        params["color"] = self._extract_color(tokens)
        
        # Extract position
        x, y = self._extract_position(tokens)
        params["x"] = x
        params["y"] = y
        
        # Extract size
        size = self._extract_size(tokens)
        params["width"] = size * 2  # Width = 2 * radius
        params["height"] = int(size * 1.5)  # Height = 1.5 * radius
        
        return params
    
    def _extract_text_params(self, tokens: list, instruction: str) -> Dict[str, Any]:
        """Extract parameters for DRAW_TEXT command"""
        params = {}
        
        # Extract color
        params["color"] = self._extract_color(tokens)
        
        # Extract position
        x, y = self._extract_position(tokens)
        params["x"] = x
        params["y"] = y
        
        # Extract text content
        # Look for quoted text or default to "TEXT"
        text_match = re.search(r'[「『"\'](.*?)[」』"\']', instruction)
        if text_match:
            params["text"] = text_match.group(1)
        else:
            # Try to extract alphanumeric sequence
            alpha_match = re.search(r'[A-Za-z0-9]+', instruction)
            if alpha_match:
                params["text"] = alpha_match.group(0)
            else:
                params["text"] = "TEXT"
        
        return params
    
    def _extract_color(self, tokens: list) -> int:
        """
        Extract color from tokens.
        
        Returns:
            RGB565 color value (default: white 0xFFFF)
        """
        for token in tokens:
            for color_name, rgb565 in self.COLOR_DICT.items():
                if color_name in token:
                    return rgb565
        
        # Default: white
        return 0xFFFF
    
    def _extract_position(self, tokens: list) -> Tuple[int, int]:
        """
        Extract position from tokens.
        
        Returns:
            Tuple of (x, y) coordinates (default: center)
        """
        for token in tokens:
            for pos_name, (x, y) in self.POSITION_DICT.items():
                if pos_name in token:
                    return (x, y)
        
        # Default: center
        return (67, 120)
    
    def _extract_size(self, tokens: list) -> int:
        """
        Extract size from tokens.
        
        Returns:
            Size value (default: 25)
        """
        for token in tokens:
            for size_name, size in self.SIZE_DICT.items():
                if size_name in token:
                    return size
        
        # Try to extract numeric value
        for token in tokens:
            # Look for number pattern
            match = re.search(r'(\d+)', token)
            if match:
                return int(match.group(1))
        
        # Default: medium size
        return 25
