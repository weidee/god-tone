from copy import deepcopy

import requests

import config


def detect(image_bytes: bytes) -> dict:
    if not image_bytes:
        raise ValueError("image_bytes is required")

    mode = getattr(config, "AGX_MODE", "http")
    if mode == "mock":
        return validate_result(_mock_detect())
    if mode != "http":
        raise ValueError(f"unsupported AGX_MODE: {mode}")

    try:
        response = requests.post(
            _agx_url() + "/detect",
            files={"image": (_capture_filename(), image_bytes, _capture_mime_type())},
            timeout=_request_timeout(),
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
        payload = response.json()
    except ValueError as exc:
        raise RuntimeError("AI Server returned invalid JSON") from exc

    return validate_result(payload)


def validate_result(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("AGX response must be an object")

    schema_version = payload.get("schema_version")
    expected_schema = getattr(config, "EXPECTED_AGX_SCHEMA_VERSION", "1.0")
    if schema_version != expected_schema:
        raise ValueError(f"unsupported AGX schema_version: {schema_version}")

    command = payload.get("command")
    if command is None:
        return payload

    _validate_detection_payload(payload)
    _validate_command(command, payload)
    return payload


def _error_message(response: requests.Response) -> str:
    try:
        body = response.json()
    except ValueError:
        text = response.text.strip()
        return text or "AI Server rejected request"

    if isinstance(body, dict):
        return body.get("error", "AI Server rejected request")

    return "AI Server rejected request"


def _mock_detect() -> dict:
    return deepcopy(getattr(config, "MOCK_AGX_RESULT", _DEFAULT_MOCK_AGX_RESULT))


def _validate_detection_payload(payload: dict) -> None:
    label = payload.get("label")
    if not isinstance(label, str) or not label:
        raise ValueError("AGX response label is required when command is present")

    allowed_labels = getattr(config, "CLASS_NAMES", ["metal", "plastic", "paper"])
    if label not in allowed_labels:
        raise ValueError(f"unsupported AGX label: {label}")

    bin_value = payload.get("bin")
    if bin_value not in config.BIN_POINTS:
        raise ValueError(f"unsupported AGX bin: {bin_value}")
    expected_bin = _bin_map().get(label)
    if expected_bin != bin_value:
        raise ValueError(f"AGX label/bin mismatch: {label} -> {bin_value}")

    confidence = _number(payload.get("confidence"), "AGX response confidence")
    if confidence < 0 or confidence > 1:
        raise ValueError("AGX response confidence must be between 0 and 1")

    image_size = payload.get("image_size")
    if not isinstance(image_size, dict):
        raise ValueError("AGX response image_size must be an object")
    _positive_number(image_size.get("width"), "AGX response image_size.width")
    _positive_number(image_size.get("height"), "AGX response image_size.height")

    detection = payload.get("detection")
    if not isinstance(detection, dict):
        raise ValueError("AGX response detection must be an object")

    bbox = detection.get("bbox")
    if not isinstance(bbox, dict):
        raise ValueError("AGX response detection.bbox must be an object")
    x1 = _number(bbox.get("x1"), "AGX response detection.bbox.x1")
    y1 = _number(bbox.get("y1"), "AGX response detection.bbox.y1")
    x2 = _number(bbox.get("x2"), "AGX response detection.bbox.x2")
    y2 = _number(bbox.get("y2"), "AGX response detection.bbox.y2")
    if x2 <= x1 or y2 <= y1:
        raise ValueError("AGX response detection.bbox must satisfy x1 < x2 and y1 < y2")

    center = detection.get("center")
    if not isinstance(center, dict):
        raise ValueError("AGX response detection.center must be an object")
    _number(center.get("x"), "AGX response detection.center.x")
    _number(center.get("y"), "AGX response detection.center.y")


def _validate_command(command: dict, payload: dict) -> None:
    if not isinstance(command, dict):
        raise ValueError("AGX command must be an object")

    action = command.get("action")
    if action != config.COMMAND_ACTION:
        raise ValueError(f"unsupported AGX command action: {action}")

    target_bin = command.get("target_bin")
    if target_bin not in config.BIN_POINTS:
        raise ValueError(f"unsupported AGX command target_bin: {target_bin}")
    if payload.get("bin") != target_bin:
        raise ValueError("AGX response bin must match command.target_bin")

    pick_zone = command.get("pick_zone")
    workspace_candidate = command.get("workspace_candidate")
    if pick_zone is None and workspace_candidate is None:
        raise ValueError("AGX command must include pick_zone or workspace_candidate")
    if pick_zone is not None and workspace_candidate is not None:
        raise ValueError("AGX command must not include both pick_zone and workspace_candidate")

    if pick_zone is not None and pick_zone not in config.PICK_POINTS:
        raise ValueError(f"unsupported AGX command pick_zone: {pick_zone}")
    if pick_zone is not None and payload.get("pick_zone") != pick_zone:
        raise ValueError("AGX response pick_zone must match command.pick_zone")
    if workspace_candidate is not None:
        _position(workspace_candidate, "AGX command workspace_candidate")
        _position(payload.get("workspace_candidate"), "AGX response workspace_candidate")


def _agx_url() -> str:
    url = getattr(config, "AGX_URL", "")
    if not isinstance(url, str) or not url:
        raise ValueError("AGX_URL is required")

    return url.rstrip("/")


def _capture_filename() -> str:
    filename = getattr(config, "CAPTURE_FILENAME", "capture.jpg")
    if not isinstance(filename, str) or not filename:
        raise ValueError("CAPTURE_FILENAME must be a non-empty string")

    return filename


def _capture_mime_type() -> str:
    mime_type = getattr(config, "CAPTURE_MIME_TYPE", "image/jpeg")
    if not isinstance(mime_type, str) or not mime_type:
        raise ValueError("CAPTURE_MIME_TYPE must be a non-empty string")

    return mime_type


def _bin_map() -> dict:
    mapping = getattr(
        config,
        "BIN_MAP",
        {
            "metal": "bin_a",
            "plastic": "bin_b",
            "paper": "bin_c",
        },
    )
    if not isinstance(mapping, dict):
        raise ValueError("BIN_MAP must be an object")

    return mapping


def _request_timeout() -> float:
    return _positive_number(getattr(config, "REQUEST_TIMEOUT", 10), "REQUEST_TIMEOUT")


def _position(position: dict, name: str) -> dict:
    if not isinstance(position, dict):
        raise ValueError(f"{name} must be an object")

    return {
        "x": _number(position.get("x"), f"{name}.x"),
        "y": _number(position.get("y"), f"{name}.y"),
        "z": _number(position.get("z"), f"{name}.z"),
    }


def _positive_number(value, name: str) -> float:
    number = _number(value, name)
    if number <= 0:
        raise ValueError(f"{name} must be positive")

    return number


def _number(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")

    return float(value)


_DEFAULT_MOCK_AGX_RESULT = {
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
