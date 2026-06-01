AGX_URL = "http://192.168.x.x:8000"
AGX_MODE = "mock"
EXPECTED_AGX_SCHEMA_VERSION = "1.0"

FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000

CAMERA_MODE = "mock"
CAMERA_IMAGE_PATH = "test_images/sample.jpg"

ROS_MODE = "mock"
ROS_NODE_NAME = "trash_sorting_arm"
ROS_COMMAND_TOPIC = "/trash_sorting/command"

REQUEST_TIMEOUT = 10
CAPTURE_FILENAME = "capture.jpg"
CAPTURE_MIME_TYPE = "image/jpeg"

COMMAND_ACTION = "pick_and_place"
CLASS_NAMES = ["metal", "plastic", "paper"]
BIN_MAP = {
    "metal": "bin_a",
    "plastic": "bin_b",
    "paper": "bin_c",
}

SCRIPT_DIR = "api/srcipts"
SCRIPT_PYTHON = "python3"
SCRIPT_TIMEOUT = 120
SCRIPT_PASS_JSON = True
BIN_SCRIPT_MAP = {
    "bin_a": "metal_10_10.py",
    "bin_b": "plastic_10_10.py",
    "bin_c": "paper_10_10.py",
}

PICK_POINTS = {
    "left": {"x": 0.18, "y": 0.08, "z": 0.02},
    "middle": {"x": 0.23, "y": 0.00, "z": 0.02},
    "right": {"x": 0.18, "y": -0.08, "z": 0.02},
}
BIN_POINTS = {
    "bin_a": {"x": 0.30, "y": 0.16, "z": 0.05},
    "bin_b": {"x": 0.32, "y": 0.00, "z": 0.05},
    "bin_c": {"x": 0.30, "y": -0.16, "z": 0.05},
}
SAFE_Z = 0.12
HOME_POSITION = {"x": 0.0, "y": 0.0, "z": 0.15}
WORKSPACE_LIMITS = {
    "x": {"min": -0.05, "max": 0.40},
    "y": {"min": -0.25, "max": 0.25},
    "z": {"min": 0.00, "max": 0.20},
}

MOCK_AGX_RESULT = {
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
