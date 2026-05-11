import io
from typing import Any

from PIL import Image

import config


def load_model(path: str) -> Any:
    from ultralytics import YOLO

    return YOLO(path)


def infer(model: Any, image_bytes: bytes) -> dict:
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    results = model.predict(
        image,
        conf=config.YOLO_CONF,
        device=config.YOLO_DEVICE,
        verbose=False,
    )

    if not results:
        return {"label": None, "confidence": None}

    boxes = results[0].boxes
    if boxes is None or boxes.conf is None or len(boxes.conf) == 0:
        return {"label": None, "confidence": None}

    best_index = int(boxes.conf.argmax().item())
    class_id = int(boxes.cls[best_index].item())
    confidence = float(boxes.conf[best_index].item())
    class_name = _class_name(model.names, class_id)

    return {"label": class_name, "confidence": confidence}


def _class_name(names: Any, class_id: int) -> str:
    try:
        return names[class_id]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"unknown YOLO class id: {class_id}") from exc
