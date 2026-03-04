"""
Command Builder for M5StickC Plus2

Builds serializable command frames with CRC-16 checksum based on command type
and parameters.

Author: spec_kit implementation
Date: 2026-03-04
"""

import struct
from typing import Dict, Any


class CommandBuilder:
    """
    Builds serial command frames for M5Stick.
    
    Format: [Header(1B)] [CmdType(1B)] [ParamsLen(1B)] [Params(*)] [CRC16(2B)] [\r\n]
    """
    
    FRAME_HEADER = 0x01
    FRAME_DELIMITER = b'\r\n'
    
    # Command types
    CMD_DRAW_CIRCLE = 0x11
    CMD_DRAW_RECT = 0x12
    CMD_DRAW_TEXT = 0x13
    CMD_CLEAR_SCREEN = 0x14
    CMD_SET_ITEM = 0x15
    CMD_PING = 0x16
    
    def build(self, cmd_type: str, params: Dict[str, Any]) -> bytes:
        """
        Build command frame based on command type.
        
        Args:
            cmd_type: Command type string (e.g., "DRAW_CIRCLE")
            params: Parameter dictionary
            
        Returns:
            Complete command frame bytes
        """
        if cmd_type == "DRAW_CIRCLE":
            return self.build_draw_circle(
                params["x"], params["y"], params["radius"], params["color"]
            )
        elif cmd_type == "DRAW_RECT":
            return self.build_draw_rect(
                params["x"], params["y"], params["width"], params["height"], params["color"]
            )
        elif cmd_type == "DRAW_TEXT":
            return self.build_draw_text(
                params["x"], params["y"], params["text"], params["color"]
            )
        elif cmd_type == "CLEAR_SCREEN":
            return self.build_clear_screen()
        else:
            raise ValueError(f"Unknown command type: {cmd_type}")
    
    def build_draw_circle(self, x: int, y: int, radius: int, color: int) -> bytes:
        """
        Build DRAW_CIRCLE command.
        
        Format: [x(2B)] [y(2B)] [radius(1B)] [color(2B)]
        Total params: 7 bytes
        """
        params = struct.pack(">HHBHx", x, y, radius, color)  # +1 padding
        return self._frame(self.CMD_DRAW_CIRCLE, params[:7])
    
    def build_draw_rect(self, x: int, y: int, width: int, height: int, color: int) -> bytes:
        """
        Build DRAW_RECT command.
        
        Format: [x(2B)] [y(2B)] [width(2B)] [height(2B)] [color(2B)]
        Total params: 10 bytes
        """
        params = struct.pack(">HHHHH", x, y, width, height, color)
        return self._frame(self.CMD_DRAW_RECT, params)
    
    def build_draw_text(self, x: int, y: int, text: str, color: int) -> bytes:
        """
        Build DRAW_TEXT command.
        
        Format: [x(2B)] [y(2B)] [text(N bytes, null-terminated)] [color(2B)]
        """
        text_bytes = text.encode('utf-8')[:128]  # Max 128 bytes
        text_bytes += b'\x00'  # Null terminator
        
        params = struct.pack(">HH", x, y) + text_bytes + struct.pack(">H", color)
        return self._frame(self.CMD_DRAW_TEXT, params)
    
    def build_clear_screen(self) -> bytes:
        """
        Build CLEAR_SCREEN command.
        
        No parameters.
        """
        return self._frame(self.CMD_CLEAR_SCREEN, b'')
    
    def build_set_item(self, item_id: int) -> bytes:
        """
        Build SET_ITEM command.
        
        Format: [item_id(1B)]
        """
        params = bytes([item_id])
        return self._frame(self.CMD_SET_ITEM, params)
    
    def build_ping(self) -> bytes:
        """
        Build PING command.
        
        No parameters.
        """
        return self._frame(self.CMD_PING, b'')
    
    def _frame(self, cmd_type: int, params: bytes) -> bytes:
        """
        Construct complete frame with header, CRC, and delimiters.
        
        Args:
            cmd_type: Command type byte
            params: Parameter bytes
            
        Returns:
            Complete frame: [Header] [Type] [Len] [Params] [CRC16] [\r\n]
        """
        header = bytes([self.FRAME_HEADER])
        payload = header + bytes([cmd_type, len(params)]) + params
        
        # Calculate CRC-16
        crc = self._crc16(payload)
        crc_bytes = struct.pack(">H", crc)
        
        # Complete frame
        frame = payload + crc_bytes + self.FRAME_DELIMITER
        
        return frame
    
    @staticmethod
    def _crc16(data: bytes) -> int:
        """
        Calculate CCITT CRC-16.
        
        Args:
            data: Input bytes
            
        Returns:
            CRC-16 value
        """
        crc = 0xFFFF
        
        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                crc &= 0xFFFF
        
        return crc
