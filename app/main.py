import base64
import os
import tempfile
import time
import uuid
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

from . import inference, report

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "outputs"
OUT.mkdir(exist_ok=True)
MAX_FRAMES = int(os.getenv("MAX_FRAMES", "600"))
DEFAULT_CONF = float(os.getenv("DEFAULT_CONF", "0.25"))
RESULTS = {}  # in-memory report store (use a database in production)

app = FastAPI(title="Asphalt Pathology Detection API", version="1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory=BASE / "static"), name="static")


def b64(img, quality=85):
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, quality])
    return base64.b64encode(buf.tobytes()).decode()


@app.get("/", response_class=HTMLResponse)
def home():
    return (BASE / "static" / "index.html").read_text(encoding="utf-8")


@app.get("/health")
def health():
    try:
        return {"status": "ok", "classes": inference.class_names()}
    except FileNotFoundError as e:
        return {"status": "model_missing", "detail": str(e)}


@app.post("/predict/image")
def predict_image(
    file: UploadFile = File(...),
    conf: float = Form(DEFAULT_CONF),
    lat: float | None = Form(None),
    lon: float | None = Form(None),
):
    img = cv2.imdecode(np.frombuffer(file.file.read(), np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(400, "Could not read the image file.")
    t0 = time.time()
    try:
        dets, ann = inference.detect(img, conf)
    except FileNotFoundError as e:
        raise HTTPException(500, str(e))
    dets = report.add_severity(dets)
    summary = report.summarise(dets, 1)
    rid = uuid.uuid4().hex[:8]
    meta = {"source": file.filename, "lat": lat, "lon": lon}
    img_b64 = b64(ann)
    RESULTS[rid] = {"html": report.build_html(rid, summary, meta, [img_b64], dets)}
    return {"report_id": rid, "report_url": f"/report/{rid}", "summary": summary,
            "detections": dets, "images": [img_b64],
            "seconds": round(time.time() - t0, 2)}


@app.post("/predict/video")
def predict_video(
    file: UploadFile = File(...),
    conf: float = Form(DEFAULT_CONF),
    frame_stride: int = Form(5),
    lat: float | None = Form(None),
    lon: float | None = Form(None),
):
    t0 = time.time()
    rid = uuid.uuid4().hex[:8]
    suffix = Path(file.filename or "v.mp4").suffix or ".mp4"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file.file.read())
    cap = cv2.VideoCapture(tmp.name)
    if not cap.isOpened():
        os.unlink(tmp.name)
        raise HTTPException(400, "Could not read the video file.")
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    stride = max(1, frame_stride)
    out_path = OUT / f"{rid}.mp4"
    writer, all_dets, worst, idx, done = None, [], [], 0, 0
    try:
        while done < MAX_FRAMES:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % stride == 0:
                dets, ann = inference.detect(frame, conf)
                dets = report.add_severity(dets)
                for d in dets:
                    d["frame"], d["time_s"] = idx, round(idx / fps, 2)
                all_dets += dets
                if writer is None:
                    h, w = ann.shape[:2]
                    writer = cv2.VideoWriter(str(out_path), cv2.VideoWriter_fourcc(*"mp4v"),
                                             max(fps / stride, 1), (w, h))
                writer.write(ann)
                if dets:
                    worst.append((report.frame_score(dets), ann))
                    worst.sort(key=lambda x: -x[0])
                    worst = worst[:3]
                done += 1
            idx += 1
    except FileNotFoundError as e:
        raise HTTPException(500, str(e))
    finally:
        cap.release()
        if writer:
            writer.release()
        os.unlink(tmp.name)
    summary = report.summarise(all_dets, done)
    imgs = [b64(a) for _, a in worst]
    meta = {"source": file.filename, "lat": lat, "lon": lon}
    RESULTS[rid] = {"html": report.build_html(rid, summary, meta, imgs, all_dets), "video": out_path}
    return {"report_id": rid, "report_url": f"/report/{rid}", "video_url": f"/video/{rid}",
            "summary": summary, "detections": all_dets[:200], "images": imgs,
            "seconds": round(time.time() - t0, 2)}


@app.get("/report/{rid}", response_class=HTMLResponse)
def get_report(rid: str):
    if rid not in RESULTS:
        raise HTTPException(404, "Report not found (reports are kept in memory until restart).")
    return RESULTS[rid]["html"]


@app.get("/video/{rid}")
def get_video(rid: str):
    p = RESULTS.get(rid, {}).get("video")
    if not p or not Path(p).exists():
        raise HTTPException(404, "Video not found.")
    return FileResponse(p, media_type="video/mp4", filename=f"annotated_{rid}.mp4")
