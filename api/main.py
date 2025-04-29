import asyncio
import os
import time
from fastapi import FastAPI, File, UploadFile, HTTPException, Response, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from qr import extract_url
from utils import fetch_all, make_zip, timestamp
from tmp_store import save_temp_zip, pop_zip, sweep_expired
import magic, time
from PIL import UnidentifiedImageError
import pillow_heif

pillow_heif.register_heif_opener()

app = FastAPI(title="idolmaster-tours-livephoto-api")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 後で Next.js の URL に絞る
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
            sweep_expired()  # 期限切れZIPを削除
            await asyncio.sleep(600)  # 10 分おき

    asyncio.create_task(loop())


@app.post("/validate")
async def validate(files: list[UploadFile] = File(...)):
    if len(files) > MAX_FILES:
        raise HTTPException(400, "最大 10 枚までです")

    good, errors, seen = [], [], {}  # seen: code -> first_idx
    for idx, f in enumerate(files, 1):
        data = await f.read()
        mime = magic.from_buffer(data, mime=True)

        if len(data) > MAX_SIZE:
            errors.append(
                f"[{idx}枚目] （{f.filename}）がサイズ上限(25MB)を超えています。"
            )
            continue
        if mime not in ALLOWED_MIME:
            errors.append(f"[{idx}枚目] （{f.filename}）が対応画像形式ではありません。")
            continue
        try:
            url = extract_url(data)
        except UnidentifiedImageError:
            errors.append(f"[{idx}枚目] （{f.filename}）を画像として読み込めません。")
            continue
        if not url:
            errors.append(f"[{idx}枚目] （{f.filename}）のQRコードを検出できません。")
            continue

        code = url.split("/")[-2]
        if code in seen:
            j = seen[code]
            errors.append(
                f"[{j}枚目] （{files[j-1].filename}）と "
                f"[{idx}枚目] （{f.filename}）のQRコードが重複しているため、片方のみダウンロードします。"
            )
            continue

        seen[code] = idx
        good.append(url)

    if not good:
        return {"ok": False, "errors": errors}  # 全滅

    imgs = await asyncio.gather(*(fetch_all(u.split("/")[-2]) for u in good))
    zip_bytes = make_zip(imgs)
    ticket = save_temp_zip(zip_bytes)
    return {
        "ok": True,
        "ticket": ticket,
        "count": len(imgs),
        "errors": errors,  # 部分失敗があればここに入る
    }


@app.get("/download/{ticket}")
def download(ticket: str, background_tasks: BackgroundTasks):
    rec = pop_zip(ticket)  # rec = (path, ts, exp)
    if not rec:
        raise HTTPException(404, "無効または期限切れのチケットです")

    path, exp = rec
    if time.time() > exp:
        if os.path.exists(path):
            os.remove(path)
        raise HTTPException(404, "無効または期限切れのチケットです")

    background_tasks.add_task(os.remove, path)

    return FileResponse(
        path,
        media_type="application/zip",
        filename=f"idolmaster_tours_livephoto_{timestamp()}.zip",
        background=background_tasks,
    )
