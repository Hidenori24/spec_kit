<!--
Sync Impact Report for v1.1.0 Amendment
- Version change: 1.0.0 → 1.1.0 (MINOR: new principles + technology section)
- Added principles:
  - VI. Clean Code & Maintainable Architecture
  - VII. Selective, Focused Testing
- Added sections:
  - Approved Technology Stack
  - Raspberry Pi 5 + M5StickC Plus2 Integration Requirements
- Updated sections:
  - Hardware & Safety Constraints (firmware update reversibility added)
  - Development Workflow & Quality Gates (architecture review + documentation)
- Removed sections:
  - None
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md (add clean code architecture gate)
  - ✅ .specify/templates/spec-template.md (add tech stack requirements)
  - ✅ .specify/templates/tasks-template.md (clarify test selectivity)
- Follow-up TODOs:
  - None
-->

# M5 Display Control Constitution

## Core Principles

### I. Human-Directed Device Control
All display changes MUST be initiated by an explicit human instruction from VS Code on
the Raspberry Pi 5 environment. The system MUST never auto-push unsolicited screen
updates to the device.

Rationale: this project exists as an operator-controlled display system, so intent and
traceability are mandatory.

### II. M5StickC Plus2 Compatibility
The first-class target device MUST be M5StickC Plus2. Any implementation that changes
transport, drawing protocol, or screen layout handling MUST preserve behavior on
M5StickC Plus2 or include an approved migration plan.

Rationale: hardware-specific constraints (screen size, memory, communication behavior)
define correctness for this system.

### III. Deterministic Display Commands (NON-NEGOTIABLE)
Each display request MUST produce a deterministic result: success with rendered content
or failure with explicit reason. Ambiguous outcomes (partial draw treated as success,
silent timeout, or unknown final state) MUST be rejected.

Rationale: operators need predictable behavior to safely use hardware in real workflows.

### IV. Hardware-in-the-Loop Verification
Changes affecting command encoding, transport, retry logic, or render pipeline MUST be
validated with both: (a) reproducible simulation/mocked tests and (b) at least one
hardware-in-the-loop verification run against a connected M5StickC Plus2.

Rationale: simulation catches regressions quickly, and device validation confirms
real-world correctness.

### V. Observable and Recoverable Operations
Every display operation MUST emit structured, human-readable result data including
request time, target device identity, and final status. Failures MUST support immediate
retry without restarting the whole system.

Rationale: operations on physical devices require fast diagnosis and safe recovery.

### VI. Clean Code & Maintainable Architecture
All code MUST prioritize long-term maintainability: clear naming, separation of concerns,
minimal coupling, and predictable control flow. Major design decisions MUST be
documented. Architecture reviews are required before major subsystem changes.

Rationale: a small team operating physical hardware needs high code clarity to avoid
costly mistakes and enable rapid iterations.

### VII. Selective, Focused Testing
Testing MUST cover critical device I/O, communication protocols, and error paths. Unit
tests for internal helper functions are not required; focus test effort on integration
and contract validation. Mocking device behavior is acceptable for development; final
validation MUST occur on hardware.

Rationale: testing IoT systems is resource-constrained; better to test thoroughly where
it matters (device contracts) than comprehensively where it does not.

## Approved Technology Stack

All new code MUST use one of the following approved languages and tooling:

- **Embedded/Device Side**: C++ (PlatformIO framework) for M5StickC Plus2
- **Coordination/Host Side**: Python 3.10+ for Raspberry Pi 5 scripting and integration
- **Editor & Tooling**: VS Code, GitHub Copilot for development assistance
- **Build/Deployment**: PlatformIO for firmware builds, pip/venv for Python environments
- **Communication**: Serial or network protocols as defined per feature specification
- **Version Control**: Git + GitHub

Rationale: this focused stack simplifies onboarding, reduces maintenance burden, and
ensures team familiarity. Any deviation MUST be justified in the plan and approved.

## Raspberry Pi 5 + M5StickC Plus2 Integration Requirements

- **Deployment Model**: M5StickC Plus2 firmware is built on Raspberry Pi 5; deployment
  happens directly from the Raspberry Pi 5 environment.
- **VS Code Integration**: Feature is developed and invoked from VS Code running on
  Raspberry Pi 5, with Copilot-assisted code generation and editing.
- **Serial/Network Communication**: Direct serial connection or network-based messaging
  between Raspberry Pi 5 host process and M5StickC Plus2 is the primary control channel.
- **Recovery Paths**: In case of device disconnect or timeout, operator MUST be able to
  reconnect and resume operations without full process restart.
- **Resource Constraints**: Code MUST account for limited memory and power on
  M5StickC Plus2; display updates MUST be batched and optimized to avoid thermal stress
  or unexpected shutdowns.

## Hardware & Safety Constraints

- All implementation decisions MUST prioritize stable operation on Raspberry Pi 5 with a
  physically connected M5StickC Plus2.
- Display payload validation MUST run before draw execution; invalid payloads MUST fail
  fast with actionable errors.
- Any feature that increases write frequency to the display MUST document thermal/power
  impact assumptions and safe operating bounds.
- Secrets or credentials used for device communication MUST NOT be hard-coded in source.
- Firmware updates to M5StickC Plus2 MUST be reversible or include a fallback version.

## Development Workflow & Quality Gates

1. **Specification first**: Every feature starts with `/speckit.specify`, followed by
   `/speckit.clarify` when needed.
2. **Plan and tasks required**: `/speckit.plan` and `/speckit.tasks` MUST exist before
   implementation starts.
3. **Architecture review**: Features affecting system-level design or introducing new
   subsystems MUST include an architecture decision document in the plan.
4. **Validation gates**:
   - Changes touching device I/O MUST include test evidence and hardware-in-the-loop
     verification notes before merge.
   - Code MUST pass style/clarity review (e.g., naming conventions, modular design).
   - Critical paths (command encoding, display rendering, error handling) MUST have
     focused test coverage.
5. **Release readiness**: Operator quickstart steps for running from VS Code on
   Raspberry Pi MUST be updated when behavior changes.
6. **Documentation**: Architecture decisions and non-obvious implementation choices MUST
   be documented in code comments or plan artifacts.

## Governance

This constitution supersedes conflicting local practices for this repository.

- **Amendment process**: Changes require a documented rationale, impact assessment on
  active specs/tasks, and approval from maintainers.
- **Versioning policy**: Use semantic versioning for this constitution.
  - MAJOR: Backward incompatible governance changes or principle removals/redefinitions.
  - MINOR: New principle/section or materially expanded mandatory guidance.
  - PATCH: Wording clarifications, typo fixes, and non-semantic edits.
- **Compliance review**: Each plan and pull request MUST include a constitution check
  result, including explicit justification for any temporary violation.
- **Operational guidance source**: Use `.specify` templates and generated feature
  artifacts as the authoritative workflow documents.

**Version**: 1.1.0 | **Ratified**: 2026-03-04 | **Last Amended**: 2026-03-04
