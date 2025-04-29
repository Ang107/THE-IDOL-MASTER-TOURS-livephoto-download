from pyzbar.pyzbar import decode
from PIL import Image, ImageOps
import io, re

PATTERN = re.compile(
    r"^https://livephoto\.idolmaster-tours-w\.bn-am\.net/livephoto/([A-Za-z0-9_-]+)/$"
)

MAX_EDGE = 1600  # 長辺 1600px に縮小してから解析


def _prepare(img: Image.Image) -> Image.Image:
    img = ImageOps.exif_transpose(img)  # 向き補正
    if max(img.size) > MAX_EDGE:  # 縮小
        r = MAX_EDGE / max(img.size)
        img = img.resize((int(img.width * r), int(img.height * r)), Image.BILINEAR)
    img = img.convert("L")  # グレースケール
    return img


def extract_url(raw: bytes) -> str | None:
    img = Image.open(io.BytesIO(raw))
    img = _prepare(img)

    # 0〜270°を90°刻みで探索
    for k in range(4):
        syms = decode(img.rotate(90 * k, expand=True))
        for sym in syms:
            url = sym.data.decode("utf-8", "ignore").strip()
            m = PATTERN.match(url)
            if m:
                code = m.group(1)
                return (
                    f"https://livephoto.idolmaster-tours-w.bn-am.net/livephoto/{code}/"
                )
    return None
