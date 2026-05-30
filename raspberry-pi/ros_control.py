import json

import config


def execute_command(command: dict | None) -> dict:
    if command is None:
        return {"executed": False, "reason": "no command", "motion_plan": []}

    validate_command(command)
    motion_plan = build_motion_plan(command)

    if config.ROS_MODE == "mock":
        print("Mock ROS command:")
        print(json.dumps(command, ensure_ascii=False, indent=2))
        print("Mock motion plan:")
        print(json.dumps(motion_plan, ensure_ascii=False, indent=2))
        return {"executed": True, "mode": "mock", "motion_plan": motion_plan}

    raise NotImplementedError("real ROS control is not implemented yet")


def validate_command(command: dict) -> None:
    if not isinstance(command, dict):
        raise ValueError("command must be an object")

    action = command.get("action")
    if action != config.COMMAND_ACTION:
        raise ValueError(f"unsupported command action: {action}")

    target_bin = command.get("target_bin")
    if target_bin not in config.TARGET_BINS:
        raise ValueError(f"unsupported target_bin: {target_bin}")

    pick = command.get("pick")
    if not isinstance(pick, dict):
        raise ValueError("command.pick is required")

    for axis in ("x", "y", "z"):
        value = pick.get(axis)
        if value is None:
            raise ValueError(f"command.pick.{axis} is required")
        if not isinstance(value, (int, float)):
            raise ValueError(f"command.pick.{axis} must be a number")


def build_motion_plan(command: dict) -> list[dict]:
    pick = command["pick"]
    target_bin = command["target_bin"]
    bin_position = _bin_position(target_bin)
    home = _position(config.HOME_POSITION, "HOME_POSITION")
    safe_z = _number(config.SAFE_Z, "SAFE_Z")

    return [
        {
            "step": "move_above_pick",
            "x": pick["x"],
            "y": pick["y"],
            "z": safe_z,
        },
        {
            "step": "move_to_pick",
            "x": pick["x"],
            "y": pick["y"],
            "z": pick["z"],
        },
        {"step": "close_gripper"},
        {
            "step": "lift",
            "x": pick["x"],
            "y": pick["y"],
            "z": safe_z,
        },
        {
            "step": "move_above_bin",
            "target_bin": target_bin,
            "x": bin_position["x"],
            "y": bin_position["y"],
            "z": safe_z,
        },
        {
            "step": "move_to_bin",
            "target_bin": target_bin,
            "x": bin_position["x"],
            "y": bin_position["y"],
            "z": bin_position["z"],
        },
        {"step": "open_gripper"},
        {
            "step": "return_home",
            "x": home["x"],
            "y": home["y"],
            "z": home["z"],
        },
    ]


def _bin_position(target_bin: str) -> dict:
    positions = getattr(config, "BIN_POSITIONS", {})
    if target_bin not in positions:
        raise ValueError(f"missing BIN_POSITIONS for target_bin: {target_bin}")

    return _position(positions[target_bin], f"BIN_POSITIONS.{target_bin}")


def _position(position: dict, name: str) -> dict:
    if not isinstance(position, dict):
        raise ValueError(f"{name} must be an object")

    return {
        "x": _number(position.get("x"), f"{name}.x"),
        "y": _number(position.get("y"), f"{name}.y"),
        "z": _number(position.get("z"), f"{name}.z"),
    }


def _number(value, name: str) -> float:
    if value is None:
        raise ValueError(f"{name} is required")
    if not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a number")

    return value
