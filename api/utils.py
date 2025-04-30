# utils.py
import datetime as dt
from zoneinfo import ZoneInfo
import aiohttp, io, zipfile, os, time, asyncio


BASE = "https://livephoto.idolmaster-tours-w.bn-am.net/livephoto/{code}/{n}.jpeg"

# キャッシュ: code -> (fetch_time, list[bytes])
_img_cache: dict[str, tuple[float, list[bytes]]] = {}
_CACHE_TTL = 15 * 60  # 15 分


async def _fetch_one(session, url):
    async with session.get(url) as r:
        return await r.read() if r.status == 200 else None


async def fetch_all(code: str) -> list[bytes]:
    # ① キャッシュが有効ならそれを返す
    entry = _img_cache.get(code)
    if entry:
        print("used cache")
        return entry[1]

    # ② そうでなければ外部フェッチ
    async with aiohttp.ClientSession() as s:
        tasks = [_fetch_one(s, BASE.format(code=code, n=i)) for i in range(3)]
        imgs = await asyncio.gather(*tasks)
        imgs = [b for b in imgs if b]

    # ③ キャッシュに保存（クリアは別タスクで行う）
    _img_cache[code] = (time.time(), imgs)
    return imgs


def cleanup_cache():
    """キャッシュのうち、TTL を過ぎたエントリを削除する"""
    now = time.time()
    expired = [code for code, (ts, _) in _img_cache.items() if now - ts > _CACHE_TTL]
    for code in expired:
        _img_cache.pop(code, None)


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
