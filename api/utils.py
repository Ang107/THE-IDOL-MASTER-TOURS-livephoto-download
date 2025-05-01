# utils.py
from collections import OrderedDict
import datetime as dt
from zoneinfo import ZoneInfo
import aiohttp, io, zipfile, os, time, asyncio


BASE = "https://livephoto.idolmaster-tours-w.bn-am.net/livephoto/{code}/{n}.jpeg"

_img_cache: OrderedDict[str, list[bytes]] = OrderedDict()
MAX_ITEMS = 100


async def _fetch_one(session, url):
    async with session.get(url) as r:
        return await r.read() if r.status == 200 else None


async def fetch_all(code: str) -> list[bytes]:
    if code in _img_cache:
        imgs = _img_cache.get(code)
        return imgs

    async with aiohttp.ClientSession() as s:
        tasks = [_fetch_one(s, BASE.format(code=code, n=i)) for i in range(3)]
        imgs = await asyncio.gather(*tasks)
        imgs = [b for b in imgs if b]

    _img_cache[code] = imgs
    if len(_img_cache) > MAX_ITEMS:
        _img_cache.popitem(last=False)
    return imgs


def timestamp() -> str:
    """日本時間 (JST) のタイムスタンプを返す"""
    jst = ZoneInfo("Asia/Tokyo")
    return dt.datetime.now(jst).strftime("%Y_%m_%d_%H_%M_%S")


def make_zip(all_imgs: list[list[bytes]], ts: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as zf:
        for idx, imgs in enumerate(all_imgs, 1):
            folder = f"{idx:02}"
            for j, raw in enumerate(imgs, 1):
                name = f"{ts}_{folder}_{j}.jpeg"
                zf.writestr(os.path.join(folder, name), raw)
                zf.writestr(os.path.join("all", name), raw)
    return buf.getvalue()
