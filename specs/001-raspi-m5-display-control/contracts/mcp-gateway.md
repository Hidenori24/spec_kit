# MCP Gateway Contract (Draft)

**Feature Branch**: `001-raspi-m5-display-control`
**Created**: 2026-03-04
**Status**: Draft

## Overview
Defines the MCP request/response contract between Copilot and the Raspberry Pi MCP gateway.

## Request (JSON-RPC)
- `id` (string/int)
- `method` (string)
- `params` (object)

### Supported Methods
- `draw`: natural language draw request
- `set_item`: switch to a predefined display item
- `get_history`: retrieve recent history entries
- `ping`: connectivity check

## Response
- `id` (string/int)
- `result` (object)
- `error` (object; optional)

### Result Fields
- `status`: `OK` or `ER-<CODE>`
- `message`: human-readable message
- `correction`: auto-correction details (optional)
- `duration_ms`: end-to-end duration

## Error Codes
- `ER-TIMEOUT`: device did not respond within timeout
- `ER-SIZE`: VRAM/display constraint violation
- `ER-MALFORMED`: invalid payload or command
- `ER-UNKNOWN`: unexpected error

## Notes
- No authentication (demo/trusted wired environment).
- Latest-only behavior enforced when multiple requests are queued.

## Change Log
- 2026-03-04: Initial draft created
