# Raspberry Pi 控制端

Raspberry Pi 端負責拍照、呼叫 AGX `/detect`、接收 AGX 回傳的 high-level `command`，再把 `pick_zone` 轉成 ArmPi-FPV motion_plan，最後呼叫 ROS 節點或 ArmPi Python 控制機械手臂。

完整系統流程與 API 合約請看根目錄 [README.md](../README.md)。

目前沒有硬體，所以此模組先提供 mock 流程：

- `camera.py`：預設產生 mock 圖片。
- `agx_client.py`：將圖片上傳到 AGX `/detect`，或在無設備時回傳 mock 偵測結果。
- `ros_control.py`：驗證 AGX 回傳的 high-level command，產生 motion plan，mock 模式只印出計畫，不呼叫真實 ROS；需要直接跑既有 Python 腳本時可切到 script 模式。
- `armpi_adapter.py`：預留 ArmPi-FPV 原廠 ROS / Python 控制函式轉接點，目前尚未接真實硬體。
- `server.py`：提供 `/trigger`，給 ESP32 或測試工具觸發一次分類流程。

## 檔案結構

```text
raspberry-pi/
├── server.py
├── run_once.py
├── camera.py
├── agx_client.py
├── ros_control.py
├── armpi_adapter.py
├── config.example.py
├── requirements.txt
├── smoke_test.py
└── README.md
```

## 設定

```bash
cd raspberry-pi
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.py config.py
```

編輯 `config.py`：

```python
AGX_URL = "http://192.168.x.x:8000"
AGX_MODE = "mock"
EXPECTED_AGX_SCHEMA_VERSION = "1.0"
FLASK_HOST = "0.0.0.0"
FLASK_PORT = 5000
CAMERA_MODE = "mock"
CAMERA_IMAGE_PATH = "test_images/sample.jpg"
ROS_MODE = "mock"
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

沒有 AGX 服務或網路環境時，先使用 `AGX_MODE = "mock"`。要透過 HTTP 串接 AGX 時，改成：

```python
AGX_MODE = "http"
AGX_URL = "http://<AGX_IP>:8000"
```

沒有 Camera 但想用真圖片測流程時，可以改成：

```python
CAMERA_MODE = "file"
CAMERA_IMAGE_PATH = "/absolute/path/to/image.jpg"
```

`CAMERA_IMAGE_PATH` 也可以填相對路徑，會以 `config.py` 所在資料夾為基準。

如果要讓 Raspberry Pi 收到 AGX command 後執行既有腳本，可以改成：

```python
ROS_MODE = "script"
SCRIPT_DIR = "/home/pi/api/srcipts"
BIN_SCRIPT_MAP = {
    "bin_a": "metal_10_10.py",
    "bin_b": "plastic_10_10.py",
    "bin_c": "paper_10_10.py",
}
```

script 模式仍會先驗證 AGX command 並產生 motion_plan，再依 `target_bin` 找腳本執行。`SCRIPT_PASS_JSON = True` 時會用環境變數 `TRASH_SORTING_COMMAND_JSON` 與 `TRASH_SORTING_MOTION_PLAN_JSON` 傳入 command 與 motion plan。mock 模式只會回傳預計執行的腳本資訊，不會呼叫真實硬體。

不要提交 `config.py`。

## 無設備 smoke test

```bash
python smoke_test.py
```

這個測試不需要 Camera、ROS 或 AGX 服務，會用 mock camera、mock AGX result 與 mock ROS 跑完整流程。
測試也會啟動本機假的 `/detect` HTTP endpoint，驗證 `AGX_MODE = "http"` 時圖片會以 multipart 格式上傳，並確認 AGX 回 `422` 時會轉成 `ValueError`。
測試也會確認 `CAMERA_MODE = "file"` 可以讀取指定圖片檔。
測試會用暫存腳本驗證 `ROS_MODE = "script"` 的路徑解析與執行流程，不會執行倉庫裡的硬體腳本。

## 執行 server

```bash
python server.py
```

健康檢查：

```bash
curl http://localhost:5000/ping
```

觸發一次流程：

```bash
curl -X POST http://localhost:5000/trigger
```

## 不開 server 單次執行

```bash
python run_once.py
```

## Motion plan

Raspberry Pi 收到 AGX 的 `command` 後，會先檢查格式，再用 `pick_zone` 查 `PICK_POINTS`，並搭配 `target_bin` 查 `BIN_POINTS` 產生 mock motion plan：

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

`PICK_POINTS`、`BIN_POINTS`、`SAFE_Z`、`HOME_POSITION` 目前是 mock / 初始校正值。接硬體後要依照相機、工作區與手臂實際座標重新量測。

## 之後接硬體時要換的地方

- `camera.capture_image()`：把 mock 圖片改成實際 Camera 拍照。
- `CAMERA_MODE = "file"`：沒有 Camera 時可先用本機圖片測流程。
- `armpi_adapter.py`：把 `move_to()`、`open_gripper()`、`close_gripper()`、`return_home()` 接到 ArmPi-FPV inverse kinematics、ROS service/action/topic 或原廠 Python 控制函式。
- `ros_control.execute_command()`：保留 command 驗證與 motion_plan 流程，接硬體時再決定是否改成呼叫 `armpi_adapter.py` 或 ROS 節點。
- `ros_control.validate_command()`：保留 command 格式驗證。
- `ros_control.build_motion_plan()`：保留任務步驟骨架，依實際手臂能力調整 motion steps 與座標。
- `config.py`：把 `CAMERA_MODE`、`ROS_MODE` 與 ROS topic 設定改成實際值。
