# Feature Specification: Raspberry Pi 5 + M5StickC Plus2 AI-Driven Display System

**Feature Branch**: `001-raspi-m5-display-control`  
**Created**: 2026-03-04  
**Status**: Draft  
**Input**: User description: 
- Goal: Freely draw and change M5StickC Plus2 screen from Raspberry Pi 5
- Enable AI-driven (VS Code + Copilot) display generation from Raspberry Pi
- Support simple item switching, MCP-based interface, wired serial communication

## User Scenarios & Testing *(mandatory)*

### User Story 1 - AI駆動での自由な画面描画 (Priority: P1)

利用者（開発者）は VS Code + GitHub Copilot から自然言語で画面描画を指示し、
M5StickC Plus2 の画面がそのまま更新されるようにしたい。
MCP（Model Context Protocol）をインターフェースとして、Copilot の指示が
直接ラズパイ上の描画エンジンに伝わる流れを実現したい。

**Why this priority**: このプロジェクトの最大価値は「AI駆動で自由に画面描画できる」こと。
これなしに他の機能はすべて意味を失うため。

**Independent Test**: 利用者が VS Code 内で「赤い円を画面中央に描画」のような
自然言語指示を与え、M5Stick 画面に対応する描画が 5 秒以内に現れることを確認できれば価値提供が成立する。

**Acceptance Scenarios**:

1. **Given** M5StickC Plus2 が受信待ちで、MCP ゲートウェイが起動している,
   **When** 利用者が VS Code/Copilot から「青い矩形を左上に配置」と指示する,
   **Then** M5Stick 画面に指示どおりの描画が現れる
2. **Given** MS Stick と Raspberry Pi 5 が有線（シリアル）で接続している,
   **When** 利用者が新しい描画指示を連続して送る,
   **Then** 最新の指示内容がそのまま画面に反映される

---

### User Story 2 - 複数描画アイテムの簡単切り替え (Priority: P2)

利用者は「グラフ表示」「温度センサー値」「スタンバイ画面」など複数の描画アイテムを
事前に定義し、必要に応じてワンコマンドで切り替えたい。
M5Stick の限られた VRAM と表示サイズの中で、複数の「描画モード」を簡単に管理しながら
高速に切り替えられるようにしたい。

**Why this priority**: IoT 環境では画面表示を動的に切り替える需要が多い。
シンプルに「モード A」「モード B」を選べるようにすることで、
運用の使いやすさが大きく向上するため。

**Independent Test**: 利用者が事前に登録した 3 つの描画アイテム（例：グラフ・温度・テキスト）を、
順序よく切り替え指示し、毎回 2 秒以内に M5Stick 画面が適切に更新されることを確認できる。

**Acceptance Scenarios**:

1. **Given** 複数の描画アイテムが事前に定義されている,
   **When** 利用者が「アイテム: グラフを表示」と指示する,
   **Then** M5Stick 画面がグラフのみを表示する状態に即座に変わる
2. **Given** 現在グラフ表示なら、**When** 「アイテム: 温度値を表示」と指示する,
   **Then** グラフが消え、温度値だけが表示される

---

### User Story 3 - MCP ドリブンな描画プリセット (Priority: P3)

利用者は、新しい描画パターンを簡単に追加できるようにしたい。
Copilot の自然言語指示に基づいて、テンプレートやプリセット化された描画コンポーネント
（ボタン、ゲージ、リスト など）を組み合わせ、M5Stick で動的に表現できる仕組みが欲しい。

**Why this priority**: 最初は固定的なアイテム切り替えで OK だが、
将来的に Copilot が新しい画面デザインを提案・実装できるようになると、UX が大きく向上する。

**Independent Test**: Copilot との複数ラウンドの対話を通じて、
市松模様やプログレスバーなどの新規描画パターンが M5Stick で実現されることを確認できる。

**Acceptance Scenarios**:

1. **Given** MCP を通じて新規レイアウト「2 行テキスト + 下部ボタン」が定義される,
   **When** 次回の指示でそのレイアウトが参照される,
   **Then** M5Stick が複数行テキストと下部ボタンを正しく描画する
2. **Given** Copilot が「プログレスバーを表示」と提案する,
   **When** 利用者がそれを許可する,
   **Then** M5Stick にプログレスバーが描画され、進捗を視覚化できる

### Edge Cases

- MCP ゲートウェイがタイムアウト（応答なし）した場合でも、利用者が指示を再送できる状態を維持すること
- 複数の描画指示が短時間に queue させられた場合、最終的に最新の指示のみが M5Stick に適用されること
- Copilot が曖昧な指示（「色を変えて」など）を生成した場合、M5Stick が前状態を保ちながら警告を返すこと
- M5Stick の VRAM 制約で指定内容が収まらない場合、表示崩れではなく明白な失敗コード（例：ER-SIZE）を返すこと
- 有線シリアルが瞬間的に切断・再接続された場合、次の指示で自動的に再同期されること

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow a user on Raspberry Pi 5 to request replacement of the current M5Stick screen content via VS Code + Copilot interface using MCP.
- **FR-002**: MCP gateway on Raspberry Pi MUST translate Copilot's natural language drawing instructions into deterministic device commands.
- **FR-003**: System MUST serialize drawing commands and send them to M5StickC Plus2 via wired (serial/UART) protocol with configurable baud rate.
- **FR-004**: System MUST apply a new screen update so that previous screen content is replaced by the latest requested content.
- **FR-005**: System MUST return a clear success or failure result for each screen update request (e.g., "OK", "ER-TIMEOUT", "ER-SIZE", "ER-MALFORMED").
- **FR-006**: System MUST support at least 5 predefined display items (graph, temperature sensor, standby screen, text log, custom layout) selectable by user or Copilot instruction.
- **FR-007**: Users MUST be able to switch between predefined display items in under 2 seconds with a single command.
- **FR-008**: System MUST maintain an item registry (configuration) listing all available display items, their layouts, and refresh logic.
- **FR-009**: System MUST prevent partially updated or visually corrupted output from being treated as a successful update.
- **FR-010**: System MUST validate incoming screen update content against M5Stick VRAM and display size constraints before applying it.
- **FR-011**: System MUST support dynamic addition of new display patterns via MCP instruction without code rebuild.
- **FR-012**: System MUST keep a retrievable history of recent update attempts including request time, request content (abbreviated), and result.

### Key Entities *(include if feature involves data)*

- **Display Update Request**: 1 回の画面更新要求。要求時刻、要求内容（自然言語またはアイテム ID）、対象デバイス識別子、要求元（Copilot/ユーザ）識別子を持つ。
- **Display Update Result**: 更新要求に対する結果。成功/失敗、失敗時の理由コード（ER-TIMEOUT、ER-SIZE など）、確定時刻を持つ。
- **Display Item** (新規): 再利用可能な表示パターン。アイテム ID、名前、レイアウト定義、更新ロジック、VRAM 要件を持つ。
- **MCP Command** (新規): Copilot → MCP ゲートウェイ間のプロトコルメッセージ。命令タイプ、パラメータ、シーケンス番号、タイムスタンプを持つ。
- **Serial Message**: MCP ゲートウェイ → M5StickC Plus2 間の通信フレーム。バイナリエンコード、チェックサム、受信確認フラグを持つ。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Copilot 経由で画面更新を指示してから M5Stick の表示置き換え完了を確認するまでが、通常条件（MCP + シリアル接続正常）で 5 秒以内に収まる。
- **SC-002**: 正常接続時の更新成功率が 95% 以上である。MCP timeout、シリアル再接続後も自動復帰可能。
- **SC-003**: 更新失敗時に、利用者が 10 秒以内に失敗理由コード（ER-SIZE、ER-TIMEOUT など）を認識できる。
- **SC-004**: 初見利用者（AI 駆動に慣れたステークホルダー）の 90% 以上が、Copilot への自然言語指示のみで 1 回以上の画面更新を完了できる。
- **SC-005**: 定義済み display item の切り替えが 2 秒以内に完了する（再描画含む）。
- **SC-006**: MCP ゲートウェイが queue 管理により、短時間の連続指示でも最後の指示のみが適用される。

## Technology Stack & Code Quality

### Approved Technology

- **Firmware (M5StickC Plus2)**: C++ with PlatformIO framework
- **Host (Raspberry Pi 5)**: Python 3.10+ for coordination and scripting
- **Editor & AI Assistance**: VS Code with GitHub Copilot
- **Version Control**: Git and GitHub

### Code Quality Requirements

- Code MUST prioritize maintainability: clear naming, separation of concerns, minimal coupling.
- Major design decisions and non-obvious implementation choices MUST be documented in code comments.
- Architecture review is required before introducing new major subsystems.
- Per Constitution Principle VII: Testing focuses on critical device I/O, communication protocols, and error handling. Unit tests for internal helpers are optional.

### Rationale

This focused technology stack and code clarity requirements reflect the small-team, IoT
environment context. Clean, maintainable code is critical for safe operations on physical
hardware without extensive test automation.
