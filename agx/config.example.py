YOLO_MODEL_PATH = "models/best.pt"
YOLO_CONF = 0.5
YOLO_DEVICE = "cuda"
YOLO_INFER_MODE = "mock"

FLASK_PORT = 8000

CLASS_NAMES = ["tissue", "foil_pack", "plastic_bottle"]

BIN_MAP = {
    "tissue": "bin_a",
    "foil_pack": "bin_b",
    "plastic_bottle": "bin_c",
}

MESSAGE_MAP = {
    "tissue": "已產生衛生紙分類控制指令",
    "foil_pack": "已產生鋁箔包分類控制指令",
    "plastic_bottle": "已產生塑膠瓶分類控制指令",
}

WORKSPACE_Z = 0.02

IMAGE_TO_WORKSPACE = {
    "scale_x": 0.001,
    "scale_y": 0.001,
    "offset_x": 0.0,
    "offset_y": 0.0,
}

MOCK_DETECTION = {
    "label": "plastic_bottle",
    "confidence": 0.91,
    "bbox_ratio": {
        "x1": 0.3,
        "y1": 0.25,
        "x2": 0.7,
        "y2": 0.75,
    },
}
