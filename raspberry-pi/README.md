# Raspberry Pi 控制端

`raspberry-pi/` 負責接收 ESP32 觸發、擷取 Camera 影像、呼叫 AGX `/detect`、驗證 AGX 回傳的 high-level `command`、產生 ArmPi-FPV motion plan，並呼叫 ROS / ArmPi Python 控制機械手臂。

完整系統流程與 API 合約請看根目錄 [README.md](../README.md)。

## 流程

```text
POST /trigger
  -> camera.capture_image()
  -> agx_client.detect()
  -> ros_control.validate_command()
  -> ros_control.build_motion_plan()
  -> ros_control.execute_command()
  -> 回傳 AGX 結果與 ROS / ArmPi 執行狀態
```

## 檔案結構

```text
raspberry-pi/
├── server.py         # Flask API
├── run_once.py       # 單次任務入口
├── camera.py         # Camera 擷取介面
├── agx_client.py     # AGX HTTP client 與回應驗證
├── ros_control.py    # command 驗證、motion plan 與執行流程
├── armpi_adapter.py  # ArmPi / ROS 控制轉接層
├── config.example.py
├── requirements.txt
└── README.md
```

## 安裝

```bash
cd raspberry-pi
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.py config.py
```

不要提交 `config.py`。

## 設定

`config.py` 必須包含：

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

`SCRIPT_PASS_JSON = True` 時，script 執行環境會收到：

| 環境變數 | 內容 |
| --- | --- |
| `TRASH_SORTING_COMMAND_JSON` | AGX command JSON |
| `TRASH_SORTING_MOTION_PLAN_JSON` | Raspberry Pi 產生的 motion plan JSON |

## 執行

server：

```bash
python server.py
```

健康檢查：

```bash
curl http://localhost:5000/ping
```

觸發一次分類：

```bash
curl -X POST http://localhost:5000/trigger
```

單次任務：

```bash
python run_once.py
```

## Command 驗證

Raspberry Pi 收到 AGX 的 `command` 後必須驗證：

- `command` 是 object。
- `action` 等於 `COMMAND_ACTION`。
- `target_bin` 存在於 `BIN_POINTS`。
- `pick_zone` 存在於 `PICK_POINTS`，或 `workspace_candidate` 是合法座標。
- `pick_zone` 與 `workspace_candidate` 只能二選一。
- `workspace_candidate` 必須落在 `WORKSPACE_LIMITS` 內。

## Motion Plan

`ros_control.build_motion_plan()` 固定產生：

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

座標來源：

| 資料 | 來源 |
| --- | --- |
| 夾取點 | `pick_zone` 對應 `PICK_POINTS`，或 `workspace_candidate` |
| 分類桶 | `target_bin` 對應 `BIN_POINTS` |
| 安全高度 | `SAFE_Z` |
| 回原點 | `HOME_POSITION` |

## 模組規則

- `server.py` 只處理 `/ping`、`/trigger` 與 HTTP 錯誤回應。
- `camera.py` 只提供 `capture_image()`，回傳圖片 bytes。
- `agx_client.py` 只呼叫 AGX `/detect` 並驗證 AGX 回應。
- `ros_control.py` 保留 command 驗證、motion plan 產生與執行流程。
- `armpi_adapter.py` 是 ROS / ArmPi 控制轉接層。
- Raspberry Pi 不執行 YOLO，不自行改寫 AGX 分類結果。
- `ValueError` 回傳 HTTP `422`。
- 其他例外回傳 HTTP `500`。
