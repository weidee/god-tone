import json

import config


def execute_command(command: dict | None) -> dict:
    if command is None:
        return {"executed": False, "reason": "no command"}

    if config.ROS_MODE == "mock":
        print("Mock ROS command:")
        print(json.dumps(command, ensure_ascii=False, indent=2))
        return {"executed": True, "mode": "mock"}

    raise NotImplementedError("real ROS control is not implemented yet")
