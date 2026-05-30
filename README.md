# ESP32 + ArmPi 智慧垃圾分類系統

本專題使用 ESP32 觸發任務，Raspberry Pi 拍照並呼叫 ROS 節點控制機械手臂，AI Server 執行 YOLOv8 影像辨識與任務控制指令產生，完成垃圾分類展示流程。

AI Server 預設放在 `agx/` 目錄，實際執行硬體可以是 NVIDIA AGX 或一般 PC。若尚未取得 AGX、YOLO 模型、Camera 或機械手臂，可先使用 mock 模式完成 API 與流程整合。

目前專案採用三個模組分工，避免過度拆層：

```text
ESP32 觸發任務
  -> Raspberry Pi 拍照
  -> Raspberry Pi 將圖片上傳到 AI Server /detect
  -> AI Server 執行 YOLOv8 推論
  -> AI Server 取得類別、邊界框、信心值、中心座標
  -> AI Server 任務控制模組計算工作區座標
  -> AI Server 任務控制模組產生控制指令
  -> AI Server 將控制指令回傳給 Raspberry Pi
  -> Raspberry Pi 呼叫 ROS 節點控制機械手臂
  -> Raspberry Pi 回到等待下一張影像
```

## 專案結構

```text
.
├── README.md
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
    └── raw/
```

## 模組分工

| 模組 | 硬體 | 職責 | 狀態 |
| --- | --- | --- | --- |
| `esp32/` | ESP32、按鈕、麥克風或喇叭 | 觸發系統開始任務，細節由 ESP32 組員決定 | 尚未實作 |
| `raspberry-pi/` | Raspberry Pi、Camera、ROS、機械手臂 | 拍照、呼叫 AI Server `/detect`、接收控制指令、呼叫 ROS 節點控制機械手臂 | Mock MVP 已實作 |
| `agx/` | NVIDIA AGX 或一般 PC | Flask API、YOLO 推論、座標轉換、任務控制指令產生 | Mock / YOLO 模式已支援 |
| `datasets/` | 本機資料夾 | 訓練與標註資料 | 本機使用 |

## AI 工具入口

不同 AI coding 工具請先閱讀以下檔案，避免讀到不同版本的規格：

| 工具 | 入口檔 |
| --- | --- |
| Codex | `AGENTS.md` |
| Claude | `CLAUDE.md` |
| OpenCode | `AGENTS.md` |

專案規格以 `README.md` 為主，AI 開發規則以 `AGENTS.md` 為主。`CLAUDE.md` 只作為入口提示，不另外維護一份規格。

## 模組邊界

- ESP32 只負責觸發系統，AI Server 不假設 ESP32 的實作方式。
- Raspberry Pi 負責拍照、上傳圖片、接收 AI Server 控制指令，以及呼叫 ROS 節點控制機械手臂。
- AI Server 負責 YOLO 推論、整理偵測結果、計算工作區座標、產生控制指令。
- AI Server 不直接控制 ROS，也不直接操作機械手臂。
- 模組之間使用 HTTP API 溝通，不共用本機程式碼。

## 支援分類

| 垃圾 | Label | Bin | 回傳訊息 |
| --- | --- | --- | --- |
| 衛生紙 | `tissue` | `bin_a` | `已產生衛生紙分類控制指令` |
| 鋁箔包 | `foil_pack` | `bin_b` | `已產生鋁箔包分類控制指令` |
| 塑膠瓶 | `plastic_bottle` | `bin_c` | `已產生塑膠瓶分類控制指令` |

## API 合約

### AI Server `GET /ping`

成功回應 `200`：

```json
{"status": "ok", "yolo": "loaded"}
```

### AI Server `POST /detect`

請求格式為 `multipart/form-data`：

| Key | Value |
| --- | --- |
| `image` | jpg 或 png 圖片 |

成功回應 `200`：

```json
{
  "label": "plastic_bottle",
  "bin": "bin_c",
  "message": "已產生塑膠瓶分類控制指令",
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

AI Server 不直接呼叫 ROS，也不直接控制機械手臂。Raspberry Pi 收到 AI Server 回傳的 `command` 後，負責呼叫自己的 ROS 節點。

Raspberry Pi 端可以依照自己的 ROS service/action/topic 設計轉換 `command`。AI Server 只保證回傳 JSON 控制指令，不假設 Raspberry Pi 內部 ROS 實作。

### Raspberry Pi `POST /trigger`

目前 Raspberry Pi 端提供測試用觸發 endpoint。ESP32 的實際觸發方式還不確定，因此此 endpoint 先作為本機測試與整合測試入口。

成功流程：

```text
POST /trigger
  -> camera.capture_image()
  -> agx_client.detect()
  -> ros_control.execute_command()
  -> 回傳 AI Server 結果與 ROS 執行狀態
```

成功回應 `200`：

```json
{
  "status": "done",
  "agx": {
    "label": "plastic_bottle",
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

## AI Server 任務控制設計

AI Server `POST /detect` 內部流程：

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

AI Server 建議模組：

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

## AI Server 設定

倉庫只保留 `agx/config.example.py`。本機執行時，請複製成不提交的 `agx/config.py`。

必要設定：

```python
YOLO_MODEL_PATH = "models/best.pt"
YOLO_CONF = 0.5
YOLO_DEVICE = "cuda"
YOLO_INFER_MODE = "mock"

FLASK_PORT = 8000

CLASS_NAMES = ["tissue", "foil_pack", "plastic_bottle"]

BIN_MAP = {
    "tissue": "bin_a",
    "foil_pack": "bin_b",
    "plastic_bottle": "bin_c",
}

MESSAGE_MAP = {
    "tissue": "已產生衛生紙分類控制指令",
    "foil_pack": "已產生鋁箔包分類控制指令",
    "plastic_bottle": "已產生塑膠瓶分類控制指令",
}

WORKSPACE_Z = 0.02

IMAGE_TO_WORKSPACE = {
    "scale_x": 0.001,
    "scale_y": 0.001,
    "offset_x": 0.0,
    "offset_y": 0.0,
}
```

沒有 YOLO 模型或 GPU 時，先使用：

```python
YOLO_INFER_MODE = "mock"
```

準備好模型後再切換成：

```python
YOLO_INFER_MODE = "yolo"
```

## 無設備開發流程

目前沒有 AGX、Raspberry Pi、Camera、ROS 或機械手臂時，可以先用兩個 mock 流程開發：

```text
AI Server mock
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

AI Server smoke test：

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

- [AI Server 啟動方式](agx/README.md)
- [Raspberry Pi 啟動方式](raspberry-pi/README.md)

## 開發注意事項

- 專案維持三個硬體/系統模組：`esp32/`、`raspberry-pi/`、`agx/`。
- 除非專題範圍改變，不要重新加入舊的 web/backend/worker 架構。
- 不要提交真實 API key、WiFi 密碼、本機設定檔、YOLO 權重或原始資料集。
- 不要提交 `agx/config.py`、`esp32/config.h`、`raspberry-pi/config.py`、`agx/models/best.pt`。
- AI Server 只回傳控制指令；Raspberry Pi / ROS 端如何執行指令，由 Raspberry Pi 組員實作。
- Raspberry Pi 目前用 mock camera 和 mock ROS；接硬體時只替換 `camera.py` 與 `ros_control.py` 的實作。
- 原始標註資料放在 `datasets/raw/`，並由 git 忽略。
