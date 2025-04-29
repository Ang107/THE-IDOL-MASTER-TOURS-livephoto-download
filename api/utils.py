import datetime as dt
import aiohttp, asyncio, io, zipfile, os
from typing import List
from zoneinfo import ZoneInfo

BASE = "https://livephoto.idolmaster-tours-w.bn-am.net/livephoto/{code}/{n}.jpeg"


async def _fetch_one(session, url):
    async with session.get(url) as r:
        return await r.read() if r.status == 200 else None


async def fetch_all(code: str) -> List[bytes]:
    async with aiohttp.ClientSession() as s:
        tasks = [_fetch_one(s, BASE.format(code=code, n=i)) for i in range(3)]
        imgs = await asyncio.gather(*tasks)
        return [b for b in imgs if b]


def timestamp() -> str:
    """日本時間 (JST) のタイムスタンプを返す"""
    jst = ZoneInfo("Asia/Tokyo")
    return dt.datetime.now(jst).strftime("%Y_%m_%d_%H_%M_%S")


def make_zip(all_imgs):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        for idx, imgs in enumerate(all_imgs, 1):
            for j, raw in enumerate(imgs):
                zf.writestr(os.path.join(f"{idx:02}", f"{j}.jpeg"), raw)
    return buf.getvalue()
