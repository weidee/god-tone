import io
from typing import Any

from PIL import Image, UnidentifiedImageError

import config


def load_model(path: str) -> Any:
    mode = _infer_mode()
    if mode == "mock":
        return {"mode": "mock"}
    if mode != "yolo":
        raise ValueError(f"unsupported YOLO_INFER_MODE: {mode}")

    from ultralytics import YOLO

    return YOLO(path)


def infer(model: Any, image_bytes: bytes) -> dict:
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except UnidentifiedImageError as exc:
        raise ValueError("invalid image") from exc

    if _infer_mode() == "mock":
        return _mock_infer(image)

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
    x1, y1, x2, y2 = [float(value) for value in boxes.xyxy[best_index].tolist()]
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2

    return {
        "label": class_name,
        "confidence": confidence,
        "bbox": {
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
        },
        "center": {
            "x": center_x,
            "y": center_y,
        },
    }


def _class_name(names: Any, class_id: int) -> str:
    try:
        return names[class_id]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"unknown YOLO class id: {class_id}") from exc


def _mock_infer(image: Image.Image) -> dict:
    mock = config.MOCK_DETECTION
    label = mock["label"]
    if label is None:
        return {"label": None, "confidence": None}

    width, height = image.size
    bbox_ratio = mock["bbox_ratio"]
    x1 = width * bbox_ratio["x1"]
    y1 = height * bbox_ratio["y1"]
    x2 = width * bbox_ratio["x2"]
    y2 = height * bbox_ratio["y2"]
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2

    return {
        "label": label,
        "confidence": mock["confidence"],
        "bbox": {
            "x1": x1,
            "y1": y1,
            "x2": x2,
            "y2": y2,
        },
        "center": {
            "x": center_x,
            "y": center_y,
        },
    }


def _infer_mode() -> str:
    return getattr(config, "YOLO_INFER_MODE", "yolo")
