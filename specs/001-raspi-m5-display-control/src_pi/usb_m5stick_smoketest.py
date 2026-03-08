"""
USB smoke test for M5StickC Plus2 via MCPGateway components.

Run:
  /home/meiden/work/github/spec_kit/.venv/bin/python usb_m5stick_smoketest.py
"""

import asyncio
from mcp_gateway import MCPGateway


async def main() -> None:
    gateway = MCPGateway(serial_port="/dev/ttyACM0", baud_rate=115200)

    ok = await gateway.serial_manager.init()
    print("SERIAL_INIT", ok)
    if not ok:
        return

    try:
        ping_result = await gateway.ping({})
        print("PING", ping_result)

        draw_circle = await gateway.draw({"instruction": "赤い円を中央に描画"})
        print("DRAW_CIRCLE", draw_circle)

        draw_text = await gateway.draw({"instruction": "中央に『HELLO』を白で表示"})
        print("DRAW_TEXT", draw_text)

        clear_result = await gateway.draw({"instruction": "画面をクリア"})
        print("CLEAR", clear_result)

        history = await gateway.get_history({"limit": 5})
        print("HISTORY", history)
    finally:
        await gateway.serial_manager.close()


if __name__ == "__main__":
    asyncio.run(main())
