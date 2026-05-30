# Raspberry Pi 控制端

Raspberry Pi 端負責拍照、呼叫 AGX `/detect`、接收 AGX 回傳的 `command`，再呼叫 ROS 節點控制機械手臂。

完整系統流程與 API 合約請看根目錄 [README.md](../README.md)。

目前沒有硬體，所以此模組先提供 mock 流程：

- `camera.py`：預設產生 mock 圖片。
- `agx_client.py`：將圖片上傳到 AGX `/detect`。
- `ros_control.py`：預設只印出 AGX 回傳的控制指令。
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
CAMERA_MODE = "mock"
ROS_MODE = "mock"
```

不要提交 `config.py`。

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

## 之後接硬體時要換的地方

- `camera.capture_image()`：把 mock 圖片改成實際 Camera 拍照。
- `ros_control.execute_command()`：把 mock print 改成呼叫 ROS service/action/topic。
- `config.py`：把 `CAMERA_MODE`、`ROS_MODE` 與 ROS topic 設定改成實際值。
