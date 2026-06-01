# Agent 開發規則

本檔案是 AI coding 工具的主要開發規則。專案規格以 `README.md` 為準；本檔案只補充 AI 實作時必須遵守的限制。

預設實作範圍是 AGX 模組與 Raspberry Pi mock 流程。AGX 模組放在 `agx/` 目錄；即使暫時使用一般電腦執行，也一律視為 AGX。除非使用者明確要求，否則不要實作 ESP32 端或真實 ROS / ArmPi 硬體控制。

目前專題版本：ESP32 觸發系統 + Raspberry Pi 拍照與 ROS 控制機械手臂 + AGX YOLO 推論與控制指令產生。沒有設備時，先用 mock camera、mock AGX result、mock ROS 跑通流程。

## 專案結構

```text
.
├── README.md
├── AGENTS.md
├── CLAUDE.md
├── agx/
├── esp32/
├── raspberry-pi/
└── datasets/
```

## 模組邊界

- ESP32 只負責觸發系統；目前不假設 ESP32 的實作細節。
- Raspberry Pi 負責拍照、上傳圖片、接收 AGX 控制指令，以及呼叫 ROS 節點控制機械手臂。
- AGX 負責 YOLO 推論、bbox/center 輸出、工作區座標計算、分類/bin 決策，以及控制指令產生。
- AGX 不直接控制 ROS，也不直接操作機械手臂。
- 模組之間使用 HTTP API 溝通，不共用本機程式碼。

## AGX 合約

支援 label：

- `metal`
- `plastic`
- `paper`

bin 對應：

- `metal` -> `bin_a`
- `plastic` -> `bin_b`
- `paper` -> `bin_c`

AGX 檔案結構：

```text
agx/
├── server.py
├── yolo_infer.py
├── task_control.py
├── config.example.py
├── requirements.txt
├── smoke_test.py
├── README.md
└── models/
    └── .gitkeep
```

AGX endpoints：

- `GET /ping`
- `POST /detect`

AGX `POST /detect` 應回傳：

- `label`
- `bin`
- `message`
- `confidence`
- `detection.bbox`
- `detection.center`
- `workspace`
- `command`

Raspberry Pi 收到 `command` 後，才呼叫自己的 ROS 節點或設定檔指定的本機腳本控制機械手臂。

## Raspberry Pi mock 合約

目前沒有硬體時，Raspberry Pi 端可以先實作與維護 mock 流程：

- `camera.py` 支援 `CAMERA_MODE = "mock"` 產生 mock 圖片，以及 `CAMERA_MODE = "file"` 讀取本機圖片；這兩者都不是實際 Camera 硬體整合。
- `agx_client.py` 支援 `AGX_MODE = "mock"` 與 `AGX_MODE = "http"`。
- `ros_control.py` 預設驗證 command、產生 motion plan、mock 執行控制指令，不呼叫真實 ROS。
- `server.py` 提供 `GET /ping` 與 `POST /trigger`。
- `smoke_test.py` 應可在沒有 Camera、ROS、AGX 服務的情況下通過。

## 規則

- 實作前先閱讀 `README.md`。
- 不要在 `CLAUDE.md` 維護另一份規格；規格只放 `README.md`，AI 規則只放 `AGENTS.md`。
- 預設只修改 `agx/`、`raspberry-pi/` mock 流程，或使用者明確要求的根目錄支援檔案。
- 除非使用者明確要求，不要修改 `esp32/` 或真實 ROS / ArmPi 硬體控制實作。
- 不要建立 `agx/models/best.pt`。
- 不要建立 `agx/config.py`。
- 不要建立 `raspberry-pi/config.py`。
- 不要建立真實 secret 檔案或真實 API key。
- AGX 設定範例只放在 `agx/config.example.py`。
- Raspberry Pi 設定範例只放在 `raspberry-pi/config.example.py`。
- AGX 與 Raspberry Pi 所有可設定值都必須從各自的 `config.py` 讀取。
- 嚴格遵守 `README.md` 裡的 API 合約。
- 目前 class labels 是 `metal`、`plastic`、`paper`。
- `ValueError` 回傳 HTTP 422。
- 其他例外回傳 HTTP 500。
- AGX 不要主動呼叫 Raspberry Pi `/move`。
- AGX 只產生控制指令並回傳給 Raspberry Pi。
- Raspberry Pi mock 模式可以驗證流程，但不得假裝已完成真實 Camera、ROS 或機械手臂整合；若使用 `ROS_MODE = "script"`，只能執行設定檔明確指定的本機腳本。
- `smoke_test.py` 只作為開發驗證入口，不是 runtime 流程；正式執行入口仍是各模組的 `server.py` 或 `run_once.py`。
