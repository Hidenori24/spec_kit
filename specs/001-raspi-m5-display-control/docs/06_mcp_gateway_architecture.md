# MCP ゲートウェイアーキテクチャ設計書

**Task**: T032  
**Status**: Draft  
**Last Updated**: 2026-03-04

---

## 1. 概要

Raspberry Pi 5 上で動作する MCP ゲートウェイのアーキテクチャ設計です。VS Code + GitHub Copilot からの JSON-RPC リクエストを受け取り、M5Stick への シリアルコマンドに翻訳・送信します。

**言語**: Python 3.10+  
**スタイル**: OOP (クラスベース設計)  
**依存関係**: pyserial, json, logging

---

## 2.全体アーキテクチャ図

```
┌────────────────────────────────────────────────────────┐
│ VS Code (Copilot)                                      │
│ "赤い円を中央に"                                        │
└──────────────┬─────────────────────────────────────────┘
               │ stdin/stdout (JSON-RPC)
               ↓
    ┌──────────────────────────────────┐
    │ MCP Gateway (src_pi/mcp_gateway.py)
    │ ┌──────────────────────────────┐ │
    │ │ MCPGateway (Main Server) │ │
    │ │ - JSON-RPC handler    │ │
    │ │ - Method dispatcher   │ │
    │ └──────────────────────────────┘ │
    │          ↓ ↓ ↓                  │
    │ ┌──────────────────────────────┐ │
    │ │ Handler modules:            │ │
    │ │ - NLParser (→ Command)      │ │
    │ │ - CommandBuilder            │ │
    │ │ - SerialManager             │ │
    │ │ - CommandQueue              │ │
    │ │ - HistoryManager            │ │
    │ │ - InstructionCorrector      │ │
    │ └──────────────────────────────┘ │
    └──────────────────────────────────┘
               │
               │ UART 115200
               ↓
    ┌──────────────────────────────────┐
    │ M5StickC Plus2 Firmware          │
    │ (serial_handler, drawing_engine) │
    └──────────────────────────────────┘
```

---

## 3. モジュール設計

### 3.1 MCPGateway (メインサーバー)

**責務**: JSON-RPC リクエスト受信、メソッドディスパッチ、応答送信

**メインメソッド**:
```python
class MCPGateway:
    def __init__(self, serial_port="/dev/ttyUSB0", baud_rate=115200):
        self.serial_manager = SerialManager(serial_port, baud_rate)
        self.nl_parser = NLParser()
        self.command_queue = CommandQueue()
        self.history_manager = HistoryManager()
        self.corrector = InstructionCorrector()
        
    async def run(self):
        """メインループ: stdin から JSON-RPC を受け取る"""
        while True:
            line = input()
            request = json.loads(line)
            response = await self.handle_request(request)
            print(json.dumps(response))
    
    async def handle_request(self, request: dict) -> dict:
        """JSON-RPC メソッド呼び出し"""
        method = request.get("method")
        params = request.get("params", {})
        
        if method == "draw":
            return await self.draw(params)
        elif method == "ping":
            return await self.ping(params)
        elif method == "set_item":
            return await self.set_item(params)
        elif method == "get_history":
            return await self.get_history(params)
        else:
            return self.error_response("Method not found")
```

---

### 3.2 NLParser (自然言語パーサー)

**責務**: 自然言語指示 → シリアルコマンド変換

**キーワード辞書**:
```python
KEYWORD_DICT = {
    "赤": 0xF800,        # RGB565 Red
    "青": 0x001F,        # Blue
    "緑": 0x07E0,        # Green
    "黄": 0xFFE0,        # Yellow
    "白": 0xFFFF,        # White
    "黒": 0x0000,        # Black
    
    "円": "DRAW_CIRCLE",
    "丸": "DRAW_CIRCLE",
    "矩形": "DRAW_RECT",
    "四角": "DRAW_RECT",
    "テキスト": "DRAW_TEXT",
    "文字": "DRAW_TEXT",
    "消す": "CLEAR_SCREEN",
    "クリア": "CLEAR_SCREEN",
}

POSITION_DICT = {
    "中央": (160, 120),
    "中心": (160, 120),
    "左上": (10, 10),
    "右下": (310, 230),
    "上": (160, 30),
    "下": (160, 210),
}
```

**コマンド生成ロジック**:
```python
class NLParser:
    def parse(self, instruction: str) -> tuple[str, dict]:
        """
        自然言語 → コマンド + パラメータ辞書
        例: "赤い円を中央に" → ("DRAW_CIRCLE", {"x": 160, "y": 120, "r": 32, "color": 0xF800})
        """
        tokens = self.tokenize(instruction)
        command_type = self.detect_command(tokens)
        params = self.extract_parameters(tokens, command_type)
        return command_type, params
    
    def detect_command(self, tokens: list[str]) -> str:
        """トークンからコマンド型を推測"""
        for token in tokens:
            if "円" in token or "丸" in token:
                return "DRAW_CIRCLE"
            elif "矩形" in token or "四角" in token:
                return "DRAW_RECT"
            elif "テキスト" in token or "文字" in token:
                return "DRAW_TEXT"
            elif "消す" in token or "クリア" in token:
                return "CLEAR_SCREEN"
        raise ValueError("Command not recognized")
```

---

### 3.3 CommandBuilder (コマンド構築)

**責務**: パラメータ辞書 → シリアルコマンド（バイト列）に変換

```python
class CommandBuilder:
    def build_draw_circle(self, x: int, y: int, radius: int, color: int) -> bytes:
        """
        DRAW_CIRCLE コマンド構築
        Format: [0x01] [0x11] [0x07] [x(2B)] [y(2B)] [r(1B)] [color(2B)] [CRC(2B)]
        """
        params = struct.pack(">HHBH", x, y, radius, color)
        return self._frame(0x11, params)
    
    def _frame(self, cmd_type: int, params: bytes) -> bytes:
        """フレーム構築 + CRC 計算"""
        header = bytes([0x01])
        payload = header + bytes([cmd_type, len(params)]) + params
        crc = self._crc16(payload)
        return payload + crc.to_bytes(2, byteorder='big') + b'\r\n'
    
    def _crc16(self, data: bytes) -> int:
        """CCITT CRC-16 計算"""
        crc = 0xFFFF
        for byte in data:
            crc ^= byte << 8
            for _ in range(8):
                crc = (crc << 1) ^ 0x1021 if crc & 0x8000 else (crc << 1)
                crc &= 0xFFFF
        return crc
```

---

### 3.4 SerialManager (シリアル通信)

**責務**: M5Stick との UART 通信（送受信、CRC チェック、リトライ）

```python
class SerialManager:
    def __init__(self, port: str, baud_rate: int):
        self.serial = serial.Serial(port, baud_rate, timeout=5)
        self.lock = threading.Lock()
    
    async def send_command(self, cmd: bytes) -> tuple[bool, str]:
        """
        コマンド送信 + 応答受信
        Return: (success, response_message)
        """
        with self.lock:
            self.serial.write(cmd)
            self.serial.flush()
            
            try:
                response = self.serial.read_until(b'\r\n')
                # パース: [0x01] [status] [len] [msg] [CRC] [\r\n]
                status = response[1]
                msg_len = response[2]
                msg = response[3:3+msg_len].decode('utf-8')
                
                return (status == 0x00), msg
            except serial.SerialTimeoutException:
                return False, "ER-TIMEOUT"
    
    async def ping(self) -> bool:
        """デバイス疎通確認"""
        cmd = self._build_ping()
        success, _ = await self.send_command(cmd)
        return success
```

---

### 3.5 CommandQueue (コマンドキュー)

**責務**: 複数のコマンド受信時、最新コマンド優先を実装（SC-006）

```python
class CommandQueue:
    def __init__(self, max_size: int = 10):
        self.queue = []
        self.max_size = max_size
    
    def enqueue(self, cmd: str, instruction: str):
        """コマンドをキューに追加"""
        self.queue.append({"cmd": cmd, "instruction": instruction})
        if len(self.queue) > self.max_size:
            self.queue.pop(0)
    
    def dequeue_latest(self) -> dict:
        """最新のコマンドを取得（古いコマンドは破棄）"""
        if self.queue:
            return self.queue.pop()
        return None
```

---

### 3.6 HistoryManager (履歴管理)

**責務**: リングバッファで最新 100 件の実行履歴を管理（FR-012）

```python
class HistoryManager:
    def __init__(self, max_size: int = 100):
        self.history = collections.deque(maxlen=max_size)
    
    def add(self, instruction: str, command: str, duration_ms: int, result: str):
        """履歴に追加"""
        self.history.append({
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "instruction": instruction,
            "command": command,
            "duration_ms": duration_ms,
            "result": result
        })
    
    def get_history(self, limit: int = 10) -> list:
        """最新 N 件を取得"""
        return list(self.history)[-limit:]
```

---

### 3.7 InstructionCorrector (自動補正)

**責務**: 曖昧な指示を自動補正（FR-015）

```python
class InstructionCorrector:
    def correct(self, instruction: str, parsed_cmd: str, params: dict) -> dict:
        """
        曖昧なパラメータを自動補正
        例: radius = 150 (超過) → radius = 120 (上限値に補正)
        """
        if parsed_cmd == "DRAW_CIRCLE":
            # 半径チェック
            if params.get("radius", 0) > 120:
                params["radius"] = 120
            if params.get("radius", 0) < 1:
                params["radius"] = 1
        
        if parsed_cmd in ["DRAW_CIRCLE", "DRAW_RECT"]:
            # 座標チェック
            x = params.get("x", 0)
            y = params.get("y", 0)
            if x >= 135:
                params["x"] = 134
            if y >= 240:
                params["y"] = 239
        
        return params
```

---

## 4. メソッド実装フロー

### `draw` メソッドの処理フロー

```
1. request → {"instruction": "赤い円を中央に"}
   
2. NLParser.parse()
   → ("DRAW_CIRCLE", {"x": 160, "y": 120, "r": 32, "color": 0xF800})

3. InstructionCorrector.correct()
   → (パラメータを検証・補正)

4. CommandBuilder.build_draw_circle()
   → bytes: [0x01] [0x11] [0x07] [x] [y] [r] [color] [CRC] [\r\n]

5. CommandQueue.enqueue()
   → キューに追加（複数指示は最新が優先）

6. SerialManager.send_command()
   → M5Stick に送信
   → 応答受信 [0x01] [status] [len] [msg] [CRC] [\r\n]

7. HistoryManager.add()
   → {"instruction": "赤い円を中央に", "command": "DRAW_CIRCLE ...", "result": "OK"}

8. return → JSON-RPC response
   {
     "status": "OK",
     "message": "描画成功",
     "duration_ms": 150,
     "timestamp": "2026-03-04T10:30:45Z"
   }
```

---

## 5. エラーハンドリング戦略

| シナリオ | 処理 |
|--------|------|
| **JSON パースエラー** | JSON-RPC error -32700 返却 |
| **メソッド不明** | JSON-RPC error -32601 返却 |
| **M5Stick タイムアウト** | ER-TIMEOUT 返却、リトライ（最大 3 回） |
| **シリアル不接続** | ER-DEVICE 返却、PING で再確認 |
| **パラメータ不正** | ER-PARAM 返却（自動補正可能な場合は補正） |
| **曖昧指示** | 自動補正 + INFO メッセージ (補正内容を返却) |

---

## 6. 非同期処理設計

```python
# asyncio を使用して非ブロッキング実装
async def draw(self, params: dict) -> dict:
    instruction = params.get("instruction")
    timeout_ms = params.get("timeout_ms", 5000)
    
    try:
        # パース (ブロッキング)
        cmd_type, cmd_params = self.nl_parser.parse(instruction)
        
        # 補正 (ブロッキング)
        cmd_params = self.corrector.correct(instruction, cmd_type, cmd_params)
        
        # コマンド構築 (ブロッキング)
        cmd_bytes = self.command_builder.build(cmd_type, cmd_params)
        
        # シリアル送信 (非同期、タイムアウト付き)
        start = time.time()
        success, response = await asyncio.wait_for(
            self.serial_manager.send_command(cmd_bytes),
            timeout=timeout_ms / 1000
        )
        duration_ms = int((time.time() - start) * 1000)
        
        # 履歴追加
        result_status = "OK" if success else response
        self.history_manager.add(instruction, str(cmd_bytes), duration_ms, result_status)
        
        return {
            "status": "OK" if success else result_status,
            "message": "描画成功" if success else response,
            "command": str(cmd_bytes),
            "duration_ms": duration_ms,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
        }
    
    except asyncio.TimeoutError:
        return {"status": "ER-TIMEOUT", "duration_ms": timeout_ms}
    except Exception as e:
        return {"status": "ER-PARSE", "message": str(e)}
```

---

## 7. テスト戦略

| テスト | 目的 |
|-------|------|
| **Unit Test** | NLParser, CommandBuilder, InstructionCorrector の正確性 |
| **Integration Test** | MCP ↔ M5Stick 通信フロー |
| **E2E Test** | Copilot ↔ MCP ↔ M5Stick 全体動作 |
| **Stress Test** | 複数指示同時送信、キュー満杯など |

---

## 8. 実装チェックリスト（Phase 2）

- [ ] MCPGateway クラス基本実装
- [ ] NLParser 実装（キーワード辞書、パラメータ抽出）
- [ ] CommandBuilder 実装（フレーム構築、CRC）
- [ ] SerialManager 実装（送受信、タイムアウト）
- [ ] CommandQueue 実装（最新優先）
- [ ] HistoryManager 実装（リングバッファ）
- [ ] InstructionCorrector 実装（自動補正ロジック）
- [ ] 非同期処理（asyncio）
- [ ] エラーハンドリング全体
- [ ] ユニットテスト
- [ ] 統合テスト

---

## 9. 変更履歴

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-04 | Initial gateway architecture design (T032) |

