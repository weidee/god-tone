# ESP32 + ArmPi 智慧垃圾分類系統

本專題使用 ESP32 觸發任務，Raspberry Pi 拍照並呼叫 ROS 節點控制機械手臂，AGX 執行 YOLOv8 影像辨識與任務控制指令產生，完成垃圾分類展示流程。

AGX 模組放在 `agx/` 目錄。若暫時使用一般電腦執行推論服務，文件與程式仍一律稱為 AGX。若尚未取得 AGX、YOLO 模型、Camera 或機械手臂，可先使用 mock 模式完成 API 與流程整合。

目前專案採用三個模組分工，避免過度拆層：

```text
ESP32 觸發任務
  -> Raspberry Pi 拍照
  -> Raspberry Pi 將圖片上傳到 AGX /detect
  -> AGX 執行 YOLOv8 推論
  -> AGX 取得類別、邊界框、信心值、中心座標
  -> AGX 任務控制模組計算工作區座標
  -> AGX 任務控制模組產生控制指令
  -> AGX 將控制指令回傳給 Raspberry Pi
  -> Raspberry Pi 呼叫 ROS 節點控制機械手臂
  -> Raspberry Pi 回到等待下一張影像
```

## 專案結構

```text
.
├── README.md
├── AGENTS.md
├── CLAUDE.md
├── agx/
│   ├── server.py
│   ├── task_control.py
│   ├── yolo_infer.py
│   ├── config.example.py
│   ├── requirements.txt
│   ├── smoke_test.py
│   ├── README.md
│   └── models/
│       └── .gitkeep
├── esp32/
│   └── .gitkeep
├── raspberry-pi/
│   ├── server.py
│   ├── run_once.py
│   ├── camera.py
│   ├── agx_client.py
│   ├── ros_control.py
│   ├── config.example.py
│   ├── requirements.txt
│   ├── smoke_test.py
│   └── README.md
└── datasets/
    ├── README.md
    ├── yolo_training.ipynb
    ├── best.pt
    └── raw/
```

## 模組分工

| 模組 | 硬體 | 職責 | 狀態 |
| --- | --- | --- | --- |
| `esp32/` | ESP32、按鈕、麥克風或喇叭 | 觸發系統開始任務，細節由 ESP32 組員決定 | 尚未實作 |
| `raspberry-pi/` | Raspberry Pi、Camera、ROS、機械手臂 | 拍照、呼叫 AGX `/detect`、接收控制指令、呼叫 ROS 節點控制機械手臂 | Mock MVP 已實作 |
| `agx/` | NVIDIA AGX | Flask API、YOLO 推論、座標轉換、任務控制指令產生 | 已可使用訓練模型推論 |
| `datasets/` | 本機資料夾 | 訓練 notebook、訓練權重與標註資料 | 已放入訓練成果 |

## 目前實作狀態

目前沒有實際硬體時，已完成可在本機驗證的流程：

- `agx/` AGX 模組支援 `YOLO_INFER_MODE = "mock"` 與 `YOLO_INFER_MODE = "yolo"`，目前範例設定指向已訓練權重 `datasets/best.pt`。
- `raspberry-pi/` 支援 `CAMERA_MODE = "mock"` 與 `CAMERA_MODE = "file"`。
- `raspberry-pi/` 支援 `AGX_MODE = "mock"` 與 `AGX_MODE = "http"`。
- Raspberry Pi 端會驗證 AGX 回傳的 `command`，再產生 `motion_plan`。
- `smoke_test.py` 只作為開發驗證入口，不是 runtime 流程；正式執行入口是各模組的 `server.py` 或 `run_once.py`。

尚未完成、需等硬體或模型確認後實作：

- ESP32 實際觸發方式。
- Raspberry Pi 真實 Camera 擷取。
- Raspberry Pi 真實 ROS / ArmPi 控制。
- 相機座標到手臂工作區座標的校正參數。

建議下一步：

- 用本機圖片搭配 `CAMERA_MODE = "file"` 測 Raspberry Pi 流程。
- 在同一台電腦跑 AGX mock 與 Raspberry Pi server，測 `AGX_MODE = "http"` 的雙 server 整合。
- 用實拍圖片校正 `IMAGE_TO_WORKSPACE` 參數。

## AI 工具入口

不同 AI coding 工具請先閱讀以下檔案，避免讀到不同版本的規格：

| 工具 | 入口檔 |
| --- | --- |
| Codex | `AGENTS.md` |
| Claude | `CLAUDE.md` |
| OpenCode | `AGENTS.md` |

專案規格以 `README.md` 為主，AI 開發規則以 `AGENTS.md` 為主。`CLAUDE.md` 只作為入口提示，不另外維護一份規格。

## 模組邊界

- ESP32 只負責觸發系統，AGX 不假設 ESP32 的實作方式。
- Raspberry Pi 負責拍照、上傳圖片、接收 AGX 控制指令，以及呼叫 ROS 節點控制機械手臂。
- AGX 負責 YOLO 推論、整理偵測結果、計算工作區座標、產生控制指令。
- AGX 不直接控制 ROS，也不直接操作機械手臂。
- 模組之間使用 HTTP API 溝通，不共用本機程式碼。

## 支援分類

| 垃圾 | Label | Bin | 回傳訊息 |
| --- | --- | --- | --- |
| 衛生紙 | `tissue` | `bin_a` | `已產生衛生紙分類控制指令` |
| 鋁箔包 | `foil_pack` | `bin_b` | `已產生鋁箔包分類控制指令` |
| 塑膠 | `plastic` | `bin_c` | `已產生塑膠分類控制指令` |

## API 合約

### AGX `GET /ping`

成功回應 `200`：

```json
{"status": "ok", "yolo": "loaded"}
```

### AGX `POST /detect`

請求格式為 `multipart/form-data`：

| Key | Value |
| --- | --- |
| `image` | jpg 或 png 圖片 |

成功回應 `200`：

```json
{
  "label": "plastic",
  "bin": "bin_c",
  "message": "已產生塑膠分類控制指令",
  "confidence": 0.91,
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
  "workspace": {
    "x": 0.23,
    "y": -0.08,
    "z": 0.02
  },
  "command": {
    "action": "pick_and_place",
    "target_bin": "bin_c",
    "pick": {
      "x": 0.23,
      "y": -0.08,
      "z": 0.02
    }
  }
}
```

沒有偵測到垃圾時回應 `200`：

```json
{"bin": null, "label": null, "message": "未偵測到垃圾", "confidence": null, "detection": null, "workspace": null, "command": null}
```

`ValueError` 回應 `422`，其他例外回應 `500`。

### Raspberry Pi ROS 控制

AGX 不直接呼叫 ROS，也不直接控制機械手臂。Raspberry Pi 收到 AGX 回傳的 `command` 後，負責呼叫自己的 ROS 節點。

Raspberry Pi 端可以依照自己的 ROS service/action/topic 設計轉換 `command`。AGX 只保證回傳 JSON 控制指令，不假設 Raspberry Pi 內部 ROS 實作。

### Raspberry Pi `POST /trigger`

目前 Raspberry Pi 端提供測試用觸發 endpoint。ESP32 的實際觸發方式還不確定，因此此 endpoint 先作為本機測試與整合測試入口。

成功流程：

```text
POST /trigger
  -> camera.capture_image()
  -> agx_client.detect()
  -> ros_control.execute_command()
  -> 回傳 AGX 結果與 ROS 執行狀態
```

成功回應 `200`：

```json
{
  "status": "done",
  "agx": {
    "label": "plastic",
    "bin": "bin_c",
    "command": {
      "action": "pick_and_place",
      "target_bin": "bin_c",
      "pick": {
        "x": 0.23,
        "y": -0.08,
        "z": 0.02
      }
    }
  },
  "ros": {
    "executed": true,
    "mode": "mock",
    "motion_plan": [
      {"step": "move_above_pick", "x": 0.23, "y": -0.08, "z": 0.12},
      {"step": "move_to_pick", "x": 0.23, "y": -0.08, "z": 0.02},
      {"step": "close_gripper"},
      {"step": "lift", "x": 0.23, "y": -0.08, "z": 0.12},
      {"step": "move_above_bin", "target_bin": "bin_c", "x": 0.32, "y": 0.18, "z": 0.12},
      {"step": "move_to_bin", "target_bin": "bin_c", "x": 0.32, "y": 0.18, "z": 0.05},
      {"step": "open_gripper"},
      {"step": "return_home", "x": 0.0, "y": 0.0, "z": 0.15}
    ]
  }
}
```

Raspberry Pi mock 模式不會呼叫真實 ROS，但會先驗證 `command`，再產生 `motion_plan`。接硬體後，Raspberry Pi / ROS 端應把這些 motion steps 轉成實際 ROS service、topic 或 action。

## AGX 任務控制設計

AGX `POST /detect` 內部流程：

```text
接收圖片
  -> YOLOv8 推論
  -> 選擇最高信心值偵測結果
  -> 輸出 label、bbox、confidence、center
  -> 將影像中心座標轉換成工作區座標
  -> 依照 label 對應 bin
  -> 產生 pick_and_place 控制指令
  -> 回傳 JSON 給 Raspberry Pi
```

AGX 建議模組：

```text
agx/
├── server.py        # Flask API、錯誤回應
├── yolo_infer.py    # YOLO 模型載入與推論
├── task_control.py  # 工作區座標計算、控制指令產生
├── config.example.py
├── requirements.txt
├── smoke_test.py
├── README.md
└── models/
    └── .gitkeep
```

`task_control.py` 不控制硬體，只產生 Raspberry Pi 可使用的 JSON 指令。

## AGX 設定

倉庫只保留 `agx/config.example.py`。本機執行時，請複製成不提交的 `agx/config.py`。

必要設定：

```python
YOLO_MODEL_PATH = "../datasets/best.pt"
YOLO_CONF = 0.5
YOLO_DEVICE = "cuda"
YOLO_INFER_MODE = "yolo"

FLASK_PORT = 8000

CLASS_NAMES = ["tissue", "foil_pack", "plastic"]

BIN_MAP = {
    "tissue": "bin_a",
    "foil_pack": "bin_b",
    "plastic": "bin_c",
}

MESSAGE_MAP = {
    "tissue": "已產生衛生紙分類控制指令",
    "foil_pack": "已產生鋁箔包分類控制指令",
    "plastic": "已產生塑膠分類控制指令",
}

WORKSPACE_Z = 0.02

IMAGE_TO_WORKSPACE = {
    "scale_x": 0.001,
    "scale_y": 0.001,
    "offset_x": 0.0,
    "offset_y": 0.0,
}
```

目前已訓練模型放在 `datasets/best.pt`，訓練 notebook 放在 `datasets/yolo_training.ipynb`。AGX 從 `agx/` 目錄啟動時，`YOLO_MODEL_PATH = "../datasets/best.pt"` 會直接指向這個權重檔。

沒有 YOLO 模型或 GPU 時，才改用：

```python
YOLO_INFER_MODE = "mock"
```

使用已訓練模型時使用：

```python
YOLO_INFER_MODE = "yolo"
```

如果 AGX 上沒有 CUDA，可先把 `YOLO_DEVICE` 改成 `"cpu"` 測試。

## 無設備開發流程

目前沒有 AGX、Raspberry Pi、Camera、ROS 或機械手臂時，可以先用兩個 mock 流程開發：

```text
AGX mock
  -> 驗證 /ping 與 /detect API 合約

Raspberry Pi mock
  -> mock camera.capture_image()
  -> 或 CAMERA_MODE=file 讀本機圖片
  -> mock agx_client.detect()
  -> validate command
  -> build motion_plan
  -> mock ros_control.execute_command()
  -> 驗證 /trigger 流程
```

AGX smoke test：

```bash
cd agx
python smoke_test.py
```

Raspberry Pi smoke test：

```bash
cd raspberry-pi
python smoke_test.py
```

## 模組啟動

各模組的安裝與執行方式放在模組自己的 README：

- [AGX 啟動方式](agx/README.md)
- [Raspberry Pi 啟動方式](raspberry-pi/README.md)

## 開發注意事項

- 專案維持三個硬體/系統模組：`esp32/`、`raspberry-pi/`、`agx/`。
- 除非專題範圍改變，不要重新加入舊的 web/backend/worker 架構。
- 不要提交真實 API key、WiFi 密碼、本機設定檔、YOLO 權重或原始資料集。
- 不要提交 `agx/config.py`、`esp32/config.h`、`raspberry-pi/config.py`、YOLO 權重或原始資料集。
- AGX 只回傳控制指令；Raspberry Pi / ROS 端如何執行指令，由 Raspberry Pi 組員實作。
- Raspberry Pi 目前用 mock camera 和 mock ROS；接硬體時只替換 `camera.py` 與 `ros_control.py` 的實作。
- 原始標註資料放在 `datasets/raw/`，並由 git 忽略。
