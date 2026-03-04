"""
History Manager with Ring Buffer

Implements FR-012: Ring buffer for storing the last 100 command executions.

Author: spec_kit implementation
Date: 2026-03-04
"""

from collections import deque
from typing import List, Dict, Any
import datetime
import logging


class HistoryManager:
    """
    Manages command execution history with a ring buffer.
    
    Stores the last N executions (default: 100).
    """
    
    def __init__(self, max_size: int = 100):
        """
        Initialize history manager.
        
        Args:
            max_size: Maximum history size (default: 100)
        """
        self.history = deque(maxlen=max_size)
        self.max_size = max_size
        self.logger = logging.getLogger(__name__)
    
    def add(self, instruction: str, command: str, duration_ms: int, result: str):
        """
        Add a command execution record to history.
        
        Args:
            instruction: Original natural language instruction
            command: Executed command (hex string)
            duration_ms: Execution duration in milliseconds
            result: Result status (OK, ER-xxx)
        """
        record = {
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "instruction": instruction,
            "command": command,
            "duration_ms": duration_ms,
            "result": result
        }
        
        self.history.append(record)
        
        self.logger.debug(f"History added: {instruction} -> {result} ({duration_ms}ms)")
    
    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieve the last N history records.
        
        Args:
            limit: Number of records to retrieve (default: 10)
            
        Returns:
            List of history records (most recent first)
        """
        # Return last 'limit' items in reverse order (newest first)
        return list(self.history)[-limit:][::-1]
    
    def get_all(self) -> List[Dict[str, Any]]:
        """
        Get all history records.
        
        Returns:
            List of all history records
        """
        return list(self.history)
    
    def clear(self):
        """Clear all history"""
        self.history.clear()
        self.logger.info("History cleared")
    
    def size(self) -> int:
        """Get current history size"""
        return len(self.history)
