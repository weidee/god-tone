import config


def empty_result() -> dict:
    return {
        "schema_version": config.SCHEMA_VERSION,
        "bin": None,
        "label": None,
        "message": "未偵測到垃圾",
        "confidence": None,
        "image_size": None,
        "detection": None,
        "pick_zone": None,
        "workspace_candidate": None,
        "workspace": None,
        "command": None,
    }


def build_result(detection: dict) -> dict:
    label = detection["label"]
    if label not in config.CLASS_NAMES:
        raise ValueError(f"無法辨識類別: {label}")

    bin_value = config.BIN_MAP[label]
    pick_target = build_pick_target(detection)

    return {
        "schema_version": config.SCHEMA_VERSION,
        "label": label,
        "bin": bin_value,
        "message": config.MESSAGE_MAP[label],
        "confidence": detection["confidence"],
        "image_size": detection["image_size"],
        "detection": {
            "bbox": detection["bbox"],
            "center": detection["center"],
        },
        "pick_zone": pick_target["pick_zone"],
        "workspace_candidate": pick_target["workspace_candidate"],
        "workspace": pick_target["workspace_candidate"],
        "command": build_command(bin_value, pick_target),
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
        }

    if mode == "workspace":
        return {
            "pick_zone": None,
            "workspace_candidate": image_to_workspace(detection["center"]),
        }

    raise ValueError(f"unsupported COORDINATE_MODE: {mode}")


def center_to_pick_zone(center_x: int | float, image_width: int | float) -> str:
    if not isinstance(center_x, (int, float)):
        raise ValueError("center.x must be a number")
    if not isinstance(image_width, (int, float)) or image_width <= 0:
        raise ValueError("image width must be a positive number")

    left_split, middle_split = _zone_splits()
    if center_x < image_width * left_split:
        return "left"
    if center_x < image_width * middle_split:
        return "middle"
    return "right"


def _zone_splits() -> tuple[float, float]:
    splits = config.ZONE_SPLITS
    if not isinstance(splits, list) or len(splits) != 2:
        raise ValueError("ZONE_SPLITS must contain two ratios")

    left_split, middle_split = splits
    if not 0 < left_split < middle_split < 1:
        raise ValueError("ZONE_SPLITS must satisfy 0 < left < middle < 1")

    return left_split, middle_split


def image_to_workspace(center: dict) -> dict:
    transform = config.IMAGE_TO_WORKSPACE
    return {
        "x": center["x"] * transform["scale_x"] + transform["offset_x"],
        "y": center["y"] * transform["scale_y"] + transform["offset_y"],
        "z": config.WORKSPACE_Z,
    }


def build_command(bin_value: str, pick_target: dict) -> dict:
    command = {
        "action": "pick_and_place",
        "target_bin": bin_value,
    }

    if pick_target["pick_zone"] is not None:
        command["pick_zone"] = pick_target["pick_zone"]
    else:
        command["workspace_candidate"] = pick_target["workspace_candidate"]

    return command
