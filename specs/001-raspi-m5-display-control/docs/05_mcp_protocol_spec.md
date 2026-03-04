# MCP プロトコル仕様書

**Task**: T031  
**Status**: Draft  
**Last Updated**: 2026-03-04

---

## 1. 概要

MCP (Model Context Protocol) は、VS Code + GitHub Copilot から JSON-RPC ベースのリクエストを受け取り、M5Stick への制御コマンドに変換するプロトコルです。本仕様書は、Raspberry Pi 5 上で動作する MCP ゲートウェイが実装する JSON-RPC インターフェースを定義します。

**基準**: [MCP Specification](https://github.com/anthropics/mcp)  
**トランスポート**: stdio (VS Code Child Process)  
**形式**: JSON-RPC 2.0

---

## 2. MCP フロー図

```
┌─────────────────────────────────────────────────────────────┐
│ VS Code + GitHub Copilot (User)                             │
│ "赤い円を中央に描画して"                                      │
└────────────────┬────────────────────────────────────────────┘
                 │ JSON-RPC Request
                 ↓
┌─────────────────────────────────────────────────────────────┐
│ Raspberry Pi 5                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ MCP ゲートウェイ (Python)                             │  │
│  │ ├─ Natural Language Parser                           │  │
│  │ ├─ Instruction Corrector (FR-015)                   │  │
│  │ ├─ Serial Manager                                   │  │
│  │ └─ History Manager                                  │  │
│  └───────────────────────────────────────────────────────┘  │
│         ↓ シリアルコマンド 115200 bps               │
│         ↓ "DRAW_CIRCLE 160 120 32 F800"              │
└─────────────┬──────────────────────────────────────────────┘
              │ UART 接続
              ↓
┌─────────────────────────────────────────────────────────────┐
│ M5StickC Plus2 (ESP32-S3)                                   │
│  ┌───────────────────────────────────────────────────────┐  │
│  │ Firmware                                              │  │
│  │ ├─ Serial Handler                                    │  │
│  │ ├─ Command Parser                                    │  │
│  │ └─ Drawing Engine                                    │  │
│  └───────────────────────────────────────────────────────┘  │
│         ↓ LCD Output                                        │
│     赤い円が画面に表示                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. MCP メソッド定義

### 3.1 `draw`

**説明**: 自然言語で指示を送信し、M5Stick に描画させる

**リクエスト**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "draw",
  "params": {
    "instruction": "赤い円を中央に描画",
    "timeout_ms": 5000
  }
}
```

**パラメータ**:
| 名前 | 型 | 必須 | 説明 |
|-----|----|----|------|
| `instruction` | string | ✓ | 自然言語命令（日本語） |
| `timeout_ms` | integer | optional | タイムアウト（デフォルト: 5000ms） |

**レスポンス（成功）**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "status": "OK",
    "message": "描画成功",
    "command": "DRAW_CIRCLE 160 120 32 F800",
    "duration_ms": 150,
    "timestamp": "2026-03-04T10:30:45Z"
  }
}
```

**レスポンス（エラー）**:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "status": "ER-TIMEOUT",
    "message": "M5Stick に接続できません",
    "duration_ms": 5000,
    "timestamp": "2026-03-04T10:30:45Z"
  }
}
```

---

### 3.2 `set_item`

**説明**: アイテムを切り替える（Phase 3 で実装）

**リクエスト**:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "set_item",
  "params": {
    "item_id": 2,
    "timeout_ms": 5000
  }
}
```

**パラメータ**:
| 名前 | 型 | 必須 | 説明 |
|-----|----|----|------|
| `item_id` | integer | ✓ | アイテム ID (0-9) |
| `timeout_ms` | integer | optional | タイムアウト |

---

### 3.3 `get_history`

**説明**: コマンド実行履歴を取得（Phase 3 で実装）

**リクエスト**:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "get_history",
  "params": {
    "limit": 10
  }
}
```

**レスポンス**:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "status": "OK",
    "history": [
      {
        "timestamp": "2026-03-04T10:30:45Z",
        "instruction": "赤い円を中央に",
        "command": "DRAW_CIRCLE 160 120 32 F800",
        "duration_ms": 150,
        "result": "OK"
      }
    ]
  }
}
```

---

### 3.4 `ping`

**説明**: デバイス状態確認

**リクエスト**:
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "ping",
  "params": {}
}
```

**レスポンス**:
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "result": {
    "status": "OK",
    "device": "M5StickCPlus2",
    "firmware_version": "1.0.0",
    "online": true
  }
}
```

---

## 4. エラーコード（JSON-RPC レベル）

| Code | Message | 説明 |
|------|---------|------|
| **-32700** | Parse error | JSON ペースエラー |
| **-32600** | Invalid Request | 不正な JSON-RPC リクエスト |
| **-32601** | Method not found | メソッドが存在しない |
| **-32602** | Invalid params | パラメータ不正 |
| **-32603** | Internal error | 内部エラー |

---

## 5. データベース応答フォーマット

### 成功応答

```json
{
  "status": "OK",
  "message": "成功メッセージ",
  "duration_ms": 150,
  "timestamp": "2026-03-04T10:30:45Z",
  "data": {}  // メソッド固有のデータ
}
```

### エラー応答

```json
{
  "status": "ER-<CODE>",
  "message": "エラーメッセージ",
  "duration_ms": 5000,
  "timestamp": "2026-03-04T10:30:45Z",
  "error_code": "0xE4",
  "retry_possible": true
}
```

**ER-<CODE> パターン**:
- `ER-TIMEOUT`: M5Stick 応答時間超過
- `ER-MALFORMED`: フレーム破損
- `ER-PARAM`: パラメータ無効
- `ER-SIZE`: VRAM 制約超過
- `ER-NOTFOUND`: アイテムなし
- `ER-DEVICE`: デバイス HW エラー

---

## 6. 無認証運用ポリシー（FR-013）

### セキュリティモデル

**前提条件**:
- ローカルネットワーク（Raspberry Pi + VS Code on 同一 LAN）
- デモンストレーション用途のみ
- 信頼できるネットワーク環境

**実装**:
- JSON-RPC リクエストには認証トークンなし
- stdio ベースの子プロセス（プロセス分離保証）
- ローカルホスト接続のみサポート

**運用範囲**:
- ✅ 社内デモンストレーション
- ✅ 大学実験環境
- ❌ インターネット公開
- ❌ 複数ユーザー共有環境

---

## 7. 実装チェックリスト（Phase 2）

- [ ] JSON-RPC 2.0 ハンドラ実装
- [ ] `draw` メソッド実装（自然言語→コマンド翻訳）
- [ ] `ping` メソッド実装
- [ ] エラーハンドリング（タイムアウト、接続失敗）
- [ ] stdio フロー（Copilot ↔ MCP ↔ M5Stick）
- [ ] ログ記録（すべてのリクエスト/レスポンス）
- [ ] 統合テスト（Copilot + MCP + M5Stick）

---

## 8. 変更履歴

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-04 | Initial protocol specification (T031) |

