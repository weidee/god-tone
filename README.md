# Smart Trash Sorting System

智慧垃圾分類系統是一個期末專題型的 IoT + AI 專案。系統由 ESP32、Raspberry Pi、NVIDIA AGX 三個模組組成，透過 HTTP 在同一個區域網路內互相通訊，完成語音指令分類或影像自動辨識，最後控制機械手臂將垃圾放入對應桶位。

目前此 repository 先完成 AGX Skill Server MVP。ESP32 與 Raspberry Pi 目錄已建立，但尚未實作。

## System Goal

系統支援兩種使用情境：

- 語音路徑：使用者透過 ESP32 說出垃圾種類，AGX 判斷分類並回傳播報文字。
- 影像路徑：Raspberry Pi 拍照送到 AGX，AGX 使用 YOLOv8 偵測物品並決策分類。
- 執行路徑：AGX 將分類結果轉成 bin 指令，送給 Raspberry Pi 控制手臂。

目前支援的垃圾類別：

| 物品 | Label | Bin |
| --- | --- | --- |
| 衛生紙 | `tissue` | `bin_a` |
| 紙盒 | `paper_box` | `bin_b` |
| 塑膠罐 | `plastic_can` | `bin_c` |

## Module Responsibilities

| 模組 | 主要硬體 | 負責人 | 核心職責 | 狀態 |
| --- | --- | --- | --- | --- |
| ESP32 voice module | ESP32、麥克風、喇叭 | 隊友 A | 喚醒詞、錄音、STT、呼叫 AGX `/classify`、播放 AGX 回傳訊息 | 目錄已建立，尚未實作 |
| Raspberry Pi camera and arm module | Raspberry Pi、Camera、伺服馬達 | 隊友 B | 拍照、呼叫 AGX `/detect`、接收 AGX `/move` 指令、控制手臂 | 目錄已建立，尚未實作 |
| AGX Skill Server module | NVIDIA AGX | 韋傑 | Flask API、YOLOv8 推論、OpenAI Skill flow、分類決策、發送 `/move` 指令 | MVP 已實作 |

## Detailed Work Breakdown

### ESP32 Voice Module

ESP32 負責使用者互動，不做分類決策。

主要工作：

- 偵測喚醒詞或按鍵觸發錄音。
- 使用麥克風擷取語音。
- 將語音轉成文字，或串接 STT API 取得文字。
- 呼叫 AGX `POST /classify`，送出 `{"text": "這是紙盒"}`。
- 讀取 AGX 回傳的 `message` 欄位並用喇叭播放。
- 管理 WiFi、AGX IP、API key 等本機設定。

交付內容：

- `esp32/main.ino`
- `esp32/wake_word.ino`
- `esp32/stt.ino`
- `esp32/http_client.ino`
- `esp32/tts.ino`
- `esp32/config.h`，此檔不可提交真實密鑰

### Raspberry Pi Camera And Arm Module

Raspberry Pi 負責影像來源與實體動作，不做 AI 決策。

主要工作：

- 定期或按需拍照。
- 將 jpg/png 圖片用 multipart form-data 呼叫 AGX `POST /detect`。
- 提供 `POST /move` endpoint，接收 AGX 傳來的 `{"bin": "bin_b"}`。
- 將 `bin_a`、`bin_b`、`bin_c` 對應到實際伺服馬達角度。
- 控制手臂或分流機構移動到指定桶位。
- 在 AGX 無回應時記錄錯誤並繼續下一輪拍照。

交付內容：

- `raspberry-pi/server.py`
- `raspberry-pi/camera.py`
- `raspberry-pi/arm_control.py`
- `raspberry-pi/config.example.py`
- `raspberry-pi/requirements.txt`

### AGX Skill Server Module

AGX 是目前已實作的 AI 決策核心。

主要工作：

- 提供 Flask server。
- 接收 ESP32 的 `POST /classify` JSON 文字請求。
- 接收 Raspberry Pi 的 `POST /detect` 圖片請求。
- 載入 YOLOv8 模型並做物件偵測。
- 透過 OpenAI Skill flow 將語音或影像結果確認成最終 label。
- 將 label 對應成 bin 與中文訊息。
- 呼叫 Raspberry Pi `POST /move` 發送手臂動作指令。
- 回傳統一 JSON 給呼叫方。

交付內容：

- `agx/server.py`
- `agx/skill.py`
- `agx/yolo_infer.py`
- `agx/config.example.py`
- `agx/requirements.txt`
- `agx/README.md`
- `agx/models/.gitkeep`

## System Flow

### Voice Flow

```text
User voice
  -> ESP32 records audio
  -> ESP32 gets text from STT
  -> ESP32 POST /classify to AGX
  -> AGX asks LLM for final class
  -> AGX POST /move to Raspberry Pi
  -> Raspberry Pi moves arm
  -> AGX returns message to ESP32
  -> ESP32 speaks message
```

### Vision Flow

```text
Raspberry Pi camera captures image
  -> Raspberry Pi POST /detect to AGX
  -> AGX runs YOLOv8 inference
  -> AGX asks LLM to confirm final class
  -> AGX POST /move to Raspberry Pi
  -> Raspberry Pi moves arm
  -> AGX returns detection result
```

## API Contract

### AGX Endpoints

| Endpoint | Method | Caller | Purpose |
| --- | --- | --- | --- |
| `/ping` | GET | Any module | Health check |
| `/classify` | POST | ESP32 | Classify voice text |
| `/detect` | POST | Raspberry Pi | Detect trash from image |

Example `POST /classify` request:

```json
{"text": "這是紙盒"}
```

Example AGX response:

```json
{
  "bin": "bin_b",
  "label": "paper_box",
  "message": "已將紙盒放入紙類回收桶",
  "confidence": null
}
```

### Raspberry Pi Endpoint

| Endpoint | Method | Caller | Purpose |
| --- | --- | --- | --- |
| `/move` | POST | AGX | Move arm to target bin |

Example `POST /move` request:

```json
{"bin": "bin_b"}
```

## Repository Structure

```text
.
├── AGENTS.md
├── README.md
├── docs/
│   ├── agx_spec.md
│   └── system_overview.md
├── agx/
│   ├── server.py
│   ├── skill.py
│   ├── yolo_infer.py
│   ├── config.example.py
│   ├── requirements.txt
│   ├── README.md
│   └── models/
│       └── .gitkeep
├── esp32/
│   └── .gitkeep
└── raspberry-pi/
    └── .gitkeep
```

## Development Notes

- Do not commit real API keys or local config files.
- Do not commit `agx/config.py`.
- Do not commit `esp32/config.h` if it contains WiFi credentials or API keys.
- Do not commit `raspberry-pi/config.py`.
- Do not commit YOLO model artifacts such as `agx/models/best.pt`.
- Keep module boundaries clear: ESP32 handles voice, Raspberry Pi handles camera/arm, AGX handles AI decision logic.

## AGX Quick Start

```bash
cd agx
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config.example.py config.py
```

Edit `agx/config.py`, then manually place the YOLO model at:

```text
agx/models/best.pt
```

Run AGX server:

```bash
python server.py
```

Test health check:

```bash
curl http://localhost:8000/ping
```
