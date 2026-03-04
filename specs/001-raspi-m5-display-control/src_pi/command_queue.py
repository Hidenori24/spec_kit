"""
Command Queue with Latest-First Priority

Implements SC-006: When multiple commands arrive, only the latest is executed.

Author: spec_kit implementation
Date: 2026-03-04
"""

from collections import deque
from typing import Dict, Any, Optional
import logging


class CommandQueue:
    """
    Command queue that prioritizes the latest command.
    
    When multiple commands are queued, only the most recent is dequeued.
    """
    
    def __init__(self, max_size: int = 10):
        """
        Initialize command queue.
        
        Args:
            max_size: Maximum queue size (default: 10)
        """
        self.queue = deque(maxlen=max_size)
        self.max_size = max_size
        self.logger = logging.getLogger(__name__)
    
    def enqueue(self, cmd: bytes, instruction: str):
        """
        Add command to queue.
        
        Args:
            cmd: Command bytes
            instruction: Original instruction string
        """
        self.queue.append({
            "cmd": cmd,
            "instruction": instruction
        })
        
        self.logger.debug(f"Enqueued: {instruction} (queue size: {len(self.queue)})")
    
    def dequeue_latest(self) -> Optional[Dict[str, Any]]:
        """
        Dequeue the latest (most recent) command and discard older ones.
        
        Returns:
            Latest command dict or None if queue is empty
        """
        if not self.queue:
            return None
        
        # Get the latest command
        latest = self.queue.pop()
        
        # Discard all older commands
        discarded_count = len(self.queue)
        self.queue.clear()
        
        if discarded_count > 0:
            self.logger.info(f"Discarded {discarded_count} older commands (SC-006)")
        
        return latest
    
    def size(self) -> int:
        """Get current queue size"""
        return len(self.queue)
    
    def clear(self):
        """Clear all commands from queue"""
        self.queue.clear()
