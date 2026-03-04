# Data Model: Raspberry Pi 5 + M5StickC Plus2 AI-Driven Display System

**Feature Branch**: `001-raspi-m5-display-control`
**Created**: 2026-03-04
**Status**: Draft

## Overview
This document defines the core entities used across the MCP gateway and M5Stick firmware pipeline. It follows the specification requirements (FR-001 to FR-015) and supports the success criteria (SC-001 to SC-006).

## Entity Model

### DisplayUpdateRequest
**Purpose**: Represents a single screen update request initiated by a user or Copilot.

**Fields**:
- `request_id` (string, unique)
- `timestamp` (ISO8601 string)
- `source` (enum: `copilot`, `user`)
- `target_device_id` (string)
- `content_type` (enum: `natural_language`, `item_id`)
- `content` (string; NL prompt or item ID)
- `priority` (enum: `normal`, `latest_only`)

**Notes**:
- The latest-only behavior is enforced by the CommandQueue per SC-006.

### DisplayUpdateResult
**Purpose**: Represents the outcome of a display update request.

**Fields**:
- `request_id` (string, foreign key to DisplayUpdateRequest)
- `timestamp` (ISO8601 string)
- `status` (enum: `OK`, `ER-TIMEOUT`, `ER-SIZE`, `ER-MALFORMED`, `ER-UNKNOWN`)
- `message` (string; human-readable status)
- `correction` (optional string; auto-correction details per FR-015)
- `duration_ms` (integer)

### DisplayItem
**Purpose**: Reusable display pattern stored in a local registry.

**Fields**:
- `item_id` (string)
- `name` (string)
- `layout` (JSON object)
- `update_logic` (string; reference to handler or template)
- `vram_bytes` (integer)
- `persisted` (boolean)

**Notes**:
- Registry is persisted to local JSON file per FR-014.

### MCPCommand
**Purpose**: Structured message between Copilot and MCP gateway.

**Fields**:
- `command_type` (enum: `DRAW`, `SET_ITEM`, `GET_HISTORY`, `PING`)
- `sequence_id` (integer)
- `timestamp` (ISO8601 string)
- `params` (JSON object)

**Notes**:
- Commands are translated into device-level serial messages.

### SerialMessage
**Purpose**: Low-level frame sent from MCP gateway to M5Stick.

**Fields**:
- `header` (string)
- `payload` (bytes)
- `checksum` (integer, CRC-16)
- `ack_required` (boolean)

**Notes**:
- Response format is `OK` or `ER-<CODE>:<reason>`.

## Relationships
- DisplayUpdateRequest 1→1 DisplayUpdateResult
- DisplayItem is referenced by DisplayUpdateRequest when `content_type = item_id`
- MCPCommand can encapsulate DisplayUpdateRequest or system commands (e.g., GET_HISTORY)
- SerialMessage is generated from MCPCommand

## Validation Rules
- Reject content if VRAM constraints are exceeded (FR-010)
- Always return explicit status codes (FR-005)
- Enforce ring buffer size of 100 history entries (FR-012)

## Change Log
- 2026-03-04: Initial draft created
