# 実装計画：Raspberry Pi 5 + M5StickC Plus2 AI-Driven Display System

**Feature Branch**: `001-raspi-m5-display-control`  
**Created**: 2026-03-04  
**Status**: Draft  
**Duration Estimate**: 12-16 weeks (5 phases)  

---

## エグゼクティブサマリ

本計画は、VS Code + GitHub Copilot を通じた AI 駆動型の M5StickC Plus2 画面制御システムの構築です。
Raspberry Pi 5 上に MCP ゲートウェイを構築し、Copilot の自然言語指示を M5Stick へのシリアルコマンドに変換します。
デモンストレーション用途を想定し、認証なしで動作し、直近100件の履歴管理と項目の永続化を実装します。

**主な成果物**:
- M5Stick C++ ファームウェア（PlatformIO）
- Raspberry Pi 5 上の MCP ゲートウェイ（Python 3.10+）
- 項目レジストリとコマンド履歴管理
- VS Code 統合デモ＆（オプション）スタンドアロン UI

---

## 1. マイルストーン

| Milestone | Target Week | Key Deliverable | Success Metric |
|-----------|-------------|-----------------|-----------------|
| **M0: 環境＆ハードウェア検証** | Week 0-2 | 通信基盤確認、HW/SW 環境稼働 | Raspberry Pi ↔ M5Stick シリアル双方向通信成立 |
| **M1: M5Stick ファームウェア基盤** | Week 2-5 | 基本描画エンジン・シリアル受信ロジック | 赤い円＆矩形を確実に M5Stick に描画 |
| **M2: MCP ゲートウェイ MVP** | Week 5-9 | Copilot ↔ MCP ↔ シリアルパイプライン | US-1 の受け入れシナリオ 2 個達成（5秒以内）|
| **M3: 高度な機能実装** | Week 9-14 | アイテム切り替え、永続化、キュー管理、自動補正 | US-2, US-3 の受け入れシナリオ達成 |
| **M4: 検証＆デプロイ** | Week 14-16 | エンドツーエンドテスト、ドキュメント、デモ | 全 SC-001 to SC-006 検証、5 秒 SLA 達成 |

---

## 2. フェーズ別実装計画

### Phase 0: 環境構築＆ハードウェア検証 (Week 0-2)

**目的**: 物理ハードウェア、通信路、開発環境の動作可能性を確認する。

**内容**:
1. **ハードウェア確保＆検証**
   - Raspberry Pi 5 電源＆OS インストール（Raspberry Pi OS 64-bit × 1）
   - M5StickC Plus2 × 1 個確保＆最新ファームウェア動作確認
   - USB-UART ケーブル確保＆ドライバ確認（Windows/Linux/macOS）

2. **シリアル通信基盤確認**
  - Raspberry Pi の UART ポート（/dev/ttyAMA0 or /dev/ttyS0）と M5Stick の RX/TX をテスト配線
  - ボーレート設定確認（115200 を想定）
  - minicom or screen コマンドで双方向疎通確認（テキスト送受信テスト）

3. **開発環境セットアップ**
  - Raspberry Pi 5 に Python 3.10+ インストール確認
  - Raspberry Pi 5 に PlatformIO CLI インストール（M5Stick 開発用）
  - Raspberry Pi 5 に VS Code インストール＆GitHub Copilot 拡張セットアップ
  - Git リポジトリクローンと ブランチ `001-raspi-m5-display-control` チェックアウト

4. **初期テスト**
  - Raspberry Pi 5 上の PlatformIO で空スケッチを M5Stick へデプロイし起動確認
  - Raspberry Pi から シリアルで「HELLO」を送信 → M5Stick 受信確認

**完了条件**:
- ✅ USB-UART ドライバ＆接続確認済み
- ✅ Raspberry Pi ↔ M5Stick 双方向通信成立（テキスト送受信）
- ✅ 開発環境全て稼働（VS Code + PlatformIO + Python 3.10+）
- ✅ リポジトリ環境構築完了

**懸念＆変更案**:
- 🔴 **懸念**: Windows マシンからの Raspberry Pi へのシリアル配線が複雑
  - **対策**: 当初は Raspberry Pi 上で minicom を使った双方向テストで進める
- 🟡 **懸念**: M5Stick の電源管理（バッテリー vs USB）
  - **対策**: デモ中は USB 給電前提；バッテリー運用は Phase 4 で検討

---

### Phase 1: M5Stick ファームウェア基盤 (Week 2-5)

**目的**: M5Stick が Raspberry Pi からのシリアルコマンドを受け取り、画面に図形を描画する基盤を構築。

**内容**:

1. **ファームウェア設計＆アーキテクチャ**
   - **設計資料作成**: 
     - コマンドプロトコル仕様（例：`DRAW_CIRCLE <x> <y> <radius> <color>` ）
     - シリアル通信フォーマット（ヘッダ、ペイロード、チェックサム）
     - ファームウェア状態遷移図（受信待機 → コマンド解析 → 描画実行 → 結果返却）
   - **UML**: State Machine、Class Diagram for DrawingEngine

2. **基本描画エンジン実装**
   - **firmware/src/drawing_engine.cpp** (C++):
     - `class DrawingEngine` with methods: `drawCircle()`, `drawRect()`, `drawText()`, `clearScreen()`
     - M5StickCPlus2 ライブラリをラップ
     - 色管理：RGB 565 format
   
   - **firmware/src/serial_handler.cpp** (C++):
     - シリアル割り込みハンドラ→コマンドバッファ蓄積
     - コマンドパーサー（トークン分割、型変換）
     - エラーハンドリング（不正ペイロード、サイズ超過 → ER-SIZE）

3. **コマンドセット定義**
   - P1 要件最小セット（6 コマンド）:
     - `DRAW_CIRCLE <x:u16> <y:u16> <r:u8> <color:u16>` → OK or ER-xxx
     - `DRAW_RECT <x:u16> <y:u16> <w:u16> <h:u16> <color:u16>` → OK or ER-xxx
     - `DRAW_TEXT <x:u16> <y:u16> <text:str> <color:u16>` → OK or ER-xxx
     - `CLEAR_SCREEN` → OK or ER-xxx
     - `SET_ITEM <item_id:u8>` → OK or ER-xxx
     - `PING` → PONG + status

   - **応答フォーマット**: `OK\r\n` or `ER-<CODE>:<reason>\r\n`

4. **VRAM＆リソース検証**
   - M5Stick C Plus2 RAM（8MB）内で描画＆履歴管理
   - アイテムレジストリ MAX 10 アイテム想定
   - 各アイテムの描画定義サイズ：MAX 512 bytes → 5KB（余裕十分）

5. **ハードウェア検証テスト**
   - 赤い円を (160, 80) に描画
   - 青い矩形を (10, 10) に描画
   - テキスト「TEST」を表示
   - 5 秒応答確認、結果コード受信確認

**完了条件**:
- ✅ DrawingEngine クラス実装＆コンパイル成功
- ✅ シリアル受信＆コマンドパーサー動作（単純テキスト指令）
- ✅ DRAW_CIRCLE, DRAW_RECT, CLEAR_SCREEN 実装＆検証
- ✅ ER-SIZE, ER-MALFORMED エラー応答確認
- ✅ ファームウェア設計書作成（コマンド仕様書含む）

**懸念＆変更案**:
- 🟡 **懸念**: M5Stick TFT ライブラリのメモリ効率
  - **対策**: フレームバッファ部分キャッシュではなく、コマンド再実行で描画
- 🟡 **懸念**: シリアル受信中のコマンド破損
  - **対策**: チェックサム（CRC-16）追加＆タイムアウトで再同期

---

### Phase 2: MCP ゲートウェイ MVP (Week 5-9)

**目的**: Raspberry Pi 上の MCP ゲートウェイが Copilot からの指示を受け取り、M5Stick へシリアルコマンドを変換・送信する。

**内容**:

1. **MCP サーバー設計**
   - **設計資料**:
     - MCP プロトコル フロー図（Copilot ↔ ゲートウェイ ↔ M5Stick）
     - メッセージスキーマ（入力：自然言語、出力：JSON 結果）
   - **UML**: Sequence Diagram

2. **Python MCP ゲートウェイ実装** (~250-350 行)
   - **src_pi/mcp_gateway.py**:
     - `class MCPGateway` with message handlers
     - Copilot からの JSON-RPC メッセージ受信（`content_type="text"`）
     - 自然言語 → 描画コマンド翻訳ロジック（キーワードマッチング）
       - "赤い円を中央に" → `DRAW_CIRCLE 160 80 20 <RED>`
       - "矩形を左上に" → `DRAW_RECT 10 10 50 50 <COLOR>`
     - シリアル送信＆応答取得（timeout = 5秒）
     - 結果を JSON フォーマットで Copilot へ返却

3. **シリアルポート管理**
   - **src_pi/serial_manager.py**:
     - PySerial 使用（`pyserial` 3.5+）
     - ボーレート 115200, timeout 5秒
     - 送信後の応答受信＆パース（`OK` or `ER-<CODE>:<reason>`）
     - 再試行ロジック（タイムアウト時 1 回リトライ）

4. **Copilot 統合テスト**
   - VS Code Chat ウィンドウで：
     - `@mcp show me a red circle in the center`
     - ゲートウェイが受信 → パース → M5Stick へ送信
     - 5 秒以内に M5Stick 画面に赤い円表示

5. **エラーハンドリング＆ログ**
   - タイムアウト → `ER-TIMEOUT`
   - 不正な指指令 → `ER-MALFORMED` → Copilot へ返却
   - **ログ記録**: ファイルログ（デバッグ用）

**完了条件**:
- ✅ MCP ゲートウェイ起動確認
- ✅ VS Code + Copilot から描画指示 → M5Stick 表示確認
- ✅ 応答時間 5 秒以内（SC-001）
- ✅ シリアルタイムアウト＆リトライ実装
- ✅ ゲートウェイ設計書＆API 仕様書作成

**懸念＆変更案**:
- 🔴 **懸念**: Copilot と MCP ゲートウェイの通信方式
  - **対策**: stdio ベース（簡易実装）＆ログで接続性確認
- 🟡 **懸念**: 自然言語 → コマンド翻訳の精度
  - **対策**: キーワード辞書を JSON で管理＆拡張可能に設計

---

### Phase 3: 高度な機能実装 (Week 9-14)

**目的**: アイテム切り替え、永続化、キュー管理、自動補正を実装＆ US-2, US-3 完成。

**内容**:

1. **アイテムレジストリ＆永続化**
   - **設計資料**:
     - Item Registry スキーマ（ID, Name, Layout JSON, VRAM size）
     - ファイル形式：JSON（`~/.m5stick_items.json`）
   
   - **src_pi/item_registry.py** (~150 行):
     - `class ItemRegistry` with `load()`, `save()`, `register_item()`, `get_item()`
     - 初期 5 アイテム（グラフ、温度、スタンバイ、テキスト、カスタムレイアウト）

   - **M5Stick ファームウェア**: `SET_ITEM <item_id>` コマンド処理
     - ローカルストレージから レイアウト JSON を読み込み
     - 描画実行

2. **キュー管理＆最新指示優先**
   - **src_pi/command_queue.py**:
     - `class CommandQueue` with `enqueue()`, `dequeue_latest()`, `is_empty()`
     - 短時間に複数指示来た場合、**最後の指示のみ実行**
     - タイムアウト 2 秒（キュー内指示が 2 秒以上古い→破棄）

3. **自動補正ロジック**
   - **src_pi/instruction_corrector.py** (~100 行):
     - `class InstructionCorrector` with `auto_correct()`
     - 曖昧指示（"色を変えて"）→ 最も近い有効コマンドに補正
     - 補正内容を結果 JSON に記録

4. **履歴管理（リングバッファ）**
   - **src_pi/history_manager.py** (~100 行):
     - `class HistoryBuffer` with ring buffer (max 100 items)
     - 各履歴: timestamp, request (abbrev.), result code, correction (if any)
     - Copilot から `GET_HISTORY` 指令 → 最新 10 件 JSON で返却

5. **アイテム切り替えテスト**
   - グラフ → 温度 → スタンバイ 順序で指示
   - 毎回 2 秒以内に M5Stick 画面更新確認（SC-005）

**完了条件**:
- ✅ ItemRegistry JSON ファイル読み書き確認
- ✅ Raspberry Pi 再起動後アイテム復旧確認
- ✅ キューイング＆最新指示優先確認
- ✅ 曖昧指示の自動補正＆結果記録確認
- ✅ Ring buffer 100 件上限＆リサイクル
- ✅ US-2, US-3 受け入れシナリオ全て達成
- ✅ アイテムレジストリ＆キュー管理設計書完成

**懸念＆変更案**:
- 🟡 **懸念**: 自動補正が誤補正する場合
  - **対策**: 補正前に Copilot へ確認メッセージ（オプション）or 明示ログ
- 🟡 **懸念**: リングバッファ 100 件で十分か
  - **対策**: デモ運用で実測 → 調整可

---

### Phase 4: 検証＆デプロイメント (Week 14-16)

**目的**: エンドツーエンド検証、ドキュメント完成、デモンストレーション準備。

**内容**:

1. **エンドツーエンドテスト**
   - **テストシナリオ**:
     - Scenario A: VS Code Copilot から「赤い円を中央に」指示 → 5 秒以内表示 (SC-001)
     - Scenario B: 「グラフ表示」指示 3 回連続 → 最後の指示だけ反映 (SC-006)
     - Scenario C: 曖昧「色変えて」→ 自動補正＆実行 (FR-015)
     - Scenario D: M5Stick 未接続状態で指示 → `ER-TIMEOUT` 返却＆リトライ可能
   
   - **受け入れ基準**:
     - SC-001～SC-006 全て達成
     - 95% 成功率
     - 失敗時 10 秒以内に理由コード認識

2. **技術資料完成**
   - **設計書** （既作成分＋統合）:
     - M5Stick ファームウェア仕様書
     - MCP ゲートウェイ API 仕様書
     - アイテムレジストリスキーマ＆永続化方式
   
   - **UML ドキュメント**:
     - システムアーキテクチャ図（3 層）
     - State Machine 図（ファームウェア）
     - Sequence 図（エンドツーエンド）
   
   - **非技術者向け説明資料**:
     - 1 ページサマリ（「VS Code から話しかけると M5Stick が変わる」）
     - ユースケース図
     - 操作ガイド

3. **デプロイメント準備**
   - **セットアップスクリプト作成**:
     - `setup_raspberry_pi.sh`: Python 3.10+ インストール、依存パッケージ、自動起動設定
     - `setup_m5stick.sh`: PlatformIO ファームウェアビルド＆デプロイ
   
   - **トラブルシューティングガイド**:
     - シリアル接続失敗時の診断
     - ファームウェア更新手順
     - ログ確認方法

4. **デモンストレーション実施**
   - Live demo: Raspberry Pi + M5Stick を接続したまま VS Code で描画指示
   - 複数指示短時間送信 → 最後の指示だけ反映確認
   - **記録**: スクリーンショット＆動画

**完了条件**:
- ✅ 全 SC-001～SC-006 検証完了
- ✅ 95% 成功率達成
- ✅ エンドツーエンドテストシナリオ A-D 全て pass
- ✅ 技術資料全て完成
- ✅ デプロイスクリプト動作確認
- ✅ デモ実施＆記録完了

**懸念＆変更案**:
- 🟡 **懸念**: 95% 成功率達成しない場合
  - **対策**: Phase 3 のキュー管理＆タイムアウト調整 or シリアル再同期強化
- 🟡 **懸念**: ドキュメント量過多
  - **対策**: API_SPEC, README に最小化＆詳細は Wiki で

---

## 3. 技術資料作成計画

### 設計書作成スケジュール

| Document | Phase | Format | Audience | 主要内容 |
|-----------|-------|--------|----------|---------|
| **System Architecture Diagram** | 2-3 | PNG/draw.io | 全員 | Copilot ↔ MCP ↔ M5Stick 3層構成 |
| **M5Stick Firmware Spec** | 1 完了後 | Markdown | 開発者 | コマンド仕様、プロトコル、状態遷移 |
| **MCP Gateway API Spec** | 2 完了後 | Markdown | 開発者 | JSON-RPC インターフェース、エラーコード |
| **Item Registry Schema** | 3 開始時 | JSON Schema | 開発者 | アイテム定義フォーマット、永続化方式 |
| **State Machine Diagram** | 1 完了後 | PNG/Mermaid | 開発者 | ファームウェア受信→解析→描画 |
| **Sequence Diagram** | 2 完了後 | PNG/PlantUML | 開発者 | Copilot → MCP → Serial → M5Stick |
| **ユースケース説明資料** | 4 | Markdown+PNG | 技術者・ステーク | 「VS Code から話しかけると...」 |
| **セットアップ＆トラブルシューティング** | 4 | Markdown | 運用者 | インストール手順、診断方法 |

### 非技術者向け説明（1 ページ）

> **「AI が M5Stick を操る」システム**
>
> VS Code で GitHub Copilot に「赤い円を画面の真ん中に描いて」と日本語で言います。
> Copilot がそれを理解し、Raspberry Pi 上の「翻訳機」（MCP ゲートウェイ）に送ります。
> 翻訳機が「M5Stick の言語」に変換して、有線で M5Stick に送ります。
> M5Stick がすぐに（5 秒以内）そのとおりに画面を変えます。
>
> **特徴**:
> - 何度も描き換えられる（同じ指示または違う指示）
> - 複数のアイテム（グラフ、温度計など）をすぐ切り替えられる
> - 複数の指示が来ても、最後の指示だけ実行される
> - 失敗したときは理由を教えてくれる

---

## 4. 完了のための条件と対応

### 基本要件（全て達成必須）

| Requirement | Status | Verification | Mitigation |
|-------------|--------|---------------|------------|
| **シリアル通信 115200 baud**（FR-003）| TBD | minicom で双方向テキスト送受信 | ボーレート変更可能に設定 |
| **5 秒 SLA**（SC-001）| TBD | E2E 20 回テスト→平均 ≤5 秒 | キューのタイムアウト調整 |
| **95% 成功率**（SC-002）| TBD | 20 回テスト中 ≥19 回成功 | シリアル再同期＆リトライ |
| **アイテム永続化**（FR-014）| TBD | RPi 再起動後ファイル存在確認 | JSON ハンドリング堅牢化 |
| **キュー最新優先**（SC-006）| TBD | 3 指示同時送信→最後のみ実行 | キューロジック＆タイムスタンプ |

---

## 5. リスク＆対応策

### 高リスク

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **M5Stick シリアル通信不安定** | Phase 1 ブロック | High | Phase 0 で徹底テスト + CRC-16 追加 |
| **Copilot API/MCP 仕様変更** | Phase 2 リワーク | Low | MCP 標準仕様書参照＆柔軟実装 |
| **Raspberry Pi 5 品切れ** | HW 調達不可 | Low | RPi 4 への downgrade 検討 |

### 中リスク

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **自然言語補正の精度不足** | US-3 受け入れ遅延 | Medium | 辞書拡張＋Copilot 協調改善 |
| **複数コマンド同時到着時の競合** | デッドロック | Medium | 排他制御＆キューの堅牢化 |

---

## 6. 積み残し＆今後の拡張

### Phase 4 での未実装（Low Priority）

- ⏳ **WiFi/Bluetooth 無線化**: 有線のみ（Phase 4 後検討）
- ⏳ **複数 M5Stick 対応**: 1 台のみ（スケーリング後）
- ⏳ **Web UI**: VS Code + Copilot が主（Web UI は別フェーズ）

### 本番化への課題

- 🔴 **認証＆セキュリティ**: demo 用認証なし → 本番利用時に OAuth 2.0
- 🔴 **スケーリング**: 複数 M5Stick 制御＆ロードバランシング
- 🔴 **ログ集約**: 現在は RPi ローカル → ELK Stack or CloudWatch

---

## 7. Week-by-Week Milestones

| Week | Phase | Key Outcome | Go/No-Go Decision |
|------|-------|-------------|-------------------|
| W1-W2 | 0 | HW 通信基盤確認 | ✅ シリアル通信成立→Phase 1 Go |
| W3-W5 | 1 | ファームウェア基本実装＆テスト | ✅ 描画動作確認→Phase 2 Go |
| W6-W9 | 2 | MCP + Copilot 連携 5 秒以内 | ✅ SC-001 達成→Phase 3 Go |
| W10-W14 | 3 | 高度機能＆US-2/US-3 完成 | ✅ SC-005/SC-006→Phase 4 |
| W15-W16 | 4 | ドキュメント＆デモ完成 | ✅ 全 SC 達成→Release |

---

## 8. チーム＆リソース

### 想定構成（小規模チーム）

| Role | FTE | Responsibility |
|------|-----|-----------------|
| **Firmware Engineer** | 1.0 | M5Stick C++, PlatformIO, HW |
| **Backend/Gateway Engineer** | 1.0 | Python MCP gateway, serial, registry |
| **QA / Integration Tester** | 0.5 | E2E テスト、受け入れ基準検証 |
| **Tech Writer** | 0.5 | 設計書、UML、ユーザーガイド |

---

## 9. 用語集

| Term | Definition |
|------|-----------|
| **MCP** | Model Context Protocol - Copilot と外部ツール間の通信 |
| **ゲートウェイ** | Raspberry Pi 上の Python 中継プログラム |
| **Item Registry** | 描画アイテム定義を保持する JSON |
| **Ring Buffer** | 固定サイズで最新データのみ保持 |
| **SLA** | Service Level Agreement = 5 秒応答時間 |

---

**Plan Status**: 🟡 Draft  
**Last Updated**: 2026-03-04
