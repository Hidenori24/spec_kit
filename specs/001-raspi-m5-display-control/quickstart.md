# Quickstart: Raspberry Pi 5 + M5StickC Plus2 Display Control

**Feature Branch**: `001-raspi-m5-display-control`
**Created**: 2026-03-04
**Status**: Draft

## Prerequisites
- Raspberry Pi 5 with Raspberry Pi OS 64-bit
- M5StickC Plus2
- USB-UART cable
- VS Code + GitHub Copilot on Raspberry Pi 5

## Phase 0 Minimal Setup
1. Install Python 3.10+ on Raspberry Pi 5.
2. Install PlatformIO CLI on Raspberry Pi 5.
3. Install VS Code + GitHub Copilot on Raspberry Pi 5.
4. Clone the repository and checkout `001-raspi-m5-display-control`.
5. Wire UART: Raspberry Pi UART ↔ M5Stick RX/TX.

## Basic Connectivity Test
- Open serial terminal (minicom/screen) at 115200.
- Send `HELLO` from Raspberry Pi and verify M5Stick receives.
- Confirm M5Stick can send a response back to Raspberry Pi.

## Firmware Smoke Test
- Build and upload an empty sketch via PlatformIO on Raspberry Pi 5.
- Verify the device boots and screen updates without errors.

## MCP Gateway Smoke Test (later phase)
- Run MCP gateway on Raspberry Pi 5.
- Send a Copilot instruction like “赤い円を中央に描画”.
- Confirm M5Stick screen updates within 5 seconds.

## Troubleshooting
- If serial communication fails, verify wiring, UART port, and baud rate.
- If upload fails, confirm PlatformIO installation and USB permissions.

## Change Log
- 2026-03-04: Initial draft created
