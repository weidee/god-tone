ESP32 音箱 設計規格書 v1.0

智慧垃圾分類系統 — ESP32 模組

負責人：隊友 A

1. 模組職責

ESP32 是系統的語音控制端，做且只做三件事：

偵測喚醒詞，開始錄音

把錄音送去 STT 轉成文字

把文字 POST 給 AGX，等回應後播出語音

2. 目錄結構


esp32/

├── main.ino           # 主程式，串接各模組

├── wake_word.ino      # 喚醒詞偵測

├── stt.ino            # 語音轉文字（呼叫 Whisper API）

├── http_client.ino    # HTTP POST 給 AGX

├── tts.ino            # 播放回應語音

└── config.h           # AGX IP、API key、port 設定


3. 硬體需求

| 元件 | 規格 |

|------|------|

| 主控 | ESP32（含 WiFi） |

| 麥克風 | I2S 數位麥克風（INMP441 或同類） |

| 喇叭 | 3W 喇叭 + PAM8403 擴大板 |

| 連線 | WiFi，與 AGX 在同一區網 |

4. 流程


開機 → 連 WiFi → 等待喚醒詞

→ 偵測到喚醒詞 → 開始錄音（3 秒）

→ 錄音結束 → POST 音訊給 Whisper API → 取得文字

→ POST {"text": "<文字>"} 給 AGX /classify

→ 收到回應 {"message": "..."} → TTS 播出

→ 回到等待喚醒詞


5. API 介面

送出（ESP32 → AGX）


POST http://<AGX_IP>:8000/classify

Content-Type: application/json

{"text": "這是紙盒"}


收到（AGX → ESP32）


{

  "bin": "bin_b",

  "label": "paper_box",

  "message": "已將紙盒放入紙類回收桶",

  "confidence": null

}


ESP32 只需要讀 message 欄位播出即可，其他欄位忽略。

6. config.h 內容


#define AGX_IP       "192.168.x.x"

#define AGX_PORT     8000

#define WIFI_SSID    "your_ssid"

#define WIFI_PASS    "your_password"

#define WHISPER_KEY  "sk-..."


7. 注意事項

喚醒詞建議用離線方案（ESP-SR 或 Porcupine），不要靠網路

STT 用 OpenAI Whisper API，錄音格式 WAV 16kHz mono

POST 給 AGX 前先確認 WiFi 已連線

AGX 沒回應時（timeout 5 秒）播出「連線失敗，請再試一次」

所有 IP 與 key 集中在 config.h，不要散落在各 .ino 檔

樹莓派 設計規格書 v1.0

智慧垃圾分類系統 — 樹莓派模組

負責人：隊友 B

1. 模組職責

樹莓派是系統的執行端，做且只做兩件事：

定期拍照，POST 圖片給 AGX 做辨識

收到 AGX 的動作指令後，驅動伺服馬達把手臂轉到對應位置

2. 目錄結構


raspberry-pi/

├── server.py          # Flask server，接收 AGX 的 /move 指令

├── camera.py          # 拍照並 POST 圖片給 AGX /detect

├── arm_control.py     # GPIO PWM 控制伺服馬達

├── config.py          # AGX IP、port、馬達 GPIO 腳位設定

├── config.example.py  # 設定範本（上傳 GitHub）

└── requirements.txt   # Python 套件清單


3. 硬體需求

| 元件 | 規格 |

|------|------|

| 主控 | Raspberry Pi 4（建議）或 3B+ |

| 相機 | Pi Camera Module v2 或 USB webcam |

| 手臂 | 伺服馬達 × N（依手臂機構決定數量） |

| 連線 | WiFi 或有線，與 AGX 在同一區網 |

4. 流程

拍照流程（camera.py，獨立背景執行）


每 2 秒拍一張照

→ POST multipart image 給 AGX /detect

→ 收到回應（若 bin 為 null 就忽略）

→ 繼續等下一輪


執行流程（server.py）


開機 → 啟動 Flask server 監聽 port 5000

→ 收到 POST /move {"bin": "bin_b"}

→ 呼叫 arm_control.move_to(bin)

→ 馬達轉到對應角度

→ 回傳 {"status": "done"}


5. API 介面

接收（AGX → 樹莓派）


POST http://<RPI_IP>:5000/move

Content-Type: application/json

{"bin": "bin_b"}


回傳（樹莓派 → AGX）


{"status": "done", "bin": "bin_b"}


送出（樹莓派 → AGX）


POST http://<AGX_IP>:8000/detect

Content-Type: multipart/form-data

image: <圖片 bytes，jpg 格式>


6. 馬達角度對應表

實際角度依手臂機構自行量測後填入 config.py。

| bin 值 | 物品 | 預設角度 |

|--------|------|---------|

| bin_a | 衛生紙 | 0° |

| bin_b | 紙盒 | 90° |

| bin_c | 塑膠罐 | 180° |

7. config.example.py 內容


AGX_URL = "http://192.168.x.x:8000"   # AGX IP，結尾不加斜線

FLASK_PORT = 5000

CAMERA_INTERVAL = 2                    # 拍照間隔（秒）

# 伺服馬達 GPIO 腳位（BCM 編號）

SERVO_PIN = 18

# bin 值對應馬達角度（依實體手臂調整）

BIN_ANGLES = {

    "bin_a": 0,

    "bin_b": 90,

    "bin_c": 180,

}


8. requirements.txt


flask>=3.0

requests>=2.31

picamera2>=0.3

RPi.GPIO>=0.7

Pillow>=10.0


9. 注意事項

camera.py 與 server.py 需同時執行，建議用兩個 terminal 或 systemd

拍照間隔 2 秒，避免對 AGX 送太多請求

馬達動作完成後延遲 1 秒再回傳 done，讓手臂有時間到位

AGX 沒回應時（timeout 5 秒）印出 log，不中斷程式

GPIO 腳位若與手臂機構不同，只改 config.py 的 SERVO_PIN，不動 arm_control.py

智慧垃圾分類系統 總覽規格書 v1.0

Smart Trash Sorting System

專案：CGU 期末專題

1. 系統簡介

本系統由三個模組組成，透過 HTTP 互相溝通，完成「語音指令」或「自動影像辨識」兩種方式的垃圾分類，並驅動機械手臂將垃圾放入對應回收桶。

模組分工總覽

| 模組 | 硬體 | 職責 | 負責人 |

|------|------|------|--------|

| ESP32 音箱 | ESP32 + 麥克風 + 喇叭 | 語音輸入輸出 | 隊友 A |

| AGX Skill Server | NVIDIA AGX | YOLOv8 推論 + AI 決策 | 韋傑 |

| 樹莓派手臂 | Raspberry Pi + Camera + 伺服馬達 | 拍照 + 手臂執行 | 隊友 B |

2. 系統架構


┌─────────────┐        POST /classify         ┌─────────────────────┐

│   ESP32     │ ─────────────────────────────▶ │                     │

│   音箱      │ ◀─────────────────────────────  │   AGX               │

│             │        回傳 message             │   Skill Server      │

└─────────────┘                                │                     │

                                               │  ┌───────────────┐  │

┌─────────────┐        POST /detect            │  │  Skill 流程   │  │

│   樹莓派    │ ─────────────────────────────▶ │  │  (LLM 決策)   │  │

│   手臂      │                                │  └───────────────┘  │

│             │ ◀─────────────────────────────  │  ┌───────────────┐  │

│             │        POST /move              │  │  YOLOv8       │  │

└─────────────┘                                │  │  (物體辨識)   │  │

                                               │  └───────────────┘  │

                                               └─────────────────────┘


3. 通訊協定

全系統統一使用 HTTP，所有模組在同一個區域網路內。不使用 MQTT，不需要 Broker。

| 方向 | 協定 | 說明 |

|------|------|------|

| ESP32 → AGX | HTTP POST JSON | 語音文字 |

| 樹莓派 → AGX | HTTP POST multipart | 圖片 |

| AGX → 樹莓派 | HTTP POST JSON | 動作指令 |

| AGX → ESP32 | HTTP 回應 JSON | TTS 文字 |

| 樹莓派 GPIO | PWM | 控制伺服馬達 |

4. 完整 API 清單

AGX 對外提供的 endpoint

| Endpoint | Method | 呼叫方 | 說明 |

|----------|--------|--------|------|

| /classify | POST | ESP32 | 接收語音文字，觸發 Skill 流程 |

| /detect | POST | 樹莓派 | 接收圖片，觸發 YOLOv8 + Skill 流程 |

| /ping | GET | 任何人 | 健康檢查 |

樹莓派對外提供的 endpoint

| Endpoint | Method | 呼叫方 | 說明 |

|----------|--------|--------|------|

| /move | POST | AGX | 接收 bin 值，控制手臂 |

5. 資料格式

語音觸發流程（路徑 A）


① ESP32 → AGX

POST /classify

{"text": "這是紙盒"}

② AGX → 樹莓派

POST /move

{"bin": "bin_b"}

③ 樹莓派 → AGX

{"status": "done", "bin": "bin_b"}

④ AGX → ESP32

{"bin": "bin_b", "label": "paper_box", "message": "已將紙盒放入紙類回收桶", "confidence": null}


圖片觸發流程（路徑 B）


① 樹莓派 → AGX

POST /detect

multipart/form-data，key=image

② AGX → 樹莓派

POST /move

{"bin": "bin_c"}

③ 樹莓派 → AGX

{"status": "done", "bin": "bin_c"}

④ AGX → 樹莓派（原本 /detect 的回應）

{"bin": "bin_c", "label": "plastic_can", "message": "偵測到塑膠罐", "confidence": 0.91}


6. 垃圾類別與 bin 值定義

三個模組都必須使用相同的 bin 值，不能各自定義。

| 物品 | label | bin 值 | 馬達角度（預設） |

|------|-------|--------|----------------|

| 衛生紙 | tissue | bin_a | 0° |

| 紙盒 | paper_box | bin_b | 90° |

| 塑膠罐 | plastic_can | bin_c | 180° |

7. Repo 結構


smart-trash/                    ← GitHub monorepo 根目錄

├── README.md                   ← 系統總覽說明

├── .gitignore                  ← 統一的忽略規則

├── esp32/

│   ├── main.ino

│   ├── wake_word.ino

│   ├── stt.ino

│   ├── http_client.ino

│   ├── tts.ino

│   └── config.h

├── agx/

│   ├── server.py

│   ├── skill.py

│   ├── yolo_infer.py

│   ├── config.example.py

│   ├── requirements.txt

│   ├── README.md

│   └── models/

│       └── .gitkeep

└── raspberry-pi/

    ├── server.py

    ├── camera.py

    ├── arm_control.py

    ├── config.example.py

    └── requirements.txt


.gitignore（根目錄）


# 設定檔（含 API key，不上傳）

agx/config.py

raspberry-pi/config.py

# YOLO 模型（檔案太大）

agx/models/*.pt

# Python 暫存

__pycache__/

*.pyc

.env


8. Branch 策略

| Branch | 用途 |

|--------|------|

| main | 穩定版，只接受 PR merge |

| dev/agx | 韋傑開發中 |

| dev/esp32 | 隊友 A 開發中 |

| dev/rpi | 隊友 B 開發中 |

開發完成後各自發 PR 到 main，互相 review 後 merge。

9. 網路設定

三台設備需在同一個 WiFi 或有線區網。建議固定 IP（設定路由器 DHCP 保留），避免每次重開機 IP 變動。

| 設備 | 建議 IP |

|------|---------|

| AGX Skill Server | 192.168.1.100 |

| 樹莓派 | 192.168.1.101 |

| ESP32 | 動態即可（它是 client） |

10. 開機順序

系統啟動時需按以下順序開機，避免 client 找不到 server：


1. 先啟動 AGX（python server.py）

2. 再啟動樹莓派（python server.py 與 python camera.py）

3. 最後開 ESP32 電源


11. 測試方式

單模組測試（不需要其他硬體）

AGX：


# 測試語音路徑

curl -X POST http://localhost:8000/classify \

  -H "Content-Type: application/json" \

  -d '{"text": "這是紙盒"}'

# 健康檢查

curl http://localhost:8000/ping


樹莓派：


# 測試手臂動作

curl -X POST http://localhost:5000/move \

  -H "Content-Type: application/json" \

  -d '{"bin": "bin_b"}'


整合測試

三台設備全部開機

從 ESP32 說出喚醒詞後說「這是塑膠罐」

預期結果：AGX 決策 bin_c → 樹莓派手臂轉到 180° → ESP32 播出「已將塑膠罐放入塑膠回收桶」

12. 異常處理原則

| 異常狀況 | 處理方式 |

|----------|---------|

| AGX 沒回應（timeout） | ESP32 播「連線失敗，請再試一次」；樹莓派印 log 繼續運行 |

| YOLO 沒偵測到物體 | AGX 回傳 bin=null，樹莓派不動作 |

| LLM 回傳無法辨識的類別 | AGX 回傳 422，ESP32 播「無法辨識，請再試一次」 |

| 樹莓派 /move 沒回應 | AGX 印 log，仍回傳結果給 ESP32 |

| WiFi 斷線 | ESP32 自動重連；樹莓派 camera.py 重試機制 |

