# Serial Protocol Contract (Draft)

**Feature Branch**: `001-raspi-m5-display-control`
**Created**: 2026-03-04
**Status**: Draft

## Overview
Defines the serial protocol between Raspberry Pi 5 and M5StickC Plus2.

## Transport
- UART, default baud rate: 115200
- Wired connection only (demo environment)
- Optional CRC-16 checksum

## Command Format (Text-based)
- `DRAW_CIRCLE <x> <y> <r> <color>`
- `DRAW_RECT <x> <y> <w> <h> <color>`
- `DRAW_TEXT <x> <y> <text> <color>`
- `CLEAR_SCREEN`
- `SET_ITEM <item_id>`
- `PING`

## Response Format
- Success: `OK`
- Failure: `ER-<CODE>:<reason>`

## Error Codes
- `ER-TIMEOUT`
- `ER-SIZE`
- `ER-MALFORMED`

## Notes
- Device should reject commands exceeding VRAM/display constraints.
- Partial draws must not be treated as success.

## Change Log
- 2026-03-04: Initial draft created
