import json

import armpi_adapter
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

    if config.ROS_MODE == "armpi":
        execute_motion_plan(motion_plan)
        return {"executed": True, "mode": "armpi", "motion_plan": motion_plan}

    raise NotImplementedError("real ROS control is not implemented yet")


def validate_command(command: dict) -> None:
    if not isinstance(command, dict):
        raise ValueError("command must be an object")

    action = command.get("action")
    if action != config.COMMAND_ACTION:
        raise ValueError(f"unsupported command action: {action}")

    target_bin = command.get("target_bin")
    if target_bin not in config.BIN_POINTS:
        raise ValueError(f"unsupported target_bin: {target_bin}")

    pick_zone = command.get("pick_zone")
    workspace_candidate = command.get("workspace_candidate")
    if pick_zone is None and workspace_candidate is None:
        raise ValueError("command.pick_zone is required")

    if pick_zone is not None and pick_zone not in config.PICK_POINTS:
        raise ValueError(f"unsupported pick_zone: {pick_zone}")

    if pick_zone is None:
        _position(workspace_candidate, "command.workspace_candidate")


def build_motion_plan(command: dict) -> list[dict]:
    pick = _pick_position(command)
    target_bin = command["target_bin"]
    bin_position = _bin_point(target_bin)
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


def execute_motion_plan(motion_plan: list[dict]) -> None:
    for step in motion_plan:
        name = step["step"]

        if name.startswith("move_") or name == "lift":
            armpi_adapter.move_to(step["x"], step["y"], step["z"])
        elif name == "close_gripper":
            armpi_adapter.close_gripper()
        elif name == "open_gripper":
            armpi_adapter.open_gripper()
        elif name == "return_home":
            armpi_adapter.return_home()
        else:
            raise ValueError(f"unknown motion step: {name}")


def _pick_position(command: dict) -> dict:
    pick_zone = command.get("pick_zone")
    if pick_zone is not None:
        return _pick_point(pick_zone)

    return _position(command.get("workspace_candidate"), "command.workspace_candidate")


def _pick_point(pick_zone: str) -> dict:
    points = config.PICK_POINTS
    if pick_zone not in points:
        raise ValueError(f"missing PICK_POINTS for pick_zone: {pick_zone}")

    return _position(points[pick_zone], f"PICK_POINTS.{pick_zone}")


def _bin_point(target_bin: str) -> dict:
    points = config.BIN_POINTS
    if target_bin not in points:
        raise ValueError(f"missing BIN_POINTS for target_bin: {target_bin}")

    return _position(points[target_bin], f"BIN_POINTS.{target_bin}")


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
