OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-4o-mini"

RPI_URL = "http://192.168.x.x:5000"

YOLO_MODEL_PATH = "models/best.pt"
YOLO_CONF = 0.5
YOLO_DEVICE = "cuda"

FLASK_PORT = 8000

CLASS_NAMES = ["tissue", "paper_box", "plastic_can"]

BIN_MAP = {
    "tissue": "bin_a",
    "paper_box": "bin_b",
    "plastic_can": "bin_c",
}

MESSAGE_MAP = {
    "tissue": "已將衛生紙放入一般垃圾桶",
    "paper_box": "已將紙盒放入紙類回收桶",
    "plastic_can": "已將塑膠罐放入塑膠回收桶",
}
