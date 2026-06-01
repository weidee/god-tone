# ESP32 + ArmPi-FPV 智慧垃圾分類系統

本專題使用 ESP32 觸發分類任務，Raspberry Pi / ArmPi-FPV 負責拍照與機械手臂控制，AGX 負責 YOLOv8 影像辨識、分類決策與 high-level command 產生。系統模組之間使用 HTTP API 溝通；AGX 不直接控制 ROS 或機械手臂，Raspberry Pi 收到 AGX 回傳的 command 後再轉成 ArmPi-FPV motion plan 執行。

## 系統流程

```text
ESP32 偵測到觸發訊號
  -> 呼叫 Raspberry Pi /trigger
  -> Raspberry Pi 擷取 Camera 影像
  -> Raspberry Pi 上傳影像到 AGX /detect
  -> AGX 執行 YOLOv8 推論
  -> AGX 輸出 label、bbox、confidence、center
  -> AGX 依 label 對應 target_bin
  -> AGX 依 center 產生 pick_zone 或 workspace_candidate
  -> AGX 回傳 high-level command
  -> Raspberry Pi 驗證 command
  -> Raspberry Pi 產生 ArmPi-FPV motion_plan
  -> Raspberry Pi 呼叫 ROS / ArmPi Python 控制機械手臂
  -> Raspberry Pi 回到等待下一次觸發
```

## 核心檔案

```text
.
├── README.md
├── agx/
│   ├── server.py
│   ├── task_control.py
│   ├── yolo_infer.py
│   ├── config.example.py
│   ├── requirements.txt
│   ├── README.md
│   └── models/
├── esp32/
├── raspberry-pi/
│   ├── server.py
│   ├── run_once.py
│   ├── camera.py
│   ├── agx_client.py
│   ├── ros_control.py
│   ├── armpi_adapter.py
│   ├── config.example.py
│   ├── requirements.txt
│   └── README.md
└── datasets/
    ├── README.md
    ├── yolo_training.ipynb
    ├── best.pt
    └── raw/
```

## 模組分工

| 模組 | 職責 | 邊界 |
| --- | --- | --- |
| `esp32/` | 偵測使用者觸發事件，通知 Raspberry Pi 開始分類任務 | 不做影像辨識，不控制機械手臂 |
| `raspberry-pi/` | 拍照、呼叫 AGX、驗證 command、產生 motion_plan、呼叫 ROS / ArmPi 控制機械手臂 | 不執行 YOLO，不自行決定分類結果 |
| `agx/` | 提供 YOLO 推論 API、輸出 bbox/center、決定 label/bin、產生 high-level command | 不直接呼叫 ROS，不操作機械手臂 |
| `datasets/` | 保存訓練 notebook、權重位置與資料集說明 | 不放 runtime 程式 |

## 支援分類

| 垃圾 | Label | Bin | 回傳訊息 |
| --- | --- | --- | --- |
| 金屬 | `metal` | `bin_a` | `已產生金屬分類控制指令` |
| 塑膠 | `plastic` | `bin_b` | `已產生塑膠分類控制指令` |
| 紙類 | `paper` | `bin_c` | `已產生紙類分類控制指令` |

YOLO 權重輸出的 class name 必須與 `metal`、`plastic`、`paper` 完全一致；其他 label 由 AGX 以 `422` 回應。

## AGX API

### `GET /ping`

成功回應 `200`：

```json
{"status": "ok", "yolo": "loaded"}
```

### `POST /detect`

請求格式為 `multipart/form-data`：

| Key | Value |
| --- | --- |
| `image` | jpg 或 png 圖片 |

成功回應 `200`：

```json
{
  "schema_version": "1.0",
  "label": "plastic",
  "bin": "bin_b",
  "message": "已產生塑膠分類控制指令",
  "confidence": 0.91,
  "image_size": {
    "width": 640,
    "height": 480
  },
  "detection": {
    "bbox": {
      "x1": 120,
      "y1": 80,
      "x2": 260,
      "y2": 220
    },
    "center": {
      "x": 190,
      "y": 150
    }
  },
  "pick_zone": "left",
  "workspace_candidate": null,
  "workspace": null,
  "command": {
    "action": "pick_and_place",
    "target_bin": "bin_b",
    "pick_zone": "left"
  }
}
```

未偵測到可分類物件時回應 `200`：

```json
{
  "schema_version": "1.0",
  "bin": null,
  "label": null,
  "message": "未偵測到垃圾",
  "confidence": null,
  "image_size": null,
  "detection": null,
  "pick_zone": null,
  "workspace_candidate": null,
  "workspace": null,
  "command": null
}
```

錯誤回應：

| 狀況 | HTTP |
| --- | --- |
| 請求資料或辨識結果不符合合約 | `422` |
| 服務內部例外 | `500` |

## Raspberry Pi API

### `GET /ping`

成功回應 `200`：

```json
{"status": "ok"}
```

### `POST /trigger`

成功流程：

```text
camera.capture_image()
  -> agx_client.detect()
  -> ros_control.execute_command()
  -> 回傳 AGX 結果與 ROS / ArmPi 執行狀態
```

成功回應 `200`：

```json
{
  "status": "done",
  "agx": {
    "label": "plastic",
    "bin": "bin_b",
    "command": {
      "action": "pick_and_place",
      "target_bin": "bin_b",
      "pick_zone": "left"
    }
  },
  "ros": {
    "executed": true,
    "mode": "script",
    "motion_plan": [
      {"step": "move_above_pick", "x": 0.18, "y": 0.08, "z": 0.12},
      {"step": "move_to_pick", "x": 0.18, "y": 0.08, "z": 0.02},
      {"step": "close_gripper"},
      {"step": "lift", "x": 0.18, "y": 0.08, "z": 0.12},
      {"step": "move_above_bin", "target_bin": "bin_b", "x": 0.32, "y": 0.00, "z": 0.12},
      {"step": "move_to_bin", "target_bin": "bin_b", "x": 0.32, "y": 0.00, "z": 0.05},
      {"step": "open_gripper"},
      {"step": "return_home", "x": 0.0, "y": 0.0, "z": 0.15}
    ],
    "script": {
      "target_bin": "bin_b",
      "name": "plastic_10_10.py",
      "path": "/path/to/raspberry-pi/api/srcipts/plastic_10_10.py"
    }
  }
}
```

錯誤回應：

| 狀況 | HTTP |
| --- | --- |
| command、AGX 回應或設定資料不符合合約 | `422` |
| AGX 連線、ROS / ArmPi 執行或服務內部例外 | `500` |

## Command 合約

AGX 回傳給 Raspberry Pi 的 `command` 必須符合：

```json
{
  "action": "pick_and_place",
  "target_bin": "bin_b",
  "pick_zone": "left"
}
```

或使用工作區座標：

```json
{
  "action": "pick_and_place",
  "target_bin": "bin_b",
  "workspace_candidate": {
    "x": 0.18,
    "y": 0.08,
    "z": 0.02
  }
}
```

欄位規則：

| 欄位 | 規則 |
| --- | --- |
| `action` | 固定為 `pick_and_place` |
| `target_bin` | 只能是 `bin_a`、`bin_b`、`bin_c` |
| `pick_zone` | 只能是 `left`、`middle`、`right` |
| `workspace_candidate` | 包含數值 `x`、`y`、`z` |
| `pick_zone` / `workspace_candidate` | 二選一 |

## Motion Plan

Raspberry Pi 將 command 轉成以下標準步驟：

```text
move_above_pick
  -> move_to_pick
  -> close_gripper
  -> lift
  -> move_above_bin
  -> move_to_bin
  -> open_gripper
  -> return_home
```

`PICK_POINTS` 負責把 `left`、`middle`、`right` 對到手臂夾取點；`BIN_POINTS` 負責把 `bin_a`、`bin_b`、`bin_c` 對到分類桶位置；`WORKSPACE_LIMITS` 負責限制 AGX 給的工作區座標。

## AGX 設定

倉庫只保留 `agx/config.example.py`。本機執行時複製成不提交的 `agx/config.py`。

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

## Raspberry Pi 設定

倉庫只保留 `raspberry-pi/config.example.py`。本機執行時複製成不提交的 `raspberry-pi/config.py`。

```python
AGX_URL = "http://<AGX_IP>:8000"
EXPECTED_AGX_SCHEMA_VERSION = "1.0"

FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000

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
```

## 執行入口

AGX：

```bash
cd agx
python server.py
```

Raspberry Pi server：

```bash
cd raspberry-pi
python server.py
```

Raspberry Pi 單次任務：

```bash
cd raspberry-pi
python run_once.py
```

## 開發規格檢查

目前文件已覆蓋以下開發規格：

- 模組責任與禁止跨界行為。
- `metal`、`plastic`、`paper` label 與 bin 對應。
- AGX `/ping`、`/detect` API request / response。
- Raspberry Pi `/ping`、`/trigger` API request / response。
- command schema 與 motion plan schema。
- AGX 與 Raspberry Pi 設定檔欄位。
- HTTP `422` / `500` 錯誤規則。
- runtime 入口檔。

仍需依實機校正或外部決策補上的項目：

- ESP32 觸發 Raspberry Pi 的實際網路位置與 payload。
- Camera 擷取方式與圖片格式細節。
- `IMAGE_TO_WORKSPACE` 相機到工作區座標校正參數。
- `PICK_POINTS`、`BIN_POINTS`、`WORKSPACE_LIMITS` 的實測座標。
- ROS service/action/topic 或 ArmPi Python 控制函式的最終名稱。

## 開發注意事項

- 專案維持三個硬體/系統模組：`esp32/`、`raspberry-pi/`、`agx/`。
- AGX 只回傳 high-level command；motion plan 與 ROS / ArmPi 控制由 Raspberry Pi 端實作。
- 模組之間使用 HTTP API 溝通，不共用本機程式碼。
- 不要提交真實 API key、WiFi 密碼、本機設定檔、YOLO 權重或原始資料集。
- 不要提交 `agx/config.py`、`esp32/config.h`、`raspberry-pi/config.py`、YOLO 權重或原始資料集。
- 原始標註資料放在 `datasets/raw/`，並由 git 忽略。
