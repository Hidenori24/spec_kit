"""
Serial Manager for M5StickC Plus2 Communication

Handles UART communication with M5Stick: send commands, receive responses,
timeout handling, retry logic, and CRC validation.

Author: spec_kit implementation
Date: 2026-03-04
"""

import asyncio
import serial
import threading
import time
from typing import Tuple, Optional
import logging


class SerialManager:
    """
    Serial communication manager for M5Stick.
    
    Handles frame transmission/reception with CRC-16 validation.
    """
    
    FRAME_HEADER = 0x01
    FRAME_DELIMITER_1 = 0x0D  # \r
    FRAME_DELIMITER_2 = 0x0A  # \n
    
    # Status codes (from firmware)
    STATUS_OK = 0x00
    STATUS_INFO = 0x10
    STATUS_ER_PARSE = 0xE0
    STATUS_ER_PARAM = 0xE1
    STATUS_ER_SIZE = 0xE2
    STATUS_ER_NOTFOUND = 0xE3
    STATUS_ER_TIMEOUT = 0xE4
    STATUS_ER_MALFORMED = 0xE5
    STATUS_ER_DEVICE = 0xE6
    STATUS_ER_BUSY = 0xE7
    
    STATUS_NAMES = {
        0x00: "OK",
        0x10: "INFO",
        0xE0: "ER-PARSE",
        0xE1: "ER-PARAM",
        0xE2: "ER-SIZE",
        0xE3: "ER-NOTFOUND",
        0xE4: "ER-TIMEOUT",
        0xE5: "ER-MALFORMED",
        0xE6: "ER-DEVICE",
        0xE7: "ER-BUSY",
    }
    
    def __init__(self, port: str, baud_rate: int, timeout: float = 5.0):
        """
        Initialize serial manager.
        
        Args:
            port: Serial port path (e.g., /dev/ttyUSB0)
            baud_rate: Baud rate (default: 115200)
            timeout: Read timeout in seconds (default: 5.0)
        """
        self.port = port
        self.baud_rate = baud_rate
        self.timeout = timeout
        self.serial: Optional[serial.Serial] = None
        self.lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        self.max_retries = 3
    
    async def init(self) -> bool:
        """
        Initialize serial connection.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.serial = serial.Serial(
                port=self.port,
                baudrate=self.baud_rate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=self.timeout
            )
            
            # Wait for device to stabilize
            await asyncio.sleep(0.1)
            
            self.logger.info(f"Serial initialized: {self.port} @ {self.baud_rate}")
            return True
        
        except serial.SerialException as e:
            self.logger.error(f"Failed to open serial port: {e}")
            return False
    
    async def close(self):
        """Close serial connection"""
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.logger.info("Serial connection closed")
    
    async def send_command(self, cmd_bytes: bytes, retries: int = 3) -> Tuple[bool, str]:
        """
        Send command to M5Stick and wait for response.
        
        Args:
            cmd_bytes: Command frame bytes (with CRC and delimiters)
            retries: Number of retry attempts (default: 3)
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        if not self.serial or not self.serial.is_open:
            return False, "ER-DEVICE: Serial not open"
        
        for attempt in range(retries):
            try:
                with self.lock:
                    # Clear input buffer
                    self.serial.reset_input_buffer()
                    
                    # Send command
                    self.serial.write(cmd_bytes)
                    self.serial.flush()
                    
                    self.logger.debug(f"Sent ({attempt+1}/{retries}): {cmd_bytes.hex()}")
                    
                    # Read response (blocking with timeout)
                    response = await asyncio.get_event_loop().run_in_executor(
                        None, self._read_response
                    )
                    
                    if response is None:
                        self.logger.warning(f"Timeout on attempt {attempt+1}/{retries}")
                        if attempt < retries - 1:
                            await asyncio.sleep(0.1)
                            continue
                        return False, "ER-TIMEOUT"
                    
                    self.logger.debug(f"Received: {response.hex()}")
                    
                    # Parse response
                    status_code, message = self._parse_response(response)
                    status_name = self.STATUS_NAMES.get(status_code, f"UNKNOWN-0x{status_code:02X}")
                    
                    # Check status
                    if status_code == self.STATUS_OK or status_code == self.STATUS_INFO:
                        return True, message or "OK"
                    elif status_code == self.STATUS_ER_MALFORMED and attempt < retries - 1:
                        # Retry on CRC error
                        self.logger.warning(f"CRC error, retrying ({attempt+1}/{retries})")
                        await asyncio.sleep(0.1)
                        continue
                    else:
                        return False, status_name
            
            except serial.SerialException as e:
                self.logger.error(f"Serial error: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(0.1)
                    continue
                return False, "ER-DEVICE"
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}")
                return False, f"ER-DEVICE: {str(e)}"
        
        return False, "ER-TIMEOUT"
    
    async def ping(self) -> bool:
        """
        Send PING to M5Stick to check if device is online.
        
        Returns:
            True if device responds, False otherwise
        """
        # Build PING command: [0x01] [0x16] [0x00] [CRC] [\r\n]
        from command_builder import CommandBuilder
        builder = CommandBuilder()
        ping_cmd = builder.build_ping()
        
        success, _ = await self.send_command(ping_cmd, retries=1)
        return success
    
    def _read_response(self) -> Optional[bytes]:
        """
        Read response frame from serial (blocking).
        
        Returns:
            Response bytes or None if timeout
        """
        try:
            # Read until \r\n delimiter
            response = self.serial.read_until(
                expected=bytes([self.FRAME_DELIMITER_1, self.FRAME_DELIMITER_2]),
                size=256
            )
            
            if not response or len(response) < 6:
                return None
            
            # Remove delimiters
            if response[-2:] == bytes([self.FRAME_DELIMITER_1, self.FRAME_DELIMITER_2]):
                response = response[:-2]
            
            return response
        
        except serial.SerialTimeoutException:
            return None
        except Exception as e:
            self.logger.error(f"Read error: {e}")
            return None
    
    def _parse_response(self, response: bytes) -> Tuple[int, str]:
        """
        Parse response frame.
        
        Format: [0x01] [status] [msg_len] [message] [CRC16]
        
        Args:
            response: Response bytes (without delimiters)
            
        Returns:
            Tuple of (status_code: int, message: str)
        """
        if len(response) < 5:  # Header + status + len + CRC(2)
            return self.STATUS_ER_MALFORMED, "Response too short"
        
        # Check header
        if response[0] != self.FRAME_HEADER:
            return self.STATUS_ER_MALFORMED, "Invalid header"
        
        status_code = response[1]
        msg_len = response[2]
        
        # Extract message
        if msg_len > 0:
            if len(response) < 3 + msg_len + 2:
                return self.STATUS_ER_MALFORMED, "Message length mismatch"
            
            message_bytes = response[3:3+msg_len]
            try:
                message = message_bytes.decode('utf-8')
            except UnicodeDecodeError:
                message = message_bytes.hex()
        else:
            message = ""
        
        # Verify CRC
        expected_crc_start = 3 + msg_len
        if len(response) < expected_crc_start + 2:
            return self.STATUS_ER_MALFORMED, "CRC missing"
        
        received_crc = (response[expected_crc_start] << 8) | response[expected_crc_start + 1]
        calculated_crc = self._calculate_crc16(response[:expected_crc_start])
        
        if received_crc != calculated_crc:
            self.logger.warning(f"CRC mismatch: received=0x{received_crc:04X}, calculated=0x{calculated_crc:04X}")
            return self.STATUS_ER_MALFORMED, "CRC error"
        
        return status_code, message
    
    @staticmethod
    def _calculate_crc16(data: bytes) -> int:
        """
        Calculate CCITT CRC-16.
        
        Args:
            data: Byte array
            
        Returns:
            CRC-16 value (16-bit)
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
