# logger.py
import os
import asyncio
import datetime as dt
from zoneinfo import ZoneInfo
import aiohttp

# Render の環境変数に設定しておく
_WEBHOOK = os.getenv(
    "DISCORD_WEBHOOK_URL"
)  # 例: https://discord.com/api/webhooks/xxxxxxxx

print(f"{_WEBHOOK=}")


async def _push_to_discord(msg: str) -> None:
    """Discord にメッセージを飛ばす（失敗しても例外を外へ出さない）"""
    if not _WEBHOOK:
        return  # 未設定なら何もしない
    try:
        async with aiohttp.ClientSession() as s:
            await s.post(_WEBHOOK, json={"content": msg}, timeout=10)
    except Exception as e:
        # Discord 側が落ちていてもアプリ本体は止めない
        print(f"[LOGGER] Discord push failed: {e}", flush=True)


def log(message: str) -> None:
    """タイムスタンプ付きでログを出力し、Discord へも送信"""
    ts = dt.datetime.now(ZoneInfo("Asia/Tokyo")).strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{ts}] {message}"
    print(msg, flush=True)  # 標準出力へ
    asyncio.create_task(_push_to_discord(msg))  # 非同期に Discord へ
