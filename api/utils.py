# utils.py
from collections import OrderedDict
import datetime as dt
from zoneinfo import ZoneInfo
import aiohttp, io, zipfile, os, asyncio, re
from html.parser import HTMLParser
from urllib.parse import urljoin

# ──────────────────── 定数 ────────────────────
BASE_PAGE = "https://livephoto.idolmaster-tours-w.bn-am.net/livephoto/{code}/"
_img_cache: OrderedDict[str, list[bytes]] = OrderedDict()
MAX_ITEMS = 100


# ──────────────────── HTML パーサ ───────────────
class _ImgSrcParser(HTMLParser):
    pattern = re.compile(r"\.(jpe?g|png)$", re.I)

    def __init__(self):
        super().__init__()
        self.srcs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "img":
            return
        attrs = dict(attrs)
        src = attrs.get("src")
        if src and self.pattern.search(src):
            self.srcs.append(src.lstrip("./"))


async def _get_img_names(session: aiohttp.ClientSession, code: str) -> list[str]:
    page_url = BASE_PAGE.format(code=code)
    async with session.get(page_url) as r:
        if r.status != 200:
            return []
        html = await r.text()
    parser = _ImgSrcParser()
    parser.feed(html)
    return parser.srcs


# ──────────────────── 画像取得 ────────────────
async def _fetch_one(session, url):
    async with session.get(url) as r:
        return await r.read() if r.status == 200 else None


async def fetch_all(code: str) -> list[bytes]:
    if code in _img_cache:
        print(f"cache exists: {code}", flush=True)
        return _img_cache[code]
    else:
        print(f"cache not exists: {code}", flush=True)

    async with aiohttp.ClientSession() as s:
        names = await _get_img_names(s, code)
        page_url = BASE_PAGE.format(code=code)
        tasks = [_fetch_one(s, urljoin(page_url, n)) for n in names]
        imgs = await asyncio.gather(*tasks)
        imgs = [b for b in imgs if b]

    _img_cache[code] = imgs
    if len(_img_cache) > MAX_ITEMS:
        _img_cache.popitem(last=False)
    print(f"保存されているキャッシュの数: {len(_img_cache)}", flush=True)
    return imgs


# ──────────────────── その他ユーティリティ ───
def timestamp() -> str:
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
