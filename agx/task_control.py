import config


def empty_result() -> dict:
    return {
        "bin": None,
        "label": None,
        "message": "未偵測到垃圾",
        "confidence": None,
        "detection": None,
        "workspace": None,
        "command": None,
    }


def build_result(detection: dict) -> dict:
    label = detection["label"]
    if label not in config.CLASS_NAMES:
        raise ValueError(f"無法辨識類別: {label}")

    bin_value = config.BIN_MAP[label]
    workspace = image_to_workspace(detection["center"])

    return {
        "label": label,
        "bin": bin_value,
        "message": config.MESSAGE_MAP[label],
        "confidence": detection["confidence"],
        "detection": {
            "bbox": detection["bbox"],
            "center": detection["center"],
        },
        "workspace": workspace,
        "command": build_command(bin_value, workspace),
    }


def image_to_workspace(center: dict) -> dict:
    transform = config.IMAGE_TO_WORKSPACE
    return {
        "x": center["x"] * transform["scale_x"] + transform["offset_x"],
        "y": center["y"] * transform["scale_y"] + transform["offset_y"],
        "z": config.WORKSPACE_Z,
    }


def build_command(bin_value: str, workspace: dict) -> dict:
    return {
        "action": "pick_and_place",
        "target_bin": bin_value,
        "pick": workspace,
    }
