# UML シーケンス図 - MCP フロー

**Task**: T034  
**Status**: Draft  
**Last Updated**: 2026-03-04

---

## 1. 全体シーケンス図

```mermaid
sequenceDiagram
    participant Copilot as GitHub Copilot<br/>(VS Code)
    participant MCP as MCP Gateway<br/>(Raspberry Pi)
    participant Parser as NL Parser +<br/>Command Builder
    participant Serial as Serial Manager
    participant M5 as M5StickC Plus2<br/>Firmware
    participant Display as LCD Display

    Copilot ->> MCP: "赤い円を中央に" (JSON-RPC)
    activate MCP
    
    MCP ->> Parser: draw(instruction, timeout=5000)
    activate Parser
    
    Parser ->> Parser: tokenize("赤い円を中央に")
    Note over Parser: ["赤い", "円を", "中央に"]
    
    Parser ->> Parser: detect_command() → DRAW_CIRCLE
    Parser ->> Parser: extract_color() → 0xF800 (赤)
    Parser ->> Parser: extract_position() → (67, 120) (中央)
    Parser ->> Parser: extract_size() → 25 (デフォルト)
    
    Parser ->> Parser: correct() - パラメータ補正
    Note over Parser: x=67, y=120, r=25, color=0xF800<br/>(すべて有効範囲)
    
    Parser ->> Parser: build_draw_circle() → バイト列
    Note over Parser: [0x01] [0x11] [0x07]<br/>[67][120][25][0xF800] [CRC] [\r\n]
    
    Parser -->> MCP: (DRAW_CIRCLE, {"x": 67, "y": 120, "r": 25, "color": 0xF800})
    deactivate Parser
    
    MCP ->> Serial: send_command(cmd_bytes)
    activate Serial
    
    Serial ->> M5: シリアル送信 (115200) [Frame]
    activate M5
    
    M5 ->> M5: Rx ISR: フレーム受信
    M5 ->> M5: CRC チェック → OK
    M5 ->> M5: コマンド型推定 → DRAW_CIRCLE
    M5 ->> M5: パラメータ解析
    M5 ->> M5: 境界チェック
    
    M5 ->> Display: LCD Lock 取得
    activate Display
    
    M5 ->> Display: drawCircle(67, 120, 25, 0xF800)
    Display ->> Display: ピクセル計算
    Display ->> Display: バッファ書き込み
    Display ->> Display: TFT フラッシュ
    Note over Display: 画面に赤い円が表示
    
    M5 ->> Display: LCD Lock 解放
    deactivate Display
    
    M5 ->> Serial: 応答フレーム送信
    Note over M5: [0x01] [0x00] [0x00] [CRC] [\r\n]
    deactivate M5
    
    Serial ->> Serial: フレーム受信 (150ms)
    Serial ->> Serial: ステータスパース → 0x00 (OK)
    Serial -->> MCP: (success=True, "OK")
    deactivate Serial
    
    MCP ->> MCP: HistoryManager.add()
    Note over MCP: {"timestamp": "2026-03-04T10:30:45Z",<br/>"instruction": "赤い円を中央に",<br/>"command": "DRAW_CIRCLE 67 120 25 F800",<br/>"duration_ms": 150,<br/>"result": "OK"}
    
    MCP ->> Copilot: JSON-RPC レスポンス<br/>{"status": "OK", "duration_ms": 150, ...}
    deactivate MCP
```

---

## 2. エラーケース: タイムアウト

```mermaid
sequenceDiagram
    participant Copilot
    participant MCP
    participant Parser
    participant Serial
    participant M5 as M5Stick<br/>(未応答)

    Copilot ->> MCP: "赤い円を描いて" (JSON-RPC)
    activate MCP
    
    MCP ->> Parser: parse()
    activate Parser
    Parser -->> MCP: DRAW_CIRCLE, params
    deactivate Parser
    
    MCP ->> Serial: send_command()
    activate Serial
    
    Serial ->> M5: シリアル送信
    activate M5
    Note over M5: ⚠️ M5Stick 未接続/故障
    M5 --X Serial: 応答なし
    
    Serial ->> Serial: await (timeout=5000ms)
    Note over Serial: 5000ms 経過
    
    Serial -->> MCP: (success=False, "ER-TIMEOUT")
    deactivate Serial
    deactivate M5
    
    MCP ->> MCP: リトライ判定
    Note over MCP: retry_count < 3 ?<br/>→ はい、リトライ
    
    MCP ->> Serial: send_command() [Retry 2/3]
    activate Serial
    Serial ->> M5: シリアル送信
    Note over M5: ⚠️ 依然未応答
    Serial -->> MCP: (success=False, "ER-TIMEOUT")
    deactivate Serial
    
    MCP ->> Serial: send_command() [Retry 3/3]
    activate Serial
    Serial ->> M5: シリアル送信
    Serial -->> MCP: (success=False, "ER-TIMEOUT")
    deactivate Serial
    
    MCP ->> MCP: 最終判定: ER-DEVICE
    Note over MCP: デバイス不応答<br/>ユーザーに通知
    
    MCP ->> Copilot: JSON-RPC レスポンス<br/>{"status": "ER-DEVICE",<br/>"message": "M5Stick に接続できません",<br/>"duration_ms": 5000}
    deactivate MCP
```

---

## 3. エラーケース: CRC エラー（フレーム破損）

```mermaid
sequenceDiagram
    participant MCP
    participant Serial
    participant M5

    MCP ->> Serial: send_command()
    activate Serial
    
    Serial ->> M5: シリアル送信 [Frame]
    activate M5
    Note over M5: ⚠️ ノイズ → 1 ビット反転
    
    M5 ->> M5: CRC チェック
    Note over M5: CRC 不一致！
    M5 ->> M5: フレーム破棄
    M5 ->> Serial: 応答フレーム送信
    Note over M5: [0x01] [0xE5] ... (ER-MALFORMED)
    deactivate M5
    
    Serial ->> Serial: フレーム受信
    Serial ->> Serial: ステータス解析 → 0xE5 (ER-MALFORMED)
    Serial -->> MCP: (success=False, "ER-MALFORMED")
    deactivate Serial
    
    MCP ->> Serial: リトライ [Retry 1/3]
    activate Serial
    Serial ->> M5: シリアル送信 [Frame] (再送)
    activate M5
    Note over M5: 正常受信
    M5 ->> M5: CRC チェック → OK
    M5 ->> M5: コマンド実行
    M5 ->> Serial: 応答: OK
    deactivate M5
    Serial -->> MCP: (success=True, "OK")
    deactivate Serial
    
    MCP ->> Copilot: JSON-RPC レスポンス → OK
```

---

## 4.複数指示：最新優先（SC-006）

```mermaid
sequenceDiagram
    participant User1 as Copilot①<br/>User A
    participant User2 as Copilot②<br/>User B
    participant MCP
    participant Queue as Command<br/>Queue
    participant Serial
    participant M5

    User1 ->> MCP: "赤い円" (ID=1, t=0ms)
    activate MCP
    MCP ->> Queue: enqueue("DRAW_CIRCLE", ...)
    Note over Queue: Queue: [1]
    
    User2 ->> MCP: "青い矩形" (ID=2, t=50ms)
    MCP ->> Queue: enqueue("DRAW_RECT", ...)
    Note over Queue: Queue: [1, 2]
    
    User1 ->> MCP: "黄色い テキスト" (ID=3, t=100ms)
    MCP ->> Queue: enqueue("DRAW_TEXT", ...)
    Note over Queue: Queue: [1, 2, 3]
    
    MCP ->> Queue: dequeue_latest()
    Note over Queue: 最新=3 を取得<br/>古い [1, 2] は破棄
    activate Queue
    Queue -->> MCP: Command #3 (DRAW_TEXT)
    deactivate Queue
    
    MCP ->> Serial: send_command(#3)
    activate Serial
    Serial ->> M5: DRAW_TEXT "テキスト" 黄
    activate M5
    M5 ->> M5: テキスト描画
    M5 ->> Serial: OK
    deactivate M5
    Serial -->> MCP: success
    deactivate Serial
    
    MCP ->> User1: レスポンス #1<br/>{"result": "SKIPPED"}
    MCP ->> User2: レスポンス #2<br/>{"result": "SKIPPED"}
    MCP ->> User2: レスポンス #3<br/>{"status": "OK", "duration_ms": 200}
    deactivate MCP
    
    Note over User1, M5: 結果: ユーザー B の指示（最新）のみが実行される
```

---

## 5. 自動補正フロー（FR-015）

```mermaid
sequenceDiagram
    participant User
    participant MCP
    participant Parser as NL Parser
    participant Corrector
    participant Serial
    participant M5

    User ->> MCP: "右下に超大きい円" (JSON-RPC)
    activate MCP
    
    MCP ->> Parser: parse()
    activate Parser
    
    Parser ->> Parser: detect_command() → DRAW_CIRCLE
    Parser ->> Parser: extract_position() → (125, 230)
    Note over Parser: ⚠️ 画面外！
    Parser ->> Parser: extract_size() → 100
    Note over Parser: ⚠️ 半径超過！
    
    Parser -->> MCP: (params with out-of-range values)
    deactivate Parser
    
    MCP ->> Corrector: correct()
    activate Corrector
    
    Corrector ->> Corrector: x=125 > 134?<br/>→ No, valid
    Corrector ->> Corrector: y=230 > 239?<br/>→ Yes, clip to 210
    Corrector ->> Corrector: radius=100 > 120?<br/>→ Yes, clip to 40
    
    Note over Corrector: 補正されたパラメータ:<br/>x=125 → 125<br/>y=230 → 210<br/>radius=100 → 40<br/>color=FFFF (白, DFL)
    
    Corrector -->> MCP: corrected_params
    deactivate Corrector
    
    MCP ->> Serial: send_command()
    activate Serial
    Serial ->> M5: DRAW_CIRCLE 125 210 40 FFFF
    activate M5
    M5 ->> M5: 描画実行
    M5 ->> Serial: OK
    deactivate M5
    Serial -->> MCP: success
    deactivate Serial
    
    MCP ->> User: JSON-RPC レスポンス
    Note over MCP: {<br/>"status": "OK",<br/>"message": "パラメータを自動調整しました。<br/>位置を (125, 210) に、半径を 40 に設定します。",<br/>"command": "DRAW_CIRCLE 125 210 40 FFFF",<br/>"duration_ms": 250<br/>}
    deactivate MCP
```

---

## 6. PING メソッド（デバイス確認）

```mermaid
sequenceDiagram
    participant MCP
    participant Serial
    participant M5

    MCP ->> Serial: ping()
    activate Serial
    
    Serial ->> M5: PING コマンド [0x01] [0x16] [0x00] [CRC] [\r\n]
    activate M5
    
    M5 ->> M5: PING 受信
    M5 ->> Serial: PONG レスポンス
    Note over M5: [0x01] [0x10] [0x02]<br/>[Device_ID] [Status] [CRC] [\r\n]
    deactivate M5
    
    Serial ->> Serial: レスポンス受信 (< 100ms)
    Serial ->> Serial: ステータス解析 → 0x10 (INFO)
    Serial -->> MCP: (online=True, device_id=0xA5)
    deactivate Serial
    
    MCP ->> MCP: デバイス状態確認
    Note over MCP: ✅ M5Stick オンライン
```

---

## 7. 初期化フロー（起動時）

```mermaid
sequenceDiagram
    participant System as System<br/>Manager
    participant MCP as MCP<br/>Gateway
    participant Serial as Serial<br/>Manager
    participant Registry as Item<br/>Registry
    participant M5

    System ->> MCP: start()
    activate MCP
    
    MCP ->> Serial: init(port="/dev/ttyUSB0", baud=115200)
    activate Serial
    Note over Serial: UART 初期化完了
    Serial -->> MCP: ready
    deactivate Serial
    
    MCP ->> Registry: load("items.json")
    activate Registry
    Note over Registry: ファイルから読み込み
    Registry -->> MCP: loaded 5 items
    deactivate Registry
    
    MCP ->> Serial: ping()
    activate Serial
    Serial ->> M5: PING
    activate M5
    M5 -->> Serial: PONG
    deactivate M5
    Serial -->> MCP: online
    deactivate Serial
    
    MCP ->> MCP: historyManager.load()
    Note over MCP: ローカルログ読み込み
    
    MCP ->> MCP: Run JSON-RPC server (stdio)
    Note over MCP: ready for Copilot requests
    deactivate MCP
    
    Note over System: ✅ 起動完了
```

---

## 8. クラス相互作用図（動作時）

```mermaid
classDiagram
    class MCPGateway {
        -serial_manager: SerialManager
        -nl_parser: NLParser
        -command_builder: CommandBuilder
        -command_queue: CommandQueue
        -history_manager: HistoryManager
        -instruction_corrector: InstructionCorrector
        +run()
        +draw(instruction)
        +ping()
        +set_item(item_id)
        +get_history(limit)
    }
    
    class SerialManager {
        -serial: Serial
        -lock: Lock
        +init(port, baud)
        +send_command(cmd_bytes): (success, response)
        +ping(): bool
    }
    
    class NLParser {
        -keyword_dict: dict
        -position_dict: dict
        +parse(instruction): (cmd_type, params)
        -tokenize()
        -detect_command()
        -extract_color()
        -extract_position()
        -extract_size()
    }
    
    class CommandBuilder {
        +build_draw_circle(x, y, r, color): bytes
        +build_draw_rect(x, y, w, h, color): bytes
        +build_draw_text(x, y, text, color): bytes
        +build_clear_screen(): bytes
        +build_set_item(item_id): bytes
        -frame(cmd_type, params): bytes
        -crc16(data): uint16
    }
    
    class InstructionCorrector {
        +correct(instruction, cmd_type, params): params
        -correct_circle_params()
        -correct_rect_params()
        -correct_text_params()
    }
    
    class CommandQueue {
        -queue: deque
        +enqueue(cmd, instruction)
        +dequeue_latest(): cmd
    }
    
    class HistoryManager {
        -history: deque(maxlen=100)
        +add(instruction, command, duration, result)
        +get_history(limit): list
        +load()
        +save()
    }
    
    MCPGateway --> SerialManager
    MCPGateway --> NLParser
    MCPGateway --> CommandBuilder
    MCPGateway --> CommandQueue
    MCPGateway --> HistoryManager
    MCPGateway --> InstructionCorrector
    NLParser --> InstructionCorrector
```

---

## 9. 変更履歴

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-04 | Initial sequence diagrams (T034) |

