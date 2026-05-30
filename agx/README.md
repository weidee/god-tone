# AGX AI Server

AGX 是本專題的 AI server，負責接收 Raspberry Pi 上傳的圖片、執行 YOLOv8 推論、計算工作區座標，並產生 Raspberry Pi 可用的控制指令。

AGX 不直接控制 ROS，也不直接操作機械手臂。Raspberry Pi 收到 AGX 回傳的 `command` 後，負責呼叫自己的 ROS 節點。

## 流程摘要

```text
Raspberry Pi 拍照
  -> 上傳影像給 AGX /detect
  -> Flask API 執行 YOLOv8 推論
  -> YOLO 輸出類別、邊界框、信心值、中心座標
  -> AGX 任務控制模組計算工作區座標
  -> AGX 任務控制模組產生控制指令
  -> AGX 將控制指令回傳給 Raspberry Pi
  -> Raspberry Pi 呼叫 ROS 節點控制機械手臂
  -> Raspberry Pi 回到等待下一張影像
```

完整系統流程與 API 合約請看根目錄 [README.md](../README.md)。

## 檔案結構

```text
agx/
├── server.py        # Flask API、錯誤回應
├── yolo_infer.py    # YOLO 模型載入與推論
├── task_control.py  # 工作區座標計算、控制指令產生
├── config.example.py
├── requirements.txt
├── README.md
└── models/
    └── .gitkeep
```

## 支援分類

- `tissue`
- `foil_pack`
- `plastic_bottle`

分類、bin 對應與回傳格式以根目錄 [README.md](../README.md) 為準。

## 安裝

從 `agx/` 目錄執行：

```bash
cd agx
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

建立本機設定：

```bash
cp config.example.py config.py
```

編輯 `config.py`：

- `YOLO_MODEL_PATH`
- `YOLO_CONF`
- `YOLO_DEVICE`
- 工作區座標轉換參數

如果 AGX 還沒有 CUDA 環境，可以先設定 `YOLO_DEVICE = "cpu"` 測試。

手動放入 YOLO 模型：

```text
agx/models/best.pt
```

不要提交 `config.py` 或 `models/best.pt`。

## 執行

```bash
python server.py
```

server 監聽 `0.0.0.0` 與 `config.FLASK_PORT`。

## 測試

健康檢查：

```bash
curl http://localhost:8000/ping
```

圖片偵測：

```bash
curl -X POST http://localhost:8000/detect \
  -F "image=@/path/to/image.jpg"
```

## 注意事項

- `server.py` 只處理 Flask routes 與錯誤回應。
- `yolo_infer.py` 只處理 YOLO 模型載入與推論。
- `task_control.py` 只處理座標轉換與控制指令產生。
- `ValueError` 回傳 HTTP 422。
- 其他例外回傳 HTTP 500。
