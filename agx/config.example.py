YOLO_MODEL_PATH = "../datasets/best.pt"
YOLO_CONF = 0.5
YOLO_DEVICE = "cuda"
YOLO_INFER_MODE = "yolo"

FLASK_PORT = 8000

SCHEMA_VERSION = "1.0"

CLASS_NAMES = ["metal", "plastic", "paper"]

BIN_MAP = {
    "metal": "bin_a",
    "plastic": "bin_b",
    "paper": "bin_c",
}

MESSAGE_MAP = {
    "metal": "已產生金屬分類控制指令",
    "plastic": "已產生塑膠分類控制指令",
    "paper": "已產生紙類分類控制指令",
}

WORKSPACE_Z = 0.02

COORDINATE_MODE = "zone"
ZONE_SPLITS = [0.33, 0.66]

IMAGE_TO_WORKSPACE = {
    "scale_x": 0.001,
    "scale_y": 0.001,
    "offset_x": 0.0,
    "offset_y": 0.0,
}

MOCK_DETECTION = {
    "label": "plastic",
    "confidence": 0.91,
    "bbox_ratio": {
        "x1": 0.3,
        "y1": 0.25,
        "x2": 0.7,
        "y2": 0.75,
    },
}
