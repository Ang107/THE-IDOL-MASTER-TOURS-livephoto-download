# tmp_store.py
import os, secrets, tempfile, time
from logger import log

_TTL = 15 * 60
# ticket -> (path, exp, timestamp)
_store: dict[str, tuple[str, float, str]] = {}


def save_temp_zip(data: bytes, ts: str) -> str:
    ticket = secrets.token_urlsafe(16)
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.write(fd, data)
    os.close(fd)
    _store[ticket] = (path, time.time() + _TTL, ts)
    log(f"zipファイル作成 チケット: {ticket}")
    return ticket


def peek_zip(ticket: str):
    return _store.get(ticket)


def pop_zip(ticket: str):
    return _store.pop(ticket, None)


def sweep_expired():
    now = time.time()
    expired = [t for t, (_, exp, _) in _store.items() if now > exp]
    for ticket in expired:
        path, _, _ = _store.pop(ticket)
        if os.path.exists(path):
            log(f"zipファイル削除チケット: {ticket}")
            os.remove(path)
    log(f"保存されているzipファイルの数: {len(_store)}")
