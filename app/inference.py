import os
from ultralytics import YOLO

MODEL_PATH = os.getenv("MODEL_PATH", "models/best.pt")
IMGSZ = int(os.getenv("IMGSZ", "640"))
_model = None


def get_model():
    global _model
    if _model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at '{MODEL_PATH}'. Copy your .pt file there or set MODEL_PATH."
            )
        _model = YOLO(MODEL_PATH)
    return _model


def class_names():
    return list(get_model().names.values())


def detect(frame, conf=0.25):
    """Run YOLO on a BGR frame. Returns (detections, annotated BGR frame)."""
    model = get_model()
    res = model.predict(frame, conf=conf, imgsz=IMGSZ, verbose=False)[0]
    h, w = frame.shape[:2]
    dets = []
    for b in res.boxes:
        x1, y1, x2, y2 = b.xyxy[0].tolist()
        dets.append({
            "class": model.names[int(b.cls)],
            "confidence": round(float(b.conf), 3),
            "box": [round(v, 1) for v in (x1, y1, x2, y2)],
            "area_ratio": round(((x2 - x1) * (y2 - y1)) / (w * h), 4),
        })
    return dets, res.plot()
