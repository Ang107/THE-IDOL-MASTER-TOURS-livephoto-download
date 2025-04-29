import os, secrets, tempfile, time

_TTL = 15 * 60
_store: dict[str, tuple[str, float]] = {}  # ticket -> (path, exp)


def save_temp_zip(data: bytes) -> str:
    ticket = secrets.token_urlsafe(16)
    fd, path = tempfile.mkstemp(suffix=".zip")
    os.write(fd, data)
    os.close(fd)
    _store[ticket] = (path, time.time() + _TTL)
    return ticket


def pop_zip(ticket: str):
    return _store.pop(ticket, None)  # (path, exp) or None


def sweep_expired():
    now = time.time()
    expired = [t for t, (p, exp) in _store.items() if now > exp]
    for ticket in expired:
        path, _ = _store.pop(ticket)
        if os.path.exists(path):
            os.remove(path)
