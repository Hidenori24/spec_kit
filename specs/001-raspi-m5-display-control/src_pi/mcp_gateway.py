"""
MCP Gateway for M5StickC Plus2 Display Control

Main server that handles JSON-RPC requests from VS Code + GitHub Copilot
and translates them to serial commands for M5Stick.

Author: spec_kit implementation
Date: 2026-03-04
"""

import asyncio
import json
import sys
import time
import datetime
from typing import Dict, Any, Optional, Tuple

from serial_manager import SerialManager
from nl_parser import NLParser
from command_builder import CommandBuilder
from command_queue import CommandQueue
from history_manager import HistoryManager
from instruction_corrector import InstructionCorrector


class MCPGateway:
    """
    Main MCP Gateway server class.
    Handles JSON-RPC 2.0 requests via stdio and communicates with M5Stick.
    """
    
    def __init__(self, serial_port: str = "/dev/ttyUSB0", baud_rate: int = 115200):
        """
        Initialize MCP Gateway.
        
        Args:
            serial_port: Serial port path (default: /dev/ttyUSB0)
            baud_rate: Baud rate (default: 115200)
        """
        self.serial_manager = SerialManager(serial_port, baud_rate)
        self.nl_parser = NLParser()
        self.command_builder = CommandBuilder()
        self.command_queue = CommandQueue(max_size=10)
        self.history_manager = HistoryManager(max_size=100)
        self.corrector = InstructionCorrector()
        
        self.logger = self._setup_logger()
        self.running = False
    
    def _setup_logger(self):
        """Setup logging configuration"""
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler('/tmp/mcp_gateway.log'),
                logging.StreamHandler(sys.stderr)
            ]
        )
        return logging.getLogger(__name__)
    
    async def run(self):
        """
        Main event loop: read JSON-RPC from stdin, process, write to stdout.
        """
        self.logger.info("MCP Gateway starting...")
        
        # Initialize serial connection
        if not await self.serial_manager.init():
            self.logger.error("Failed to initialize serial manager")
            return
        
        # Ping device
        if not await self.serial_manager.ping():
            self.logger.warning("M5Stick not responding to PING")
        else:
            self.logger.info("M5Stick online")
        
        self.running = True
        self.logger.info("MCP Gateway ready")
        
        # Main loop: read from stdin
        while self.running:
            try:
                line = await asyncio.get_event_loop().run_in_executor(
                    None, sys.stdin.readline
                )
                
                if not line:
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                # Parse JSON-RPC request
                try:
                    request = json.loads(line)
                except json.JSONDecodeError as e:
                    response = self._error_response(
                        request_id=None,
                        code=-32700,
                        message="Parse error",
                        data=str(e)
                    )
                    self._write_response(response)
                    continue
                
                # Handle request
                response = await self.handle_request(request)
                self._write_response(response)
                
            except KeyboardInterrupt:
                self.logger.info("Received interrupt signal")
                break
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
        
        self.logger.info("MCP Gateway shutting down")
        await self.serial_manager.close()
    
    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle JSON-RPC request and return response.
        
        Args:
            request: JSON-RPC request dict
            
        Returns:
            JSON-RPC response dict
        """
        request_id = request.get("id")
        method = request.get("method")
        params = request.get("params", {})
        
        self.logger.info(f"Request: method={method}, id={request_id}")
        
        # Validate JSON-RPC 2.0
        if request.get("jsonrpc") != "2.0":
            return self._error_response(request_id, -32600, "Invalid Request")
        
        if not method:
            return self._error_response(request_id, -32600, "Invalid Request: method missing")
        
        # Dispatch method
        try:
            if method == "draw":
                result = await self.draw(params)
            elif method == "ping":
                result = await self.ping(params)
            elif method == "set_item":
                result = await self.set_item(params)
            elif method == "get_history":
                result = await self.get_history(params)
            else:
                return self._error_response(request_id, -32601, f"Method not found: {method}")
            
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result
            }
        
        except Exception as e:
            self.logger.error(f"Error handling {method}: {e}")
            return self._error_response(request_id, -32603, "Internal error", str(e))
    
    async def draw(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Draw method: translate natural language instruction to M5Stick command.
        
        Args:
            params: {"instruction": str, "timeout_ms": int (optional)}
            
        Returns:
            Result dict with status, message, duration, etc.
        """
        instruction = params.get("instruction")
        timeout_ms = params.get("timeout_ms", 5000)
        
        if not instruction:
            return {
                "status": "ER-PARAM",
                "message": "Missing instruction parameter",
                "duration_ms": 0,
                "timestamp": self._timestamp()
            }
        
        self.logger.info(f"Draw: instruction='{instruction}'")
        start_time = time.time()
        
        try:
            # Parse natural language
            cmd_type, cmd_params = self.nl_parser.parse(instruction)
            self.logger.debug(f"Parsed: type={cmd_type}, params={cmd_params}")
            
            # Correct parameters
            corrected_params = self.corrector.correct(instruction, cmd_type, cmd_params)
            if corrected_params != cmd_params:
                self.logger.info(f"Parameters auto-corrected: {cmd_params} -> {corrected_params}")
            
            # Build command bytes
            cmd_bytes = self.command_builder.build(cmd_type, corrected_params)
            self.logger.debug(f"Command bytes: {cmd_bytes.hex()}")
            
            # Enqueue (latest-first priority)
            self.command_queue.enqueue(cmd_bytes, instruction)
            
            # Dequeue latest
            latest_cmd = self.command_queue.dequeue_latest()
            if latest_cmd is None:
                return {
                    "status": "ER-BUSY",
                    "message": "Command queue empty",
                    "duration_ms": int((time.time() - start_time) * 1000),
                    "timestamp": self._timestamp()
                }
            
            # Send to M5Stick with timeout
            try:
                success, response_msg = await asyncio.wait_for(
                    self.serial_manager.send_command(latest_cmd["cmd"]),
                    timeout=timeout_ms / 1000
                )
            except asyncio.TimeoutError:
                success = False
                response_msg = "ER-TIMEOUT"
            
            duration_ms = int((time.time() - start_time) * 1000)
            
            # Add to history
            result_status = "OK" if success else response_msg
            self.history_manager.add(
                instruction=latest_cmd["instruction"],
                command=latest_cmd["cmd"].hex(),
                duration_ms=duration_ms,
                result=result_status
            )
            
            # Build response
            if success:
                message = "描画成功"
                if corrected_params != cmd_params:
                    message += " (パラメータ自動調整)"
            else:
                message = f"描画失敗: {response_msg}"
            
            return {
                "status": "OK" if success else result_status,
                "message": message,
                "command": latest_cmd["cmd"].hex(),
                "duration_ms": duration_ms,
                "timestamp": self._timestamp()
            }
        
        except ValueError as e:
            self.logger.warning(f"Parse error: {e}")
            return {
                "status": "ER-PARSE",
                "message": str(e),
                "duration_ms": int((time.time() - start_time) * 1000),
                "timestamp": self._timestamp()
            }
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return {
                "status": "ER-DEVICE",
                "message": f"Internal error: {str(e)}",
                "duration_ms": int((time.time() - start_time) * 1000),
                "timestamp": self._timestamp()
            }
    
    async def ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ping method: check M5Stick device status.
        
        Returns:
            Device status dict
        """
        self.logger.info("Ping")
        
        online = await self.serial_manager.ping()
        
        return {
            "status": "OK" if online else "ER-DEVICE",
            "device": "M5StickCPlus2",
            "firmware_version": "1.0.0",
            "online": online,
            "timestamp": self._timestamp()
        }
    
    async def set_item(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Set item method: switch display item (Phase 3).
        
        Args:
            params: {"item_id": int}
            
        Returns:
            Result dict
        """
        item_id = params.get("item_id")
        
        if item_id is None or not isinstance(item_id, int):
            return {
                "status": "ER-PARAM",
                "message": "Invalid item_id parameter",
                "timestamp": self._timestamp()
            }
        
        self.logger.info(f"Set item: id={item_id}")
        
        # Build SET_ITEM command
        cmd_bytes = self.command_builder.build_set_item(item_id)
        
        # Send to M5Stick
        success, response_msg = await self.serial_manager.send_command(cmd_bytes)
        
        return {
            "status": "OK" if success else response_msg,
            "message": "アイテム切り替え成功" if success else f"失敗: {response_msg}",
            "timestamp": self._timestamp()
        }
    
    async def get_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get history method: retrieve command execution history.
        
        Args:
            params: {"limit": int (optional, default 10)}
            
        Returns:
            History list
        """
        limit = params.get("limit", 10)
        
        self.logger.info(f"Get history: limit={limit}")
        
        history = self.history_manager.get_history(limit)
        
        return {
            "status": "OK",
            "history": history,
            "timestamp": self._timestamp()
        }
    
    def _error_response(self, request_id: Optional[int], code: int, 
                       message: str, data: Any = None) -> Dict[str, Any]:
        """Generate JSON-RPC error response"""
        error = {
            "code": code,
            "message": message
        }
        if data is not None:
            error["data"] = data
        
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": error
        }
    
    def _write_response(self, response: Dict[str, Any]):
        """Write JSON-RPC response to stdout"""
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()
    
    def _timestamp(self) -> str:
        """Generate ISO 8601 timestamp"""
        return datetime.datetime.utcnow().isoformat() + "Z"


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="MCP Gateway for M5StickC Plus2")
    parser.add_argument("--port", default="/dev/ttyUSB0", help="Serial port")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    
    args = parser.parse_args()
    
    gateway = MCPGateway(serial_port=args.port, baud_rate=args.baud)
    
    try:
        asyncio.run(gateway.run())
    except KeyboardInterrupt:
        print("\nShutdown requested", file=sys.stderr)
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
