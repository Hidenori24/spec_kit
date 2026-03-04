# 自然言語→コマンド翻訳仕様書

**Task**: T033  
**Status**: Draft  
**Last Updated**: 2026-03-04

---

## 1. 概要

Copilot から日本語での自然言語指示を受け取り、M5Stick 向けシリアルコマンドに翻訳するシステムの仕様です。キーワード辞書マッチングと位置推定ロジックを組み合わせて、精度の高い翻訳を実現します。

**対応言語**: 日本語  
**翻訳精度**: 95% 以上を目標（FR-015: 自動補正により達成）  
**処理時間**: < 100ms

---

## 2. 翻訳パイプライン

```
自然言語入力
    ↓
トークン化（形態素解析）
    ↓
コマンド型推定
    ↓
パラメータ抽出
    ↓
パラメータ補正（FR-015）
    ↓
シリアルコマンド生成
    ↓
M5Stick 送信
```

---

## 3. ステップ 1: トークン化

**方法**: 簡易形態素解析（キーワード辞書マッチング）

```python
def tokenize(text: str) -> list[str]:
    """テキストを形態素に分割"""
    # 実装例: 日本語テキストをスペースと句切りで分割
    tokens = []
    current = ""
    
    for char in text:
        if char in "、。！？ ":
            if current:
                tokens.append(current)
                current = ""
        else:
            current += char
    
    if current:
        tokens.append(current)
    
    return tokens

# 例: "赤い円を中央に" → ["赤い", "円を", "中央に"]
```

---

## 4. ステップ 2: コマンド型推定

**方法**: キーワード辞書マッチング（優先度順）

### 4.1 コマンド型キーワード辞書

```python
COMMAND_KEYWORDS = {
    "DRAW_CIRCLE": {
        "primary": ["円", "丸"],
        "secondary": ["描く", "描画"],
        "priority": 1
    },
    "DRAW_RECT": {
        "primary": ["矩形", "四角", "長方形"],
        "secondary": ["描く", "描画"],
        "priority": 2
    },
    "DRAW_TEXT": {
        "primary": ["テキスト", "文字", "文"],
        "secondary": ["描く", "書く"],
        "priority": 3
    },
    "CLEAR_SCREEN": {
        "primary": ["消す", "クリア", "リセット"],
        "secondary": ["画面"],
        "priority": 4
    }
}

def detect_command(tokens: list[str]) -> str:
    """トークンリストからコマンド型を推定"""
    for cmd, keywords in COMMAND_KEYWORDS.items():
        # プライマリキーワード（高精度）
        for token in tokens:
            if any(kw in token for kw in keywords["primary"]):
                return cmd
    
    # セカンダリキーワード（中精度）
    for cmd, keywords in COMMAND_KEYWORDS.items():
        for token in tokens:
            if any(kw in token for kw in keywords["secondary"]):
                return cmd
    
    raise ValueError("Command not identified")
```

---

## 5. ステップ 3: パラメータ抽出

### 5.1 色パラメータ抽出

```python
COLOR_DICT = {
    "赤": 0xF800,      # RGB565 (255, 0, 0)
    "青": 0x001F,      # (0, 0, 255)
    "緑": 0x07E0,      # (0, 255, 0)
    "黄": 0xFFE0,      # (255, 255, 0)
    "白": 0xFFFF,      # (255, 255, 255)
    "黒": 0x0000,      # (0, 0, 0)
    "紫": 0xF81F,      # (255, 0, 255)
    "茶": 0x8410,      # (128, 64, 0)
    "グレー": 0x8410,  # (128, 128, 128)
}

def extract_color(tokens: list[str]) -> int:
    """トークンから色を抽出"""
    for token in tokens:
        for color_name, rgb565 in COLOR_DICT.items():
            if color_name in token:
                return rgb565
    
    # デフォルト: 白
    return 0xFFFF
```

### 5.2 位置パラメータ抽出

```python
POSITION_DICT = {
    "中央": (67, 120),      # 画面中心 (135/2, 240/2)
    "中心": (67, 120),
    "左上": (10, 10),
    "右下": (125, 230),
    "右上": (125, 10),
    "左下": (10, 230),
    "上": (67, 40),
    "下": (67, 200),
    "左": (20, 120),
    "右": (115, 120),
}

def extract_position(tokens: list[str]) -> tuple[int, int]:
    """トークンから位置を抽出"""
    for token in tokens:
        for pos_name, (x, y) in POSITION_DICT.items():
            if pos_name in token:
                return (x, y)
    
    # デフォルト: 中央
    return (67, 120)
```

### 5.3 サイズパラメータ抽出

```python
SIZE_DICT = {
    "大きい": 40,
    "大": 40,
    "中": 25,
    "小さい": 15,
    "小": 15,
}

def extract_size(tokens: list[str]) -> int:
    """トークンからサイズを抽出"""
    for token in tokens:
        for size_name, size in SIZE_DICT.items():
            if size_name in token:
                return size
    
    # デフォルト: 中サイズ
    return 25
```

---

## 6. ステップ 4: パラメータ補正（FR-015）

**目的**: 曖昧な指示や境界値外のパラメータを自動補正

### 6.1 補正ルール

```python
class InstructionCorrector:
    
    def correct_circle_params(self, params: dict) -> dict:
        """DRAW_CIRCLE パラメータ補正"""
        # デフォルト値設定
        if "color" not in params:
            params["color"] = 0xFFFF  # 白
        if "radius" not in params:
            params["radius"] = 25
        
        # 境界値チェック
        x = params.get("x", 67)
        y = params.get("y", 120)
        radius = params.get("radius", 25)
        
        # 座標範囲: 0-134 (x), 0-239 (y)
        params["x"] = max(0, min(134, x))
        params["y"] = max(0, min(239, y))
        
        # 半径範囲: 1-120
        params["radius"] = max(1, min(120, radius))
        
        return params
    
    def correct_rect_params(self, params: dict) -> dict:
        """DRAW_RECT パラメータ補正"""
        if "color" not in params:
            params["color"] = 0xFFFF
        if "width" not in params:
            params["width"] = 50
        if "height" not in params:
            params["height"] = 30
        
        x = params.get("x", 67)
        y = params.get("y", 120)
        w = params.get("width", 50)
        h = params.get("height", 30)
        
        # 座標範囲チェック
        params["x"] = max(0, min(134, x))
        params["y"] = max(0, min(239, y))
        
        # サイズ範囲: 画面内に収まるよう調整
        params["width"] = max(1, min(135 - params["x"], w))
        params["height"] = max(1, min(240 - params["y"], h))
        
        return params
    
    def correct_text_params(self, params: dict) -> dict:
        """DRAW_TEXT パラメータ補正"""
        if "color" not in params:
            params["color"] = 0xFFFF
        if "text" not in params:
            params["text"] = "TEXT"
        
        x = params.get("x", 67)
        y = params.get("y", 120)
        
        params["x"] = max(0, min(130, x))  # テキストは右端から余裕
        params["y"] = max(0, min(230, y))
        
        # テキスト長制限
        text = params.get("text", "TEXT")
        if len(text) > 20:
            params["text"] = text[:20]
        
        return params
```

---

## 7. 翻訳例集

### 例 1: シンプル指示

```
入力: "赤い円を中央に"

トークン化: ["赤い", "円を", "中央に"]

コマンド型推定:
  - "円" キーワードマッチ → DRAW_CIRCLE

パラメータ抽出:
  - 色: "赤い" → 0xF800
  - 位置: "中央" → (67, 120)
  - サイズ: デフォルト → 25

補正:
  - x=67, y=120, radius=25, color=0xF800 (すべて有効)

出力:
  DRAW_CIRCLE 67 120 25 F800
```

### 例 2: 曖昧指示（限界値超過）

```
入力: "左上に大きな矩形"

トークン化: ["左上に", "大きな", "矩形"]

コマンド型推定:
  - "矩形" キーワードマッチ → DRAW_RECT

パラメータ抽出:
  - 位置: "左上" → (10, 10)
  - サイズ: "大きな" → width=60, height=60
  - 色: デフォルト → 0xFFFF (白)

補正:
  - x=10, y=10 (有効)
  - width=60 (有効: 10+60=70 < 135)
  - height=60 (有効: 10+60=70 < 240)

出力:
  DRAW_RECT 10 10 60 60 FFFF
```

### 例 3: 曖昧指示（境界値超過 → 補正）

```
入力: "右下に超大きい円"

トークン化: ["右下に", "超大きい", "円"]

コマンド型推定:
  - "円" → DRAW_CIRCLE

パラメータ抽出:
  - 位置: "右下" → (125, 230)  ← 画面外！
  - サイズ: "超大きい" → 100    ← 制限超過！
  - 色: デフォルト → 0xFFFF

補正 (InstructionCorrector):
  - x=125 → x=120 (境界内に調整)
  - y=230 → y=210 (余裕を持たせる)
  - radius=100 → radius=40 (画面内に収まる値に)

出力:
  DRAW_CIRCLE 120 210 40 FFFF

ユーザーへの通知:
  "パラメータを自動調整しました。
   位置を (120, 210) に、半径を 40 に設定します。"
```

---

## 8. キーワード辞書の拡張

**今後のアップデート**（Phase 3+）:

| 機能 | キーワード例 |
|-----|-----------|
| **レイヤー表示** | "前に", "奥に", "重ねる" |
| **アニメーション** | "点滅", "移動", "回転" |
| **パターン** | "グラデーション", "ドット", "ストライプ" |
| **速度制御** | "速く", "遅く", "普通" |

---

## 9. エラー処理

| シナリオ | 対応 |
|--------|------|
| **コマンド未サポート** | "申し訳ありません。その指示には対応していません。" |
| **パラメータ不足** | デフォルト値で補完 |
| **パラメータ超過** | 自動補正 + ユーザー通知 |
| **テキスト入力** | 最大 20 文字まで対応 |

---

## 10. テストケース

| ID | 入力 | 期待出力 | 検証項目 |
|----|----|---------|--------|
| **TC-001** | "赤い円を中央に" | DRAW_CIRCLE 67 120 25 F800 | コマンド型、色、位置 |
| **TC-002** | "青い矩形を左上に" | DRAW_RECT 10 10 50 30 001F | 四角形、青色 |
| **TC-003** | "右下に大きい円" | DRAW_CIRCLE 120 210 40 FFFF | 位置補正、サイズ補正 |
| **TC-004** | "画面消して" | CLEAR_SCREEN | コマンド単独 |
| **TC-005** | "テキストABCを書いて" | DRAW_TEXT 67 120 ABC FFFF | テキスト抽出 |

---

## 11. 実装チェックリスト

- [ ] トークン化関数
- [ ] コマンド型推定ロジック
- [ ] 色キーワード辞書
- [ ] 位置キーワード辞書
- [ ] サイズキーワード辞書
- [ ] パラメータ補正ロジック（全コマンド型）
- [ ] テキスト抽出ロジック
- [ ] ユーザー通知メッセージ生成
- [ ] ユニットテスト（全テストケース）

---

## 12. 変更履歴

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-04 | Initial spec (T033) |

