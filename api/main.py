# main.py
import asyncio
import os
import time

import aiohttp
import magic
import pillow_heif
from PIL import UnidentifiedImageError
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from qr import extract_url
from tmp_store import peek_zip, save_temp_zip, sweep_expired
from utils import fetch_all, make_zip, timestamp
from logger import log

pillow_heif.register_heif_opener()

app = FastAPI(title="idolmaster-tours-livephoto-api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://the-idol-master-tours-livephoto.onrender.com",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Disposition"],
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
            sweep_expired()
            await asyncio.sleep(600)  # 10 分ごと

    asyncio.create_task(loop())


@app.post("/validate")
async def validate(files: list[UploadFile] = File(...)):
    log("[POST]: /validate")
    if len(files) > MAX_FILES:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "最大 10 枚までです"},
        )

    successes, errors, seen = [], [], {}
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
                            f"[{idx}枚目] （{f.filename}）はライブフォトの保存期間が終了しています。"
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
                    f"[{idx}枚目] （{f.filename}）のQRコードは他と重複しているためスキップしました。"
                )
                continue

            seen[code] = idx
            successes.append(url)
    log(f"Success: {len(successes)} Error: {len(errors)}")
    if not successes:
        return JSONResponse(status_code=200, content={"ok": False, "errors": errors})

    imgs = await asyncio.gather(*(fetch_all(u.split("/")[-2]) for u in successes))
    ts = timestamp()
    zip_bytes = make_zip(imgs, ts)
    ticket = save_temp_zip(zip_bytes, ts)

    return JSONResponse(
        status_code=200,
        content={
            "ok": True,
            "ticket": ticket,
            "count": len(imgs),
            "errors": errors,
        },
    )


@app.get("/download/{ticket}")
async def download_stream(ticket: str):
    log(f"[GET]: /download/{ticket}")
    rec = peek_zip(ticket)
    if not rec:
        return JSONResponse(
            status_code=404,
            content={
                "ok": False,
                "error": "無効または期限切れのチケットです。再度検証したあとに、ダウンロードしてください。",
            },
        )
    path, exp, ts = rec

    return FileResponse(
        path,
        media_type="application/zip",
        filename=f"idolmaster_tours_livephoto_{ts}.zip",
    )
