# AGX Skill Server

AGX is the AI decision server for the smart trash sorting system. It receives voice text from ESP32, receives images from Raspberry Pi, runs YOLOv8 inference for image input, asks the Skill flow for the final class, and sends bin movement commands to Raspberry Pi.

## Directory Structure

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

## Setup

Run commands from the `agx/` directory unless noted otherwise.

```bash
cd agx
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Create local config:

```bash
cp config.example.py config.py
```

Edit `config.py` and fill in:

- `OPENAI_API_KEY`
- `RPI_URL`
- YOLO settings if your model path, confidence threshold, or device differs

If the AGX device does not have CUDA ready yet, set `YOLO_DEVICE = "cpu"` for local testing.

Place the YOLO model manually at:

```text
agx/models/best.pt
```

Do not commit `config.py` or `models/best.pt`.

## Run

```bash
python server.py
```

The server listens on `0.0.0.0` and `config.FLASK_PORT`.

## Test

Ping:

```bash
curl http://localhost:8000/ping
```

Voice classification:

```bash
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "這是紙盒"}'
```

Image detection:

```bash
curl -X POST http://localhost:8000/detect \
  -F "image=@/path/to/image.jpg"
```

## Notes

- `server.py` handles Flask routes and error responses.
- `skill.py` handles prompts, OpenAI calls, class parsing, and Raspberry Pi `/move` dispatch.
- `yolo_infer.py` handles YOLO model loading and inference.
- YOLO image input is converted to RGB before inference.
- YOLO class names should match `CLASS_NAMES` in `config.py`.
- `ValueError` returns HTTP 422.
- Other exceptions return HTTP 500.

## Common Issues

- `ModuleNotFoundError: No module named 'config'`: copy `config.example.py` to `config.py` inside `agx/`.
- Model load failure: confirm `agx/models/best.pt` exists and run `python server.py` from `agx/`.
- Raspberry Pi move failure: AGX still returns the classification result and prints a warning log.
