# Research Notes: Raspberry Pi 5 + M5StickC Plus2 Display Control

**Feature Branch**: `001-raspi-m5-display-control`
**Created**: 2026-03-04
**Status**: Draft

## Scope
Research notes for MCP integration, serial transport, and device constraints. This document records decisions and external references that inform implementation.

## Decisions & Assumptions
- **No authentication** for MCP gateway (demo/trusted wired environment). (FR-013)
- **Ring buffer** retains last 100 requests. (FR-012)
- **Item registry persistence** via local JSON file on Raspberry Pi. (FR-014)
- **Auto-correct ambiguous instructions** to nearest valid command with correction details returned. (FR-015)
- **Default baud rate**: 115200 for serial/UART. (FR-003)

## MCP Integration
- MCP gateway receives natural-language instructions from Copilot.
- Translation strategy: keyword-based mapping, extensible dictionary.
- JSON-RPC message format used for requests and responses.

## Serial Transport
- Wired serial/UART between Raspberry Pi 5 and M5StickC Plus2.
- Response format: `OK` or `ER-<CODE>:<reason>`.
- CRC-16 recommended for reliability (Phase 1 tasks).

## Device Constraints
- Target device: M5StickC Plus2.
- VRAM and display size constraints must be validated prior to draw (FR-010).

## References
- Internal spec: `specs/001-raspi-m5-display-control/spec.md`
- Plan: `specs/001-raspi-m5-display-control/plan.md`
- Tasks: `specs/001-raspi-m5-display-control/tasks.md`

## Open Questions
- None currently.

## Change Log
- 2026-03-04: Initial draft created
