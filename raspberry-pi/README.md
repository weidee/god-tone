# Raspberry Pi 控制端

Raspberry Pi 端負責拍照、呼叫 AI Server `/detect`、接收 AI Server 回傳的 `command`，再呼叫 ROS 節點控制機械手臂。

完整系統流程與 API 合約請看根目錄 [README.md](../README.md)。

目前沒有硬體，所以此模組先提供 mock 流程：

- `camera.py`：預設產生 mock 圖片。
- `agx_client.py`：將圖片上傳到 AI Server `/detect`，或在無設備時回傳 mock 偵測結果。
- `ros_control.py`：預設只印出 AI Server 回傳的控制指令。
- `server.py`：提供 `/trigger`，給 ESP32 或測試工具觸發一次分類流程。

## 檔案結構

```text
raspberry-pi/
├── server.py
├── run_once.py
├── camera.py
├── agx_client.py
├── ros_control.py
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
CAMERA_MODE = "mock"
CAMERA_IMAGE_PATH = "test_images/sample.jpg"
ROS_MODE = "mock"
COMMAND_ACTION = "pick_and_place"
TARGET_BINS = ["bin_a", "bin_b", "bin_c"]
SAFE_Z = 0.12
HOME_POSITION = {"x": 0.0, "y": 0.0, "z": 0.15}
BIN_POSITIONS = {
    "bin_a": {"x": 0.12, "y": 0.18, "z": 0.05},
    "bin_b": {"x": 0.22, "y": 0.18, "z": 0.05},
    "bin_c": {"x": 0.32, "y": 0.18, "z": 0.05},
}
```

沒有 AI Server 或網路環境時，先使用 `AGX_MODE = "mock"`。要串接 PC/AGX 上的 AI Server 時，改成：

```python
AGX_MODE = "http"
AGX_URL = "http://<AI_SERVER_IP>:8000"
```

沒有 Camera 但想用真圖片測流程時，可以改成：

```python
CAMERA_MODE = "file"
CAMERA_IMAGE_PATH = "/absolute/path/to/image.jpg"
```

`CAMERA_IMAGE_PATH` 也可以填相對路徑，會以 `config.py` 所在資料夾為基準。

不要提交 `config.py`。

## 無設備 smoke test

```bash
python smoke_test.py
```

這個測試不需要 Camera、ROS 或 AI Server，會用 mock camera、mock AGX result 與 mock ROS 跑完整流程。
測試也會啟動本機假的 `/detect` HTTP endpoint，驗證 `AGX_MODE = "http"` 時圖片會以 multipart 格式上傳，並確認 AI Server 回 `422` 時會轉成 `ValueError`。
測試也會確認 `CAMERA_MODE = "file"` 可以讀取指定圖片檔。

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

Raspberry Pi 收到 AI Server 的 `command` 後，會先檢查格式，再轉成 mock motion plan：

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

`SAFE_Z`、`HOME_POSITION`、`BIN_POSITIONS` 目前是 mock / 初始校正值。接硬體後要依照相機、工作區與手臂實際座標重新量測。

## 之後接硬體時要換的地方

- `camera.capture_image()`：把 mock 圖片改成實際 Camera 拍照。
- `CAMERA_MODE = "file"`：沒有 Camera 時可先用本機圖片測流程。
- `ros_control.execute_command()`：把 mock print 改成呼叫 ROS service/action/topic。
- `ros_control.validate_command()`：保留 command 格式驗證。
- `ros_control.build_motion_plan()`：保留任務步驟骨架，依實際手臂能力調整 motion steps 與座標。
- `config.py`：把 `CAMERA_MODE`、`ROS_MODE` 與 ROS topic 設定改成實際值。
