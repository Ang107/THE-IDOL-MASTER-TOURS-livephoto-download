# main.py

import asyncio
import os
import time

import aiohttp
import magic
import pillow_heif
from PIL import UnidentifiedImageError
from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from qr import extract_url
from tmp_store import peek_zip, pop_zip, save_temp_zip, sweep_expired
from utils import cleanup_cache, fetch_all, make_zip, timestamp

pillow_heif.register_heif_opener()

app = FastAPI(title="idolmaster-tours-livephoto-api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILES = 10
MAX_SIZE = 25 * 1024 * 1024  # 25MB
ALLOWED_MIME = {
    "image/jpeg",
    "image/png",
    "image/heic",
    "image/heif",
    "image/heics",
}


@app.on_event("startup")
async def schedule_cleanup():
    async def loop():
        while True:
            # ZIP 一時ストアの期限切れクリーン
            sweep_expired()
            # 画像キャッシュの期限切れクリーン
            cleanup_cache()
            await asyncio.sleep(600)  # 10 分ごと

    asyncio.create_task(loop())


@app.post("/validate")
async def validate(files: list[UploadFile] = File(...)):
    if len(files) > MAX_FILES:
        raise HTTPException(400, "最大 10 枚までです")

    good, errors, seen = [], [], {}  # seen: code -> first_idx
    async with aiohttp.ClientSession() as session:
        for idx, f in enumerate(files, 1):
            data = await f.read()
            mime = magic.from_buffer(data, mime=True)

            if len(data) > MAX_SIZE:
                errors.append(
                    f"[{idx}枚目] （{f.filename}）がサイズ上限(25MB)を超えています。"
                )
                continue
            if mime not in ALLOWED_MIME:
                errors.append(
                    f"[{idx}枚目] （{f.filename}）が対応画像形式ではありません。"
                )
                continue
            try:
                url = extract_url(data)
            except UnidentifiedImageError:
                errors.append(
                    f"[{idx}枚目] （{f.filename}）を画像として読み込めません。"
                )
                continue
            if not url:
                errors.append(
                    f"[{idx}枚目] （{f.filename}）のQRコードを検出できません。"
                )
                continue
            try:
                async with session.get(url) as resp:
                    if resp.status == 404:
                        errors.append(
                            f"[{idx}枚目] （{f.filename}）のQR先リソースが見つかりませんでした（404）。"
                        )
                        continue
            except Exception as e:
                errors.append(
                    f"[{idx}枚目] （{f.filename}）のQR先へのアクセスでエラーが発生しました: {e}"
                )
                continue
            code = url.split("/")[-2]
            if code in seen:
                errors.append(
                    f"[{idx}枚目] （{f.filename}）のQRコードは他のQRコードと重複しているため、スキップされました。"
                )
                continue

            seen[code] = idx
            good.append(url)

    if not good:
        return {"ok": False, "errors": errors}  # 全滅

    imgs = await asyncio.gather(*(fetch_all(u.split("/")[-2]) for u in good))

    # バリデーション実行時にタイムスタンプを取得
    ts = timestamp()

    zip_bytes = make_zip(imgs, ts)
    ticket = save_temp_zip(zip_bytes, ts)
    return {
        "ok": True,
        "ticket": ticket,
        "count": len(imgs),
        "errors": errors,
    }


def file_iterator(path: str, chunk_size: int = 1024 * 1024):
    """1MBずつ読み込んで yield するジェネレータ"""
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield chunk


@app.get("/download/{ticket}")
async def download_stream(ticket: str):
    rec = peek_zip(ticket)  # (path, exp, ts) or None
    if not rec:
        raise HTTPException(404, "無効または期限切れのチケットです")
    path, exp, ts = rec

    if time.time() > exp:
        pop = pop_zip(ticket)
        if pop:
            path_to_remove, _, _ = pop
            if os.path.exists(path_to_remove):
                os.remove(path_to_remove)
        raise HTTPException(404, "無効または期限切れのチケットです")

    # ダウンロード後は削除せず、15分後の掃除に任せる
    headers = {
        "Content-Disposition": f'attachment; filename="idolmaster_tours_livephoto_{ts}.zip"'
    }
    return StreamingResponse(
        file_iterator(path),
        media_type="application/zip",
        headers=headers,
    )
