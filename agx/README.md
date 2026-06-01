# AGX 模組

`agx/` 負責接收 Raspberry Pi 上傳的圖片、執行 YOLOv8 推論、輸出偵測結果、決定分類桶，並產生 Raspberry Pi 可執行的 high-level command。

AGX 不直接控制 ROS，也不直接操作機械手臂。Raspberry Pi 收到 AGX 回傳的 `command` 後，負責產生 motion plan 並呼叫 ROS / ArmPi 控制程式。

## 流程

```text
Raspberry Pi 上傳影像
  -> Flask /detect 接收 multipart image
  -> yolo_infer.py 載入 YOLOv8 並推論
  -> 選擇最高 confidence 偵測結果
  -> task_control.py 對應 label/bin
  -> 依 center 產生 pick_zone 或 workspace_candidate
  -> 產生 pick_and_place command
  -> 回傳 JSON 給 Raspberry Pi
```

完整系統流程與 API 合約請看根目錄 [README.md](../README.md)。

## 檔案結構

```text
agx/
├── server.py        # Flask API 與錯誤回應
├── yolo_infer.py    # YOLO 模型載入與推論
├── task_control.py  # label/bin、座標與 command 產生
├── config.example.py
├── requirements.txt
├── README.md
└── models/
```

## 支援分類

- `metal` -> `bin_a`
- `plastic` -> `bin_b`
- `paper` -> `bin_c`

YOLO 權重輸出的 class name 必須與上述 label 完全一致。

## 安裝

```bash
cd agx
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.py config.py
```

不要提交 `config.py` 或 YOLO 權重檔。

## 設定

`config.py` 必須包含：

```python
YOLO_MODEL_PATH = "../datasets/best.pt"
YOLO_CONF = 0.5
YOLO_DEVICE = "cuda"
YOLO_INFER_MODE = "yolo"

FLASK_HOST = "0.0.0.0"
FLASK_PORT = 8000

SCHEMA_VERSION = "1.0"
COMMAND_ACTION = "pick_and_place"

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
```

`COORDINATE_MODE = "zone"` 時，AGX 回傳 `pick_zone`。`COORDINATE_MODE = "workspace"` 時，AGX 回傳 `workspace_candidate`。

## 執行

```bash
python server.py
```

server 監聽 `config.FLASK_HOST` 與 `config.FLASK_PORT`。

健康檢查：

```bash
curl http://localhost:8000/ping
```

圖片偵測：

```bash
curl -X POST http://localhost:8000/detect \
  -F "image=@/path/to/image.jpg"
```

## 模組規則

- `server.py` 只處理 Flask routes 與 HTTP 錯誤回應。
- `yolo_infer.py` 只處理圖片解析、YOLO 模型載入與推論結果整理。
- `task_control.py` 只處理 label/bin、`pick_zone` / `workspace_candidate` 與 high-level command 產生。
- `ValueError` 回傳 HTTP `422`。
- 其他例外回傳 HTTP `500`。
- AGX 不呼叫 Raspberry Pi，不呼叫 ROS，不控制機械手臂。
