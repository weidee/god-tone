import config


def empty_result(image_size: dict | None = None) -> dict:
    return {
        "schema_version": config.SCHEMA_VERSION,
        "bin": None,
        "label": None,
        "message": "未偵測到垃圾",
        "confidence": None,
        "image_size": image_size,
        "detection": None,
        "pick_zone": None,
        "workspace_candidate": None,
        "workspace": None,
        "command": None,
    }


def build_result(detection: dict) -> dict:
    normalized = normalize_detection(detection)
    label = normalized["label"]
    if label not in config.CLASS_NAMES:
        raise ValueError(f"無法辨識類別: {label}")

    bin_value = _map_value(config.BIN_MAP, label, "BIN_MAP")
    pick_target = build_pick_target(normalized)

    return {
        "schema_version": config.SCHEMA_VERSION,
        "label": label,
        "bin": bin_value,
        "message": _map_value(config.MESSAGE_MAP, label, "MESSAGE_MAP"),
        "confidence": normalized["confidence"],
        "image_size": normalized["image_size"],
        "detection": {
            "bbox": normalized["bbox"],
            "center": normalized["center"],
        },
        "pick_zone": pick_target["pick_zone"],
        "workspace_candidate": pick_target["workspace_candidate"],
        "workspace": pick_target["workspace"],
        "command": build_command(bin_value, pick_target),
    }


def normalize_detection(detection: dict) -> dict:
    if not isinstance(detection, dict):
        raise ValueError("detection must be an object")

    image_size = _image_size(detection.get("image_size"))
    bbox = _bbox(detection.get("bbox"), image_size)
    center = _center(detection.get("center"), bbox, image_size)

    return {
        "label": _label(detection.get("label")),
        "confidence": _confidence(detection.get("confidence")),
        "image_size": image_size,
        "bbox": bbox,
        "center": center,
    }


def build_pick_target(detection: dict) -> dict:
    mode = config.COORDINATE_MODE
    if mode == "zone":
        return {
            "pick_zone": center_to_pick_zone(
                detection["center"]["x"],
                detection["image_size"]["width"],
            ),
            "workspace_candidate": None,
            "workspace": None,
        }

    if mode == "workspace":
        workspace = image_to_workspace(detection["center"])
        return {
            "pick_zone": None,
            "workspace_candidate": workspace,
            "workspace": workspace,
        }

    raise ValueError(f"unsupported COORDINATE_MODE: {mode}")


def center_to_pick_zone(center_x: int | float, image_width: int | float) -> str:
    center_x = _number(center_x, "center.x")
    image_width = _positive_number(image_width, "image width")

    left_split, middle_split = _zone_splits()
    if center_x < image_width * left_split:
        return "left"
    if center_x < image_width * middle_split:
        return "middle"
    return "right"


def _zone_splits() -> tuple[float, float]:
    splits = config.ZONE_SPLITS
    if not isinstance(splits, (list, tuple)) or len(splits) != 2:
        raise ValueError("ZONE_SPLITS must contain two ratios")

    left_split = _number(splits[0], "ZONE_SPLITS[0]")
    middle_split = _number(splits[1], "ZONE_SPLITS[1]")
    if not 0 < left_split < middle_split < 1:
        raise ValueError("ZONE_SPLITS must satisfy 0 < left < middle < 1")

    return left_split, middle_split


def image_to_workspace(center: dict) -> dict:
    transform = config.IMAGE_TO_WORKSPACE
    if not isinstance(transform, dict):
        raise ValueError("IMAGE_TO_WORKSPACE must be an object")

    center = _center(center, None, None)
    return {
        "x": center["x"] * _number(transform.get("scale_x"), "IMAGE_TO_WORKSPACE.scale_x")
        + _number(transform.get("offset_x"), "IMAGE_TO_WORKSPACE.offset_x"),
        "y": center["y"] * _number(transform.get("scale_y"), "IMAGE_TO_WORKSPACE.scale_y")
        + _number(transform.get("offset_y"), "IMAGE_TO_WORKSPACE.offset_y"),
        "z": _number(config.WORKSPACE_Z, "WORKSPACE_Z"),
    }


def build_command(bin_value: str, pick_target: dict) -> dict:
    command = {
        "action": config.COMMAND_ACTION,
        "target_bin": bin_value,
    }

    if pick_target["pick_zone"] is not None:
        command["pick_zone"] = pick_target["pick_zone"]
    else:
        command["workspace_candidate"] = pick_target["workspace_candidate"]

    return command


def _label(value) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("detection.label is required")

    return value


def _confidence(value) -> float:
    number = _number(value, "detection.confidence")
    if number < 0 or number > 1:
        raise ValueError("detection.confidence must be between 0 and 1")

    return number


def _image_size(value) -> dict:
    if not isinstance(value, dict):
        raise ValueError("detection.image_size must be an object")

    width = _positive_number(value.get("width"), "detection.image_size.width")
    height = _positive_number(value.get("height"), "detection.image_size.height")
    return {
        "width": int(width) if width.is_integer() else width,
        "height": int(height) if height.is_integer() else height,
    }


def _bbox(value, image_size: dict) -> dict:
    if not isinstance(value, dict):
        raise ValueError("detection.bbox must be an object")

    x1 = _number(value.get("x1"), "detection.bbox.x1")
    y1 = _number(value.get("y1"), "detection.bbox.y1")
    x2 = _number(value.get("x2"), "detection.bbox.x2")
    y2 = _number(value.get("y2"), "detection.bbox.y2")

    if x2 <= x1 or y2 <= y1:
        raise ValueError("detection.bbox must satisfy x1 < x2 and y1 < y2")
    if x1 < 0 or y1 < 0 or x2 > image_size["width"] or y2 > image_size["height"]:
        raise ValueError("detection.bbox must stay inside image_size")

    return {"x1": x1, "y1": y1, "x2": x2, "y2": y2}


def _center(value, bbox: dict | None, image_size: dict | None) -> dict:
    if not isinstance(value, dict):
        if bbox is None:
            raise ValueError("center must be an object")
        value = {
            "x": (bbox["x1"] + bbox["x2"]) / 2,
            "y": (bbox["y1"] + bbox["y2"]) / 2,
        }

    x = _number(value.get("x"), "center.x")
    y = _number(value.get("y"), "center.y")
    if image_size is not None:
        if x < 0 or x > image_size["width"] or y < 0 or y > image_size["height"]:
            raise ValueError("detection.center must stay inside image_size")

    return {"x": x, "y": y}


def _map_value(mapping: dict, key: str, name: str) -> str:
    if not isinstance(mapping, dict):
        raise ValueError(f"{name} must be an object")

    value = mapping.get(key)
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name}.{key} is required")

    return value


def _positive_number(value, name: str) -> float:
    number = _number(value, name)
    if number <= 0:
        raise ValueError(f"{name} must be a positive number")

    return number


def _number(value, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")

    return float(value)
