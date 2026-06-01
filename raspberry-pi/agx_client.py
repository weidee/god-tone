import requests

import config


def detect(image_bytes: bytes) -> dict:
    if not image_bytes:
        raise ValueError("image_bytes is required")

    mode = getattr(config, "AGX_MODE", "http")
    if mode == "mock":
        return _mock_detect()
    if mode != "http":
        raise ValueError(f"unsupported AGX_MODE: {mode}")

    try:
        response = requests.post(
            config.AGX_URL.rstrip("/") + "/detect",
            files={"image": ("capture.jpg", image_bytes, "image/jpeg")},
            timeout=config.REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise RuntimeError(f"AI Server request failed: {exc}") from exc

    if response.status_code == 422:
        raise ValueError(_error_message(response))

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        raise RuntimeError(f"AI Server returned HTTP {response.status_code}") from exc

    try:
        return response.json()
    except ValueError as exc:
        raise RuntimeError("AI Server returned invalid JSON") from exc


def _error_message(response: requests.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        return "AI Server rejected request"

    return body.get("error", "AI Server rejected request")


def _mock_detect() -> dict:
    return {
        "schema_version": "1.0",
        "label": "plastic",
        "bin": "bin_b",
        "message": "已產生塑膠分類控制指令",
        "confidence": 0.91,
        "image_size": {
            "width": 640,
            "height": 480,
        },
        "detection": {
            "bbox": {
                "x1": 120,
                "y1": 80,
                "x2": 260,
                "y2": 220,
            },
            "center": {
                "x": 190,
                "y": 150,
            },
        },
        "pick_zone": "left",
        "workspace_candidate": None,
        "workspace": None,
        "command": {
            "action": "pick_and_place",
            "target_bin": "bin_b",
            "pick_zone": "left",
        },
    }
