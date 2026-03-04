# UML 状態遷移図

**Task**: T018  
**Status**: Draft  
**Last Updated**: 2026-03-04

---

## 1. ファームウェア全体状態遷移図

```mermaid
stateDiagram-v2
    [*] --> INIT
    
    INIT --> IDLE: [Boot complete]
    
    IDLE --> RX_BUFFERING: [Serial data available]
    
    RX_BUFFERING --> RX_BUFFERING: [Byte received]
    RX_BUFFERING --> FRAME_CHECK: [Frame delimiter detected (0xNN\r\n)]
    RX_BUFFERING --> TIMEOUT: [5s timeout]
    
    FRAME_CHECK --> CRC_VALIDATE: [Frame length valid]
    FRAME_CHECK --> ERROR_MALFORMED: [Invalid length]
    
    CRC_VALIDATE --> PARSE_COMMAND: [CRC OK]
    CRC_VALIDATE --> ERROR_MALFORMED: [CRC Error]
    
    PARSE_COMMAND --> VALIDATE_PARAMS: [Command recognized]
    PARSE_COMMAND --> ERROR_PARSE: [Unknown command]
    
    VALIDATE_PARAMS --> EXECUTE: [All params valid]
    VALIDATE_PARAMS --> ERROR_PARAM: [Out of range]
    VALIDATE_PARAMS --> ERROR_SIZE: [VRAM exceeded]
    
    EXECUTE --> EXECUTE_DRAW: [DRAW_* command]
    EXECUTE --> EXECUTE_SET: [SET_ITEM command]
    EXECUTE --> EXECUTE_PING: [PING command]
    EXECUTE --> EXECUTE_CLEAR: [CLEAR_SCREEN]
    
    EXECUTE_DRAW --> SEND_OK: [Success]
    EXECUTE_DRAW --> ERROR_DEVICE: [LCD error]
    EXECUTE_DRAW --> TIMEOUT: [Execution timeout]
    
    EXECUTE_SET --> SEND_OK: [Item found]
    EXECUTE_SET --> ERROR_NOTFOUND: [Item ID invalid]
    
    EXECUTE_PING --> SEND_PONG: [Device ready]
    EXECUTE_CLEAR --> SEND_OK: [Success]
    
    SEND_OK --> TX_RESPONSE
    SEND_PONG --> TX_RESPONSE
    
    ERROR_PARSE --> TX_ERROR
    ERROR_PARAM --> TX_ERROR
    ERROR_SIZE --> TX_ERROR
    ERROR_MALFORMED --> TX_ERROR
    ERROR_NOTFOUND --> TX_ERROR
    ERROR_DEVICE --> TX_ERROR
    TIMEOUT --> TX_ERROR
    
    TX_ERROR --> IDLE
    TX_RESPONSE --> IDLE: [Response sent]
    
    IDLE --> [*]: [Power off]
```

---

## 2. 描画コマンド実行フロー (EXECUTE_DRAW)

```mermaid
stateDiagram-v2
    [*] --> PARSE_DRAW_TYPE
    
    PARSE_DRAW_TYPE --> DRAW_CIRCLE: [Type = 0x11]
    PARSE_DRAW_TYPE --> DRAW_RECT: [Type = 0x12]
    PARSE_DRAW_TYPE --> DRAW_TEXT: [Type = 0x13]
    
    DRAW_CIRCLE --> LCD_LOCK: [Acquire LCD]
    DRAW_RECT --> LCD_LOCK: [Acquire LCD]
    DRAW_TEXT --> LCD_LOCK: [Acquire LCD]
    
    LCD_LOCK --> RENDERING: [LCD locked]
    LCD_LOCK --> ERROR_BUSY: [LCD busy (retry)]
    
    RENDERING --> PIXEL_CALC: [Calculate region]
    PIXEL_CALC --> WRITE_PIXELS: [Write to buffer]
    WRITE_PIXELS --> FLUSH: [Flush to display]
    
    FLUSH --> LCD_UNLOCK: [Success]
    FLUSH --> ERROR_DEVICE: [HW error]
    
    LCD_UNLOCK --> [*]
    
    ERROR_BUSY --> [*]
    ERROR_DEVICE --> [*]
```

---

## 3. シリアル通信状態遷移図

```mermaid
stateDiagram-v2
    [*] --> SERIAL_INIT
    
    SERIAL_INIT --> SERIAL_IDLE: [Baud rate configured]
    
    SERIAL_IDLE --> RX_WAIT: [ISR enabled]
    
    RX_WAIT --> RX_BUFFER: [Byte received]
    RX_BUFFER --> RX_BUFFER: [More bytes]
    RX_BUFFER --> FRAME_COMPLETE: [Delimiter detected]
    
    FRAME_COMPLETE --> QUEUE_COMMAND: [Frame valid]
    FRAME_COMPLETE --> DISCARD: [Frame invalid (timeout)]
    
    DISCARD --> RX_WAIT: [Ready for next]
    
    QUEUE_COMMAND --> QUEUE_OK: [Enqueued]
    QUEUE_COMMAND --> QUEUE_FULL: [Buffer overflow]
    
    QUEUE_OK --> RX_WAIT
    QUEUE_FULL --> ERROR_BUSY: [Return ER-BUSY]
    ERROR_BUSY --> RX_WAIT
    
    RX_WAIT --> [*]: [Power off]
```

---

## 4. クラス図 (構造)

```mermaid
classDiagram
    class SerialHandler {
        -rxBuffer: uint8_t[256]
        -txBuffer: uint8_t[256]
        -bufferIndex: uint16_t
        
        +init() void
        +handleRxInterrupt() void
        +sendResponse(Result) void
        -calculateCRC16(uint8_t*, uint16_t) uint16_t
    }
    
    class CommandParser {
        +parse(uint8_t*, uint16_t): Command
        +validate(Command): bool
        +encode(Result): uint8_t*
        -tokenize(uint8_t*): Token[]
    }
    
    class DrawingEngine {
        -activeItem: uint8_t
        -vramUsed: uint32_t
        
        +drawCircle(x, y, r, color): Result
        +drawRect(x, y, w, h, color): Result
        +drawText(x, y, text, color): Result
        +clearScreen(): Result
        +setActiveItem(id): Result
        -validateBounds(x, y, w, h): bool
        -validateVRAM(bytes): bool
    }
    
    class Command {
        +type: uint8_t
        +params: uint8_t[]
        +paramsLen: uint16_t
        +crc: uint16_t
    }
    
    class Result {
        +status: uint8_t [OK=0x00, ER-xxx=0xE0-0xE7]
        +message: char*
        +duration_ms: uint16_t
        +crc: uint16_t
    }
    
    class M5StickCDisplay {
        +drawCircle(x, y, r, color) void
        +drawRect(x, y, w, h, color) void
        +drawString(x, y, str, color) void
        +fillScreen(color) void
    }
    
    SerialHandler --> CommandParser: [uses]
    CommandParser --> Command: [creates]
    DrawingEngine --> Result: [produces]
    DrawingEngine --> M5StickCDisplay: [uses]
    Command --> DrawingEngine: [triggers]
```

---

## 5. シーケンス図（正常系）

```mermaid
sequenceDiagram
    participant Pi as Raspberry Pi
    participant FW as M5Stick<br/>Firmware
    participant Display as M5Stick<br/>Display
    
    Pi ->> FW: DRAW_CIRCLE (0x11)<br/>[x=160, y=120, r=32, color=0xF800]
    activate FW
    
    FW ->> FW: Parse command
    FW ->> FW: Validate parameters
    FW ->> FW: Reserve VRAM
    
    FW ->> Display: Acquire LCD lock
    activate Display
    
    FW ->> Display: Calculate pixels
    FW ->> Display: Write to buffer
    FW ->> Display: Flush to TFT
    
    Display -->> FW: Done (150ms)
    deactivate Display
    
    FW ->> FW: Release VRAM
    FW ->> Pi: OK (status=0x00)
    deactivate FW
```

---

## 6. シーケンス図（エラー系：タイムアウト）

```mermaid
sequenceDiagram
    participant Pi as Raspberry Pi
    participant FW as M5Stick<br/>Firmware
    participant Display as M5Stick<br/>Display
    
    Pi ->> FW: DRAW_RECT<br/>(large, complex)
    activate FW
    
    FW ->> FW: Parse, validate
    FW ->> Display: Acquire LCD
    activate Display
    
    FW ->> Display: Write pixels (loop)
    Note over FW,Display: 5000ms timeout<br/>triggered
    
    Display --X FW: No response
    deactivate Display
    
    FW ->> FW: Error handling:<br/>Release resources
    FW ->> Pi: ER-TIMEOUT<br/>(status=0xE4)
    deactivate FW
    
    Note over Pi: Retry strategy:<br/>PING check → retry or reset
```

---

## 7. シーケンス図（エラー系：CRC エラー）

```mermaid
sequenceDiagram
    participant Pi as Raspberry Pi
    participant FW as M5Stick<br/>Firmware
    
    Pi ->> FW: Frame (corrupted:<br/>CRC mismatch)
    activate FW
    
    FW ->> FW: Receive + buffer
    FW ->> FW: CRC check
    Note over FW: CRC validation<br/>FAILED
    
    FW ->> Pi: ER-MALFORMED<br/>(status=0xE5)
    deactivate FW
    
    Note over Pi: Retry logic:<br/>clear buffer, resync
    Pi ->> FW: Frame (retry 1/3)
```

---

## 8. ステートマシン：責務分離

| モジュール | 責務 | 状態 |
|----------|------|------|
| **SerialHandler** | UART 割り込み, バッファ管理 | RX_WAIT → RX_BUFFER → FRAME_COMPLETE |
| **CommandParser** | フレーム解析, 妥当性チェック | PARSE → VALIDATE_PARAMS → EXECUTE |
| **DrawingEngine** | 画面描画, VRAM 管理 | LCD_LOCK → RENDERING → LCD_UNLOCK |
| **Main Loop** | 状態遷移の調整, 応答送信 | DISPATCH → ERROR_HDL → TX_RESPONSE → IDLE |

---

## 9. タイムライン（応答時間）

```
Timeline: DRAW_CIRCLE (5 秒 SLA)
─────────────────────────────────────────→ Time (ms)

[0]    Rx complete (Frame received)
 │
 ├─ [0-10]   Parse command
 ├─ [10-20]  Validate parameters
 ├─ [20-100] Reserve VRAM
 │           ↓
 ├─ [100-150] Execute drawing
 │   ├─ Acquire LCD lock (10ms)
 │   ├─ Calculate pixels (30ms)
 │   ├─ Write buffer (50ms)
 │   └─ Flush to display (50ms)
 │
 ├─ [150-160] Release resources
 │
 └─ [160-170] Send response Tx
             ↓
         [170] Response complete (✓ within 5000ms)
```

---

## 10. 変更履歴

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-04 | Initial draft (State, Class, Sequence diagrams) |

