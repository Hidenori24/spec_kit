# ファームウェアアーキテクチャ設計書

**Task**: T015  
**Status**: Draft  
**Last Updated**: 2026-03-04

---

## 1. 概要

M5StickC Plus2 上で動作するファームウェアは、Raspberry Pi 5 からのシリアルコマンドを受信し、画面に図形を描画するシステムです。本設計書では、ファームウェアの全体アーキテクチャ、モジュール構成、状態遷移、通信フローを定義します。

**開発環境**: PlatformIO + C++17  
**ターゲット**: M5StickC Plus2（ESP32-S3）  
**シリアル設定**: 115200 bps, 8N1

---

## 2. アーキテクチャ概要

```
┌────────────────────────────────────────────────────────┐
│            M5StickC Plus2 (ESP32-S3)                  │
├────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────┐  │
│  │  main() / Loop                                    │  │
│  │  - Serial Event Dispatch                          │  │
│  │  - State Manager                                  │  │
│  └──────────────────────────────────────────────────┘  │
│         ↓ ↓ ↓         ↓ ↓ ↓         ↓ ↓ ↓              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │  Serial      │ │  Command     │ │  Drawing     │   │
│  │  Handler     │ │  Parser      │ │  Engine      │   │
│  └──────────────┘ └──────────────┘ └──────────────┘   │
│         ↓              ↓                  ↓            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐   │
│  │  Rx Buffer   │ │  Command     │ │  LCD         │   │
│  │  (Ring)      │ │  Queue       │ │  (M5Stick)   │   │
│  └──────────────┘ └──────────────┘ └──────────────┘   │
└────────────────────────────────────────────────────────┘
```

---

## 3. モジュール構成

### 3.1 Serial Handler (`serial_handler.cpp`)

**責務**: Raspberry Pi からのシリアルデータ受信、バッファ管理、フレーム検出

**主要メソッド**:
- `void init()` - シリアルポート初期化（115200 bps）
- `void handleRxInterrupt()` - UART 割り込みハンドラ
- `bool getCommand(Command*)` - バッファからコマンド取得
- `void sendResponse(const Result&)` - 応答送信

**バッファ設計**:
- Ring Buffer (256 bytes)
- リトライ時の自動リセット
- フレーム同期エラー: CRC-16 チェック

### 3.2 Command Parser (`command_parser.cpp`)

**責務**: バイト列をコマンドオブジェクトに変換、入力値の検証

**主要メソッド**:
- `ParseResult parse(const uint8_t* buf, size_t len)` - バイト列解析
- `bool validate(const Command&)` - コマンド妥当性確認
- `void encode(const Result&, uint8_t* out)` - 結果をバイト列に符号化

**コマンド形式**:
```
[HEADER(1B)] [COMMAND_TYPE(1B)] [PARAMS_LEN(1B)] [PARAMS(*)] [CRC16(2B)]
```

Example:
- `0x01 0x11 0x08 0x00A0 0x0050 0x0020 0xF800 0xABCD` → DRAW_CIRCLE

### 3.3 Drawing Engine (`drawing_engine.cpp`)

**責務**: 画面描画（円、矩形、テキスト、クリア）、色管理、VRAM 制約チェック

**主要メソッド**:
- `Result drawCircle(uint16_t x, uint16_t y, uint8_t r, uint16_t color)` - 円描画
- `Result drawRect(uint16_t x, uint16_t y, uint16_t w, uint16_t h, uint16_t color)` - 矩形描画
- `Result drawText(uint16_t x, uint16_t y, const char* text, uint16_t color)` - テキスト描画
- `Result clearScreen()` - 画面クリア
- `void setActiveItem(uint8_t item_id)` - アイテム切り替え

**色フォーマット**: RGB565 (16-bit)

**VRAM 制約**:
- M5Stick TFT RAM: 8MB
- フレームバッファ使用量: 最大 320×240×2 ≈ 150KB
- リソース余裕: 充分（描画定義は 512B 以下を想定）

---

## 4. 状態遷移図

```
┌─────────────────────┐
│   IDLE              │
│ (受信待機)           │
└──────────┬──────────┘
           │ [Rx byte available]
           ↓
┌─────────────────────┐
│   RX_BUFFERING      │
│ (バッファ蓄積)       │
└──────────┬──────────┘
           │ [Frame complete]
           ↓
┌─────────────────────┐
│   PARSE_CMD         │
│ (コマンド解析)       │
└──────────┬──────────┘
           │
      ┌────┴─────┬──────────┬──────────┐
      │           │          │          │
  [Valid]    [Invalid]  [Malformed] [Timeout]
      │           │          │          │
      ↓           ↓          ↓          ↓
   EXEC      ERROR_HDL   ERROR_HDL   ERROR_HDL
   (実行)    [ER-xxx]    [ER-PARSE]  [ER-TIMEOUT]
      │           │          │          │
      └───────────┴──────────┴──────────┘
              ↓
    ┌─────────────────────┐
    │   TX_RESPONSE       │
    │ (応答送信)           │
    └──────────┬──────────┘
               │
               ↓
    ┌─────────────────────┐
    │   IDLE (Loop)       │
    └─────────────────────┘
```

---

## 5. 通信フロー

### 正常パス

```
Raspberry Pi                  M5Stick
    │                            │
    ├─ Command Frame ────────────→│
    │  [0x01 0x11 ...]           │
    │                    ┌─────────────┐
    │                    │ Parse       │
    │                    │ Validate    │
    │                    │ Execute     │
    │                    └─────────────┘
    │                            │
    │←─ Response Frame ──────────┤
    │  [0x01 result_code ...]    │
    │                            │
```

### エラーパス

```
Raspberry Pi                  M5Stick
    │                            │
    ├─ Malformed Frame ─────────→│
    │  [0x01 0xFF ...]           │
    │                    ┌─────────────┐
    │                    │ Parse Error │
    │                    │ CRC Check   │
    │                    └─────────────┘
    │                            │
    │←─ Error Response ─────────┤
    │  [0x02 ER-PARSE ...]      │
    │                            │
```

---

## 6. タイムスペック

| イベント | 目標時間 |
|---------|--------|
| データ受信 (Frame) | < 100ms |
| コマンド解析 | < 50ms |
| 描画実行 | < 3000ms (大規模描画) |
| 応答送信 | < 50ms |
| **Total RTT** | **< 5000ms (5秒 SLA)** |

---

## 7. メモリガイドライン

| 領域 | サイズ | 備考 |
|-----|-------|------|
| コード + 定数 | ~200KB | M5Stick ROM: 4MB |
| フレームバッファ | ~150KB | TFT メモリ |
| Ring Buffer (Rx) | 256B | UART 受信用 |
| Command Queue | ~2KB | 最大 10 コマンド |
| 動作メモリ（Stack + Heap） | ~100KB | |
| **合計** | **~450KB** | ESP32-S3: 8MB SRAM → 余裕充分 |

---

## 8. エラーハンドリング戦略

1. **CRC エラー**: フレーム再送要求（タイムアウト後 3 回リトライ）
2. **パース エラー**: エラーコード返却 → IDLE へ遷移
3. **VRAM 超過**: エラーコード返却 → 描画スキップ
4. **タイムアウト**: デフォルトコマンド（CLEAR_SCREEN）実行 → リセット

---

## 9. 次フェーズへの引き継ぎ要件

- ✅ シリアルコマンド仕様書（T016）確定
- ✅ エラーコード定義書（T017）確定
- ✅ UML State Machine and Class Diagram（T018）作成
- ✅ PlatformIO プロジェクトテンプレート（platformio.ini）準備

