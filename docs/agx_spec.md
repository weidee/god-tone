# AGX MVP Specification

AGX is the AI decision server for the smart trash sorting system. For this MVP, implement only the `agx/` module and the explicitly requested root support files.

## Scope

- Receive voice text from ESP32 through `POST /classify`.
- Receive image bytes from Raspberry Pi through `POST /detect` and run YOLOv8 inference.
- Use the Skill flow with OpenAI to produce the final class.
- Send `POST /move` commands to Raspberry Pi.
- Do not implement ESP32 or Raspberry Pi code in this task.

## Classes

Supported labels:

- `tissue`
- `paper_box`
- `plastic_can`

Bin mapping:

- `tissue` -> `bin_a`
- `paper_box` -> `bin_b`
- `plastic_can` -> `bin_c`

## Files

Create this AGX structure:

```text
agx/
├── server.py
├── skill.py
├── yolo_infer.py
├── config.example.py
├── requirements.txt
├── README.md
└── models/
    └── .gitkeep
```

Do not create:

- `agx/config.py`
- `agx/models/best.pt`
- real API key files

## Configuration

All configurable values must be read from `config.py` at runtime. The repository only contains `agx/config.example.py`.

Required config values:

```python
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
```

## API

### `GET /ping`

Response `200`:

```json
{"status": "ok", "yolo": "loaded"}
```

### `POST /classify`

Request JSON:

```json
{"text": "這是紙盒"}
```

Success `200`:

```json
{"bin": "bin_b", "label": "paper_box", "message": "已將紙盒放入紙類回收桶", "confidence": null}
```

Invalid classification `422`:

```json
{"error": "無法辨識類別: <raw>"}
```

General error `500`:

```json
{"error": "<error message>"}
```

### `POST /detect`

Request multipart form-data:

- key: `image`
- value: jpg or png image file

Success `200`:

```json
{"bin": "bin_c", "label": "plastic_can", "message": "已將塑膠罐放入塑膠回收桶", "confidence": 0.91}
```

No detection `200`:

```json
{"bin": null, "label": null, "message": "未偵測到垃圾", "confidence": null}
```

Invalid request `422` for `ValueError`; other exceptions return `500`.

## Implementation Notes

- `server.py` handles routing and error responses only.
- `skill.py` handles prompt creation, OpenAI calls, parsing, and Raspberry Pi dispatch.
- `yolo_infer.py` handles YOLO model loading and inference only.
- `ValueError` returns HTTP 422.
- Other exceptions return HTTP 500.
- Raspberry Pi `/move` failures should be logged with `print` and must not block returning the classification result.
