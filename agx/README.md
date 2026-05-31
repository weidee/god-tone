# AGX 模組

`agx/` 是本專題的 AGX 模組，負責接收 Raspberry Pi 上傳的圖片、執行 YOLOv8 推論、判斷垃圾類別與分類桶，並產生 Raspberry Pi 可用的 high-level command。即使暫時使用一般電腦執行，也一律視為 AGX。

AGX 不直接控制 ROS，也不直接操作機械手臂。Raspberry Pi 收到 AGX 回傳的 `command` 後，負責產生 motion_plan，並呼叫自己的 ROS 節點或 ArmPi Python 控制程式。

## 流程摘要

```text
Raspberry Pi 拍照
  -> 上傳影像給 AGX /detect
  -> Flask API 執行 YOLOv8 推論
  -> YOLO 輸出類別、邊界框、信心值、中心座標
  -> AGX 任務控制模組依類別對應 target_bin
  -> AGX 任務控制模組依中心座標產生 pick_zone 或 workspace_candidate
  -> AGX 產生 high-level command 並回傳給 Raspberry Pi
  -> Raspberry Pi 轉成 motion_plan 後呼叫 ROS / ArmPi 控制機械手臂
  -> Raspberry Pi 回到等待下一次觸發
```

完整系統流程與 API 合約請看根目錄 [README.md](../README.md)。

## 檔案結構

```text
agx/
├── server.py        # Flask API、錯誤回應
├── yolo_infer.py    # YOLO 模型載入與推論
├── task_control.py  # pick_zone / workspace_candidate 與控制指令產生
├── config.example.py
├── requirements.txt
├── smoke_test.py
├── README.md
└── models/
    └── .gitkeep
```

## 支援分類

- `tissue`
- `foil_pack`
- `plastic`

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
- `YOLO_INFER_MODE`
- `COORDINATE_MODE`
- `ZONE_SPLITS`
- 工作區座標轉換參數

目前已訓練模型放在根目錄的 `datasets/best.pt`，訓練 notebook 放在 `datasets/yolo_training.ipynb`。從 `agx/` 目錄啟動時，範例設定已指向：

```python
YOLO_MODEL_PATH = "../datasets/best.pt"
YOLO_INFER_MODE = "yolo"
```

如果還沒有 YOLO 模型或 CUDA 環境，可以在本機 `config.py` 改成：

```python
YOLO_INFER_MODE = "mock"
```

mock 模式仍會檢查上傳圖片是否可讀，並回傳固定的模擬偵測結果，方便先測 API 與 Raspberry Pi 呼叫流程。

demo 階段建議使用 `COORDINATE_MODE = "zone"`，AGX 只回傳 `pick_zone`，實際 ArmPi-FPV 夾取座標由 Raspberry Pi 端的 `PICK_POINTS` 決定。相機與手臂工作區校正完成後，再改用 `COORDINATE_MODE = "workspace"` 產生 `workspace_candidate`。

使用已訓練模型時，保持：

```python
YOLO_INFER_MODE = "yolo"
```

如果沒有 CUDA，可以先設定 `YOLO_DEVICE = "cpu"` 測試。

不要提交 `config.py` 或 YOLO 權重檔。

## 執行

```bash
python server.py
```

server 監聽 `0.0.0.0` 與 `config.FLASK_PORT`。

## 測試

mock 模式 smoke test：

```bash
python smoke_test.py
```

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
- `task_control.py` 只處理 `pick_zone` / `workspace_candidate` 與 high-level command 產生。
- `ValueError` 回傳 HTTP 422。
- 其他例外回傳 HTTP 500。
