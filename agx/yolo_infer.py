import io
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError

import config


def load_model(path: str) -> Any:
    mode = _infer_mode()
    if mode == "mock":
        return {"mode": "mock"}
    if mode != "yolo":
        raise ValueError(f"unsupported YOLO_INFER_MODE: {mode}")

    model_path = _model_path(path)

    from ultralytics import YOLO

    return YOLO(str(model_path))


def infer(model: Any, image_bytes: bytes) -> dict:
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except (OSError, UnidentifiedImageError) as exc:
        raise ValueError("invalid image") from exc

    image_size = _image_size(image)

    if _infer_mode() == "mock":
        return _mock_infer(image)

    results = model.predict(
        image,
        conf=config.YOLO_CONF,
        device=config.YOLO_DEVICE,
        verbose=False,
    )

    if not results:
        return {"label": None, "confidence": None, "image_size": image_size}

    boxes = results[0].boxes
    if boxes is None or boxes.conf is None or len(boxes.conf) == 0:
        return {"label": None, "confidence": None, "image_size": image_size}

    best_index = int(boxes.conf.argmax().item())
    class_id = int(boxes.cls[best_index].item())
    confidence = float(boxes.conf[best_index].item())
    class_name = _class_name(model.names, class_id)
    bbox = _bbox(boxes.xyxy[best_index].tolist(), image_size)
    center = _center(bbox)

    return {
        "label": class_name,
        "confidence": confidence,
        "image_size": image_size,
        "bbox": bbox,
        "center": center,
    }


def _class_name(names: Any, class_id: int) -> str:
    try:
        name = names[class_id]
    except (KeyError, IndexError, TypeError):
        try:
            name = names[str(class_id)]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"unknown YOLO class id: {class_id}") from exc

    if not isinstance(name, str) or not name:
        raise RuntimeError(f"invalid YOLO class name for id: {class_id}")

    return name


def _mock_infer(image: Image.Image) -> dict:
    mock = _mock_detection()
    label = mock.get("label")
    if label is None:
        return {"label": None, "confidence": None, "image_size": _image_size(image)}

    width, height = image.size
    bbox_ratio = mock["bbox_ratio"]
    bbox = _bbox(
        [
            width * _ratio(bbox_ratio.get("x1"), "MOCK_DETECTION.bbox_ratio.x1"),
            height * _ratio(bbox_ratio.get("y1"), "MOCK_DETECTION.bbox_ratio.y1"),
            width * _ratio(bbox_ratio.get("x2"), "MOCK_DETECTION.bbox_ratio.x2"),
            height * _ratio(bbox_ratio.get("y2"), "MOCK_DETECTION.bbox_ratio.y2"),
        ],
        _image_size(image),
    )

    return {
        "label": label,
        "confidence": _confidence(mock.get("confidence"), "MOCK_DETECTION.confidence"),
        "image_size": _image_size(image),
        "bbox": bbox,
        "center": _center(bbox),
    }


def _infer_mode() -> str:
    return config.YOLO_INFER_MODE


def _image_size(image: Image.Image) -> dict:
    width, height = image.size
    return {"width": width, "height": height}


def _model_path(path: str) -> Path:
    if not isinstance(path, str) or not path:
        raise ValueError("YOLO_MODEL_PATH is required")

    model_path = Path(path).expanduser()
    if not model_path.is_absolute():
        model_path = Path(config.__file__).resolve().parent / model_path

    model_path = model_path.resolve()
    if not model_path.is_file():
        raise ValueError(f"YOLO model file not found: {model_path}")

    return model_path


def _mock_detection() -> dict:
    mock = getattr(config, "MOCK_DETECTION", None)
    if not isinstance(mock, dict):
        raise ValueError("MOCK_DETECTION must be an object")

    bbox_ratio = mock.get("bbox_ratio")
    if mock.get("label") is not None and not isinstance(bbox_ratio, dict):
        raise ValueError("MOCK_DETECTION.bbox_ratio must be an object")

    return mock


def _bbox(values: list[float], image_size: dict) -> dict:
    if len(values) != 4:
        raise RuntimeError("YOLO bbox must contain four values")

    width = _positive_number(image_size.get("width"), "image width")
    height = _positive_number(image_size.get("height"), "image height")
    x1, y1, x2, y2 = [float(value) for value in values]
    x1 = _clamp(x1, 0.0, width)
    y1 = _clamp(y1, 0.0, height)
    x2 = _clamp(x2, 0.0, width)
    y2 = _clamp(y2, 0.0, height)

    if x2 <= x1 or y2 <= y1:
        raise ValueError("invalid detection bbox")

    return {"x1": x1, "y1": y1, "x2": x2, "y2": y2}


def _center(bbox: dict) -> dict:
    return {
        "x": (bbox["x1"] + bbox["x2"]) / 2,
        "y": (bbox["y1"] + bbox["y2"]) / 2,
    }


def _ratio(value, name: str) -> float:
    number = _number(value, name)
    if number < 0 or number > 1:
        raise ValueError(f"{name} must be between 0 and 1")

    return number


def _confidence(value, name: str) -> float:
    number = _number(value, name)
    if number < 0 or number > 1:
        raise ValueError(f"{name} must be between 0 and 1")

    return number


def _positive_number(value, name: str) -> float:
    number = _number(value, name)
    if number <= 0:
        raise ValueError(f"{name} must be positive")

    return number


def _number(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")

    return float(value)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))
