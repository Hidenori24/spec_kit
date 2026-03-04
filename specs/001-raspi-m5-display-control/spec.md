# Feature Specification: Raspberry Pi 5 から M5Stick 画面更新

**Feature Branch**: `001-raspi-m5-display-control`  
**Created**: 2026-03-04  
**Status**: Draft  
**Input**: User description: "ラズパイ5からm5 stickの画面描画を書き換えたい。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 画面内容の即時更新 (Priority: P1)

利用者は Raspberry Pi 5 側で新しい表示内容を指定し、M5Stick 側の画面をすぐに置き換えたい。

**Why this priority**: この機能の中核価値そのものであり、成立しないと他の改善が意味を持たないため。

**Independent Test**: 利用者が任意の表示内容を 1 回送信し、M5Stick の画面が指定内容に更新されることを確認できれば価値提供が成立する。

**Acceptance Scenarios**:

1. **Given** M5Stick が受信待ち状態である, **When** 利用者が Raspberry Pi 5 から新しい画面内容を送る, **Then** M5Stick 画面が新しい内容に置き換わる
2. **Given** すでに別の表示内容が画面に出ている, **When** 利用者が別内容を送る, **Then** 以前の内容が残らず新内容が表示される

---

### User Story 2 - 更新失敗の把握 (Priority: P2)

利用者は、送信した更新が反映されなかった場合に、失敗を認識して再試行したい。

**Why this priority**: 運用時のトラブル切り分けに直結し、実用性を大きく左右するため。

**Independent Test**: 意図的に受信不可状態を作って送信し、利用者が失敗状態を認識できる表示または通知を確認できる。

**Acceptance Scenarios**:

1. **Given** M5Stick が更新を受け取れない状態である, **When** 利用者が更新を送る, **Then** 利用者が失敗を認識できる結果が返る

---

### User Story 3 - 定型レイアウトの再利用 (Priority: P3)

利用者はよく使う表示パターンを再利用し、短時間で画面を書き換えたい。

**Why this priority**: 継続運用での作業時間を削減し、更新ミスを減らせるため。

**Independent Test**: あらかじめ定義した表示パターンを選択して送信し、意図どおり同じレイアウトが再現されることを確認できる。

**Acceptance Scenarios**:

1. **Given** 利用者が定型表示パターンを保持している, **When** そのパターンを選択して送信する, **Then** M5Stick に対応する画面が表示される

### Edge Cases

- M5Stick が未接続または一時的に応答不能な場合でも、利用者が再試行可能な状態を維持できること
- 画面サイズ制約を超える内容が指定された場合、表示崩れではなく利用者が理解できる失敗扱いになること
- 連続した更新要求が短時間に複数来た場合、最終的に適用された内容が利用者に判別可能であること

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow a user on Raspberry Pi 5 to request replacement of the current M5Stick screen content.
- **FR-002**: System MUST apply a new screen update so that previous screen content is replaced by the latest requested content.
- **FR-003**: System MUST return a clear success or failure result for each screen update request.
- **FR-004**: Users MUST be able to retry a failed update request without restarting the entire workflow.
- **FR-005**: System MUST prevent partially updated or visually corrupted output from being treated as a successful update.
- **FR-006**: System MUST validate incoming screen update content against allowed display constraints before applying it.
- **FR-007**: System MUST keep a retrievable history of recent update attempts including request time and result.
- **FR-008**: System MUST support at least one reusable predefined display pattern selectable by the user.

### Key Entities *(include if feature involves data)*

- **Display Update Request**: 1 回の画面更新要求。要求時刻、要求内容、対象デバイス識別子、要求元識別子を持つ。
- **Display Update Result**: 更新要求に対する結果。成功/失敗、理由、確定時刻を持つ。
- **Display Template**: 再利用可能な表示パターン。テンプレート名と表示内容定義を持つ。

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 利用者が画面更新を開始してから M5Stick の表示置き換え完了を確認するまでが、通常条件で 5 秒以内に収まる。
- **SC-002**: 正常接続時の更新成功率が 95% 以上である。
- **SC-003**: 更新失敗時に、利用者が 10 秒以内に失敗理由を認識できる。
- **SC-004**: 初見利用者の 90% 以上が説明なしで 1 回以上の画面更新を完了できる。

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
