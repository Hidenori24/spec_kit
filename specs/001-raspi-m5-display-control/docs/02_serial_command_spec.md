# シリアルコマンド仕様書

**Task**: T016  
**Status**: Draft  
**Last Updated**: 2026-03-04

---

## 1. 概要

M5StickC Plus2 ファームウェアが受け入れるシリアルコマンドの完全仕様です。Raspberry Pi MCP ゲートウェイから JSON-RPC リクエストを受け取り、以下の 6 つシリアルコマンドに変換します。

**通信方式**: UART 115200 bps, 8 data bits, 1 stop bit, no parity  
**フレームサイズ**: 最大 256 bytes  
**応答時間**: < 5000ms (SLA)

---

## 2. フレーム構造

```
┌────────┬──────────┬────────────┬──────────────┬──────────┐
│ HEADER │ CMD_TYPE │ PARAMS_LEN │ PARAMS       │ CRC16    │
├────────┼──────────┼────────────┼──────────────┼──────────┤
│ 1 byte │ 1 byte   │ 1 byte     │ N bytes      │ 2 bytes  │
└────────┴──────────┴────────────┴──────────────┴──────────┘

例: 0x01 0x11 0x08 [x(2B) y(2B) r(1B) color(2B) pad(1B)] CRC(2B)
```

### フレームフィールド

| フィールド | サイズ | 説明 |
|----------|-------|------|
| **HEADER** | 1B | フレーム開始マーク `0x01` |
| **CMD_TYPE** | 1B | コマンドタイプ（0x10-0x16） |
| **PARAMS_LEN** | 1B | パラメータ長（0-254） |
| **PARAMS** | N B | コマンド固有パラメータ |
| **CRC16** | 2B | CCITT CRC-16 (all bytes except CRC itself) |

---

## 3. コマンド詳細

### 3.1 DRAW_CIRCLE

**コマンドタイプ**: `0x11`  
**説明**: 指定座標に円を描画

**パラメータ**:
```
[x(2B)] [y(2B)] [radius(1B)] [color(2B)]
Total: 7 bytes
```

| パラメータ | 型 | 範囲 | 説明 |
|-----------|----|----|------|
| `x` | uint16_t | 0-319 | 中心 X 座標 |
| `y` | uint16_t | 0-239 | 中心 Y 座標 |
| `radius` | uint8_t | 1-120 | 半径（ピクセル） |
| `color` | uint16_t | 0x0000-0xFFFF | RGB565 カラーコード |

**応答**: `OK` or `ER-PARAM` or `ER-SIZE`

**例**:
```
Request:  0x01 0x11 0x07 0x00A0 0x0078 0x20 0xF800 <crc>
          (中心: (160, 120), 半径: 32, 色: 赤)
Response: 0x01 0x00 0x00 <crc>  (OK)
```

---

### 3.2 DRAW_RECT

**コマンドタイプ**: `0x12`  
**説明**: 指定座標・サイズで矩形を描画

**パラメータ**:
```
[x(2B)] [y(2B)] [width(2B)] [height(2B)] [color(2B)]
Total: 9 bytes
```

| パラメータ | 型 | 範囲 | 説明 |
|-----------|----|----|------|
| `x` | uint16_t | 0-319 | 左上 X 座標 |
| `y` | uint16_t | 0-239 | 左上 Y 座標 |
| `width` | uint16_t | 1-319 | 幅（ピクセル） |
| `height` | uint16_t | 1-239 | 高さ（ピクセル） |
| `color` | uint16_t | 0x0000-0xFFFF | RGB565 カラーコード |

**応答**: `OK` or `ER-PARAM` or `ER-SIZE`

**例**:
```
Request:  0x01 0x12 0x09 0x0010 0x0010 0x00C8 0x0078 0x00FF <crc>
          (位置: (16, 16), サイズ: (200, 120), 色: 青)
Response: 0x01 0x00 0x00 <crc>  (OK)
```

---

### 3.3 DRAW_TEXT

**コマンドタイプ**: `0x13`  
**説明**: 指定座標にテキストを描画

**パラメータ**:
```
[x(2B)] [y(2B)] [text(N bytes, null-terminated)] [color(2B)]
Total: 5 + N bytes (N ≤ 128)
```

| パラメータ | 型 | 説明 |
|-----------|----|----|------|
| `x` | uint16_t | テキスト左上 X 座標 |
| `y` | uint16_t | テキスト左上 Y 座標 |
| `text` | char[] | UTF-8 文字列（null 終了） |
| `color` | uint16_t | RGB565 カラーコード |

**応答**: `OK` or `ER-PARAM` or `ER-SIZE`

**例**:
```
Request:  0x01 0x13 0x06 0x0028 0x0050 'HELLO' 0x00 0x0000 <crc>
          (位置: (40, 80), テキスト: 'HELLO', 色: 黒)
Response: 0x01 0x00 0x00 <crc>  (OK)
```

---

### 3.4 CLEAR_SCREEN

**コマンドタイプ**: `0x14`  
**説明**: 画面全体をクリア（黒）

**パラメータ**: なし

**応答**: `OK`

**例**:
```
Request:  0x01 0x14 0x00 <crc>
Response: 0x01 0x00 0x00 <crc>  (OK)
```

---

### 3.5 SET_ITEM

**コマンドタイプ**: `0x15`  
**説明**: アイテムを切り替え＆描画（Phase 3 で使用）

**パラメータ**:
```
[item_id(1B)]
Total: 1 byte
```

| パラメータ | 型 | 範囲 | 説明 |
|-----------|----|----|------|
| `item_id` | uint8_t | 0-9 | アイテム ID |

**応答**: `OK` or `ER-NOTFOUND`

**例**:
```
Request:  0x01 0x15 0x01 0x02 <crc>
          (アイテム ID 2 に切り替え)
Response: 0x01 0x00 0x00 <crc>  (OK)
```

---

### 3.6 PING

**コマンドタイプ**: `0x16`  
**説明**: デバイス状態確認（疎通テスト）

**パラメータ**: なし

**応答**: `PONG` + ステータスバイト

**例**:
```
Request:  0x01 0x16 0x00 <crc>
Response: 0x01 0x10 0x02 0x00 0xA5 <crc>
          (ステータス: 0x00=OK, 0xA5=Device ID 165)
```

---

## 4. 応答形式

### 正常応答

```
[0x01] [STATUS_CODE] [DATA_LEN] [DATA(optional)] [CRC16]
```

**STATUS_CODE**:
- `0x00` = OK (成功)
- `0x10` = INFO (情報応答、PING 用)

### エラー応答

```
[0x01] [ERROR_CODE] [REASON_LEN] [REASON] [CRC16]
```

**ERROR_CODE**:
- `0xE0` = ER-PARSE (解析失敗)
- `0xE1` = ER-PARAM (パラメータ無効)
- `0xE2` = ER-SIZE (境界外 / VRAM 超過)
- `0xE3` = ER-NOTFOUND (アイテム未見つけ)
- `0xE4` = ER-TIMEOUT (タイムアウト)
- `0xE5` = ER-MALFORMED (フレーム破損)

---

## 5. CRC-16 計算

**方式**: CCITT CRC-16 (Poly: 0x1021, Init: 0xFFFF)

```c
uint16_t crc16_ccitt(const uint8_t* data, size_t len) {
    uint16_t crc = 0xFFFF;
    for (size_t i = 0; i < len; i++) {
        crc ^= (data[i] << 8);
        for (int j = 0; j < 8; j++) {
            crc = (crc & 0x8000) ? ((crc << 1) ^ 0x1021) : (crc << 1);
            crc &= 0xFFFF;
        }
    }
    return crc;
}
```

---

## 6. 例外・エッジケース

| シナリオ | 処理 |
|--------|------|
| フレームサイズ超過 (> 256B) | ER-PARAM を返却 |
| CRC エラー | フレーム破棄, 次のフレーム待機 |
| パラメータ型変換失敗 | ER-MALFORMED 返却 |
| コマンド実行タイムアウト | ER-TIMEOUT, リセット |
| M5Stick 画面応答不可（HW エラー） | ER-DEVICE 返却 |

---

## 7. バージョン・変更履歴

| Version | Date | Changes | Ref |
|---------|------|---------|-----|
| 1.0 | 2026-03-04 | Initial draft (6 commands) | T016 |

