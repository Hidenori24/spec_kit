# USB 接続テストメモ

このディレクトリで実行する M5StickC Plus2 の USB スモークテスト。

## ファイル
- [usb_m5stick_smoketest.py](usb_m5stick_smoketest.py)

## 実行
- `cd specs/001-raspi-m5-display-control/src_pi`
- `/home/meiden/work/github/spec_kit/.venv/bin/python usb_m5stick_smoketest.py`

## テスト内容
1. シリアル初期化 (`/dev/ttyACM0`, 115200)
2. `ping`
3. 自然言語描画（円）
4. 自然言語描画（テキスト）
5. 画面クリア
6. 履歴取得

## 成功条件
- `PING` が `online: True`
- `DRAW_*` / `CLEAR` の `status` が `OK`
- `HISTORY` に実行結果が記録される
