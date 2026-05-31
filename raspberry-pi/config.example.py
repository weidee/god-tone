AGX_URL = "http://192.168.x.x:8000"
AGX_MODE = "mock"

FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000

CAMERA_MODE = "mock"
CAMERA_IMAGE_PATH = "test_images/sample.jpg"

ROS_MODE = "mock"
ROS_NODE_NAME = "trash_sorting_arm"
ROS_COMMAND_TOPIC = "/trash_sorting/command"

REQUEST_TIMEOUT = 10

COMMAND_ACTION = "pick_and_place"

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
