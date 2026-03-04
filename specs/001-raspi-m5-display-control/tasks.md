# タスク分解：Raspberry Pi 5 + M5StickC Plus2 AI-Driven Display System

**Feature Branch**: `001-raspi-m5-display-control`  
**Task Allocation**: 78 tasks across 5 phases  
**Status**: Draft  

---

## タスク体系

各タスクは以下の形式で記載：
- **T###**: Task ID（3 桁）
- **[Phase]**: フェーズ（P0-P4）
- **[Priority]**: 優先度（P1=Critical, P2=High, P3=Medium, P4=Low）
- **[Estimate]**: 見積もり日数
- **[Dependencies]**: 依存タスク
- **[Parallel]**: 並列実行可能（[P] 表記）

## 整合性マッピング

| User Story | Tasks | Spec Section | Plan Phase |
|---|---|---|---|
| **US-1** (AI駆動描画、P1) | T027, T040, T059～T062 | Acceptance Scenarios 1-2 | Phase 1-2 |
| **US-2** (アイテム切り替え、P2) | T045～T051, T056 | Acceptance Scenarios 1-2 | Phase 3 |
| **US-3** (MCP プリセット、P3) | T048, T057 | Acceptance Scenarios 1-2 | Phase 3 |

---

## Phase 0: 環境構築＆ハードウェア検証 (Week 0-2)

### 基本インフラ (P1 - Critical)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T001** | HW 確保：Raspberry Pi 5 + M5StickC Plus2 + USB-UART ケーブル | P1 | 1 day | Not Started | - |
| **T002** | Raspberry Pi OS インストール＆初期セットアップ（SSH, 固定 IP 設定） | P1 | 2 days | Not Started | T001 |
| **T003** | USB-UART ドライバインストール（Windows/macOS） | P1 | 1 day | Not Started | T001 |
| **T004** | M5StickC Plus2 デフォルトファームウェア確認（画面表示） | P1 | 1 day | Not Started | T001 |
| **T005** | Raspberry Pi UART ポート確認＆動作テスト（minicom/screen）| P1 | 1 day | Not Started | T002, T003 |

### 開発環境セットアップ (P1)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T006** | Raspberry Pi に Python 3.10+ インストール確認 | P1 | 1 day | Not Started | T002 |
| **T007** | Windows/macOS マシンに PlatformIO CLI インストール | P1 | 1 day | Not Started | - |
| **T008** | VS Code インストール＆GitHub Copilot 拡張セットアップ | P1 | 2 days | Not Started | - |
| **T009** | リポジトリクローン＆ブランチチェックアウト（`001-raspi-m5-display-control`） | P1 | 0.5 days | Not Started | T008 |
| **T010** | Git 初期コミット（Phase 0 スナップショット） | P2 | 0.5 days | Not Started | T009 |

### ハードウェア統合テスト (P1)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T011** | シリアルテスト：Raspberry Pi → M5Stick テキスト送信（「HELLO」） | P1 | 2 days | Not Started | T005, T004 |
| **T012** | シリアルテスト：M5Stick → Raspberry Pi レスポンス受信確認 | P1 | 1 day | Not Started | T011 |
| **T013** | リポジトリディレクトリ構造作成（firmware/, src_pi/, tests_pi/, docs/） | P2 | 1 day | Not Started | T009 |
| **T014** | Phase 0 完了チェックリスト作成＆検証 | P2 | 0.5 days | Not Started | T012, T013 |

---

## Phase 1: M5Stick ファームウェア基盤 (Week 2-5)

### 設計＆仕様書 (P1)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T015** | ファームウェアアーキテクチャ設計書作成（コマンドプロトコル、状態遷移） | P1 | 2 days | ✅ Completed | T014 |
| **T016** | シリアルコマンド仕様書作成（DRAW_CIRCLE, DRAW_RECT 等） | P1 | 2 days | ✅ Completed | T015 |
| **T017** | エラーコード定義書（ER-TIMEOUT, ER-SIZE, ER-MALFORMED） | P1 | 1 day | ✅ Completed | T016 |
| **T018** | UML State Machine 図作成（ファームウェア受信→解析→描画） | P2 | 1 day | ✅ Completed | T015 |

### 描画エンジン実装 (P1)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T019** | `firmware/src/drawing_engine.cpp` 基本実装（drawCircle, drawRect, clearScreen） | P1 | 3 days | ✅ Completed | T016 |
| **T020** | M5StickCPlus2 LCD ライブラリ統合＆色管理（RGB565） | P1 | 2 days | ✅ Completed | T019 |
| **T021** | `firmware/src/drawing_engine.cpp` テスト（統合テスト：DrawingEngine + LCD 実機描画） | P1 | 2 days | ⏳ In Progress | T019, T020 |

### シリアルハンドラ実装 (P1)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T022** | `firmware/src/serial_handler.cpp` 基本実装（割り込みハンドラ、バッファ管理） | P1 | 2 days | ✅ Completed | T016 |
| **T023** | コマンドパーサー実装（トークン分割、型変換） | P1 | 2 days | ✅ Completed | T022 |
| **T024** | エラーハンドリング＆応答フォーマット（OK/ER-xxx） | P1 | 1 day | ✅ Completed | T017, T023 |
| **T025** | CRC-16 チェックサム追加（通信信頼性向上） | P2 | 1 day | ⏳ In Progress | T024 |

### ファームウェア統合＆テスト (P1)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T026** | PlatformIO での ビルド＆M5Stick へのアップロード | P1 | 1 day | Not Started | T021, T024 |
| **T027** | HW 統合テスト：Raspberry Pi から DRAW_CIRCLE 指示 → M5Stick 描画確認 | P1 | 2 days | Not Started | T026, T012 |
| **T028** | フェイルセーフテスト：不正コマンド送信 → ER-MALFORMED 応答確認 | P1 | 1 day | Not Started | T027 |
| **T029** | VRAM＆リソース検証（RAM 使用率確認、メモリリーク チェック、FR-010 VRAM 制約検証） | P2 | 1 day | Not Started | T027 |
| **T030** | Phase 1 完了チェックリスト＆ファームウェア設計書最終版 | P2 | 1 day | Not Started | T029 |

---

## Phase 2: MCP ゲートウェイ MVP (Week 5-9)

### MCP ゲートウェイ設計 (P1)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T031** | MCP プロトコル仕様確認＆フロー図作成 | P1 | 1 day | ✅ Completed | T030 |
| **T032** | MCP ゲートウェイアーキテクチャ設計書（JSON-RPC インターフェース） | P1 | 2 days | ✅ Completed | T031 |
| **T033** | 自然言語→コマンド翻訳仕様書（キーワード辞書、補正戦略） | P1 | 1 day | ✅ Completed | T032 |
| **T078** | 無認証運用の前提条件・運用範囲を設計書に明記（FR-013） | P2 | 0.5 days | ✅ Completed | T032 |
| **T034** | UML Sequence 図作成（Copilot → MCP → Serial → M5Stick） | P2 | 1 day | ✅ Completed | T032 |

### Python MCP ゲートウェイ実装 (P1)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T035** | `src_pi/mcp_gateway.py` 基本実装（MCPGateway クラス、メッセージハンドラ） | P1 | 3 days | ✅ Completed | T033 |
| **T036** | `src_pi/serial_manager.py` 実装（シリアル送受信、タイムアウト、リトライ） | P1 | 2 days | ✅ Completed | T033 |
| **T037** | 自然言語パーサー実装（"赤い円" → DRAW_CIRCLE コマンド翻訳） | P1 | 2 days | ✅ Completed | T035, T036 |
| **T038** | JSON-RPC レスポンス形式実装（OK, ER-xxx） | P1 | 1 day | ✅ Completed | T036 |

### Copilot 統合＆テスト (P2)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T039** | VS Code + Copilot との stdio 接続確認 | P1 | 2 days | Not Started | T035 |
| **T040** | E2E テスト：Copilot → MCP → M5Stick 描画確認（5 秒以内） | P1 | 2 days | Not Started | T026, T039 |
| **T041** | エラーテスト：M5Stick 未接続 → ER-TIMEOUT 確認 | P1 | 1 day | Not Started | T040 |
| **T042** | 応答時間測定＆ログ記録（5 秒 SLA 検証） | P2 | 1 day | Not Started | T040 |
| **T043** | MCP ゲートウェイ API 仕様書最終版作成 | P2 | 1 day | Not Started | T041, T042 |
| **T044** | Phase 2 完了チェックリスト＆デモ動画記録 | P2 | 1 day | Not Started | T043 |

---

## Phase 3: 高度な機能実装 (Week 9-14)

### アイテムレジストリ＆永続化 (P1)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T045** | アイテムレジストリスキーマ設計（JSON フォーマット、VRAM 要件） | P1 | 1 day | Not Started | T044 |
| **T046** | `src_pi/item_registry.py` 実装（読み込み、保存、登録、取得） | P1 | 2 days | Not Started | T045 |
| **T047** | 初期 5 アイテム定義作成（グラフ、温度、スタンバイ、テキスト、カスタム） | P1 | 1 day | Not Started | T046 |
| **T048** | M5Stick ファームウェア拡張：SET_ITEM コマンド実装 | P1 | 2 days | Not Started | T026, T047 |
| **T049** | Raspberry Pi 再起動後アイテム復旧テスト（FR-014 検証） | P2 | 1 day | Not Started | T048 |

### キュー管理＆最新指示優先 (P1)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T050** | `src_pi/command_queue.py` 実装（enqueue, dequeue_latest, タイムアウト） | P1 | 2 days | Not Started | T044 |
| **T051** | キュー動作テスト：複数指示同時送信 → 最後のみ実行確認（SC-006） | P1 | 1 day | Not Started | T050, T040 |

### 自動補正＆曖昧性処理 (P2)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T052** | `src_pi/instruction_corrector.py` 実装（キーワード辞書、補正ロジック） | P2 | 2 days | Not Started | T037 |
| **T053** | 曖昧指示テスト：「色を変えて」→ 自動補正結果確認（FR-015） | P2 | 1 day | Not Started | T052, T040 |

### 履歴管理（リングバッファ） (P2)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T054** | `src_pi/history_manager.py` 実装（Ring Buffer max 100） | P2 | 1 day | Not Started | T044 |
| **T055** | Copilot から `GET_HISTORY` 指令テスト → 最新 10 件 JSON 確認 | P2 | 1 day | Not Started | T054, T040 |

### US-2, US-3 受け入れテスト (P1)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T056** | US-2 受け入れシナリオテスト：グラフ → 温度 → スタンバイ 2 秒以内切り替え（SC-005） | P1 | 2 days | Not Started | T049, T051 |
| **T057** | US-3 受け入れシナリオテスト：新規プリセット定義 → 描画確認 | P2 | 1 day | Not Started | T053, T056 |
| **T058** | Phase 3 完了チェックリスト＆高度機能設計書最終版 | P2 | 1 day | Not Started | T056, T057 |

---

## Phase 4: 検証＆デプロイメント (Week 14-16)

### エンドツーエンドテスト (P1)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T059** | Scenario A テスト：「赤い円を中央に」指示 → 5 秒以内表示（SC-001） | P1 | 1 day | Not Started | T058 |
| **T060** | Scenario B テスト：3 回連続指示 → 最後だけ反映（SC-006） | P1 | 1 day | Not Started | T058 |
| **T061** | Scenario C テスト：曖昧「色変えて」→ 自動補正実行（FR-015） | P1 | 1 day | Not Started | T058 |
| **T062** | Scenario D テスト：M5Stick 未接続 → ER-TIMEOUT＆リトライ確認（SC-003: 10 秒以内の失敗認識） | P1 | 1 day | Not Started | T058 |
| **T063** | 統計テスト：20 回反復 → 95% 成功率確認（SC-002） | P1 | 2 days | Not Started | T059～T062 |
| **T077** | 初見利用者ユーザビリティテスト（10 名中 90% 成功、SC-004） | P2 | 2 days | Not Started | T063 |

### ドキュメント完成 (P2)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T064** | システムアーキテクチャ図作成（3 層図：Copilot ↔ MCP ↔ M5Stick） | P2 | 1 day | Not Started | T032 |
| **T065** | M5Stick ファームウェア仕様書最終版 | P2 | 1 day | Not Started | T030 |
| **T066** | MCP ゲートウェイ API 仕様書最終版 | P2 | 1 day | Not Started | T043 |
| **T067** | アイテムレジストリスキーマドキュメント | P2 | 0.5 days | Not Started | T045 |
| **T068** | 非技術者向け説明資料作成（「VS Code から話しかけると M5Stick が変わる」） | P3 | 1 day | Not Started | T064 |
| **T069** | セットアップガイド作成（README.md） | P2 | 1 day | Not Started | T065, T066 |
| **T070** | トラブルシューティングガイド作成 | P3 | 1 day | Not Started | T069 |

### デプロイメント準備 (P2)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T071** | `setup_raspberry_pi.sh` 作成（Python, pyserial, dependencies） | P2 | 1 day | Not Started | T044 |
| **T072** | `setup_m5stick.sh` 作成（PlatformIO ビルド＆アップロード） | P2 | 1 day | Not Started | T044 |
| **T073** | セットアップスクリプト検証（クリーン RPi でテスト） | P2 | 1 day | Not Started | T071, T072 |

### デモンストレーション＆最終検証 (P2)

| ID | Task | Priority | Estimate | Status | Dependencies |
|---|---|---|---|---|---|
| **T074** | Live デモ準備＆実施記録（スクリーンショット＆動画） | P2 | 2 days | Not Started | T063 |
| **T075** | Phase 4 完了チェックリスト＆最終検証報告書 | P2 | 1 day | Not Started | T074 |
| **T076** | リポジトリ最終コミット＆タグ作成（v0.1.0） | P2 | 0.5 days | Not Started | T075 |

---

## タスク間の依存関係サマリ

```
Phase 0 (Infrastructure):
  T001 → T002, T003, T004
  T002 → T005, T006
  T003 → T005
  T005 → T011, T012

Phase 1 (Firmware):
  T015, T016, T017, T018 (Design)
  T019 → T021
  T022 → T023 → T024
  T021, T024 → T026
  T026 → T027 → T028, T029

Phase 2 (MCP):
  T031, T032, T033, T034 (Design)
  T032 → T078
  T033 → T035, T036, T037
  T035, T036 → T039
  T039 → T040, T041, T042, T043

Phase 3 (Features):
  T045 → T046, T047 → T048, T049
  T044 → T050, T054
  T037 → T052
  T049, T051 → T056, T057

Phase 4 (Validation):
  T058 → T059～T062 → T063 → T077
  → T064～T070 (Documents)
  → T071～T073 (Deployment)
  → T074, T075, T076 (Demo & Release)
```

---

## 優先度別タスク一覧

### P1 Critical (44 tasks) - Phase 0-3, 4 のメインパス

```
T001, T002, T003, T004, T005, T006, T007, T008, T009,
T011, T012,
T015, T016, T019, T020, T021, T022, T023, T024, T026, T027, T028,
T031, T032, T033, T035, T036, T037, T038, T039, T040, T041,
T045, T046, T047, T048, T050, T051,
T056,
T059, T060, T061, T062, T063
```

### P2 High (28 tasks) - 基盤強化＆ドキュメント

```
T010, T013, T014,
T017, T018, T025, T029, T030,
T043, T044,
T049, T052, T054, T055, T058,
T064, T065, T066, T067, T069, T071, T072, T073, T074, T075, T076, T077, T078
```

### P3 Medium (4 tasks) - ナイスツーハブ

```
T068, T070, T053, T057
```

---

## 見積もり集計

| Phase | Tasks | Total Estimate | Target Duration |
|-------|-------|-----------------|-----------------|
| **P0** | 14 | 14-15 days | 2 weeks |
| **P1** | 16 | 25-30 days | 3 weeks |
| **P2** | 15 | 21-26 days | 4 weeks |
| **P3** | 14 | 20-25 days | 5 weeks |
| **P4** | 19 | 20-24 days | 2 weeks |
| **Total** | **78** | **100-120 days** | **12-16 weeks** |

**実務的な配置**: 1.0 FTE Firmware + 1.0 FTE Backend (並列進行) → 12 週エスティメート

---

## ステータストラッキング

各タスクの進捗は **Git コミット**と **pull request** で追跡：
- T001-T010: Phase 0 branch (`phase-0-env`)
- T011-T030: Phase 1 branch (`phase-1-firmware`)
- T031-T044: Phase 2 branch (`phase-2-mcp`)
- T045-T058: Phase 3 branch (`phase-3-features`)
- T059-T077: Phase 4 branch (`phase-4-validation`)

**最終的なマージ**: `001-raspi-m5-display-control` ← 各フェーズブランチ PR

---

## Git ワークフロー

各フェーズのタスク完了時に phase ブランチを切り、PR で統合：

```bash
# Phase 0 完了時
git checkout -b phase-0-env
# T001～T014 のタスク実行＆コミット
git push origin phase-0-env
# PR 作成：phase-0-env → 001-raspi-m5-display-control

# 以降 Phase 1-4 も同様
git checkout -b phase-1-firmware
git checkout -b phase-2-mcp
git checkout -b phase-3-features
git checkout -b phase-4-validation
```

## テスト方法サマリ

### Phase 0 テスト
- **T011/T012**: minicom/screen で シリアル双方向テキスト確認
- **完了条件**: 「HELLO」送受信成功、レスポンス確認

### Phase 1 テスト
- **T021**: 統合テスト（DrawingEngine + LCD 実機描画）
- **T027**: HW 統合テスト（Raspberry Pi から DRAW_CIRCLE → M5Stick 表示）
- **T028**: エラーハンドリングテスト（ER-MALFORMED 応答）
- **完了条件**: 赤い円＆矩形表示確認、エラーコード返却

### Phase 2 テスト
- **T040**: E2E（Copilot → MCP → M5Stick）5 秒以内到着
- **T041**: エラーテスト（M5Stick 未接続 → ER-TIMEOUT）
- **T042**: 応答時間測定（複数回実行、平均値確認）
- **完了条件**: 5 秒 SLA 達成、タイムアウト処理確認

### Phase 3 テスト
- **T049**: Raspberry Pi 再起動 → JSON ファイル存在確認
- **T051**: 複数指示同時送信 → 最後の指示のみ実行確認
- **T053**: 曖昧指示「色を変えて」→ 自動補正実行確認
- **T056**: アイテム切り替え 3 回（グラフ→温度→スタンバイ）2秒以内
- **完了条件**: US-2/US-3 受け入れシナリオ全て pass

### Phase 4 テスト
- **T063**: 統計テスト 20 回反復 → 95% 成功率確認
- **T077**: 初見利用者ユーザビリティテスト（10 名中 90% 成功）
- **T074**: Live デモ（スクリーンショット＆動画記録）
- **完了条件**: 全 SC-001～SC-006 検証pass、SC-004 ユーザビリティ達成、デモ実施

---

**Task Status**: 🟡 Draft (Ready for Phase 0 Execution)  
**Last Updated**: 2026-03-04  
**Next Action**: Git phase-0-env branch 作成 → T001 開始
