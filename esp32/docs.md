# ESP32 整合說明

這個資料夾是 ESP32 端程式。依照目前專題邊界，ESP32 只負責偵測觸發訊號；Raspberry Pi 才負責拍照、呼叫 AGX `/detect`，以及依 AGX 回傳的 `command` 控制 ROS 或本機腳本。

## 目前程式狀態

- 主要 firmware 在 `firmware/`，使用 PlatformIO 建置。
- 目前程式以本機 TFLite 音訊模型辨識 `on`、`off`、`one`、`two`、`three`、`unknown`、`_background`。
- ESP32 偵測到 `on` 時會從 Serial 印出單獨一行 `ON`。
- ESP32 偵測到 `off` 時會從 Serial 印出單獨一行 `OFF`。
- `one`、`two`、`three` 目前只改 LED 亮度，不作為本專題流程觸發訊號。
- Serial baud rate 是 `115200`。

本專題目前只需要把 `ON` 當成開始分類流程的觸發訊號。後續可由電腦或 Raspberry Pi 的 Serial 讀取程式收到 `ON` 後呼叫 Raspberry Pi `POST /trigger`。

## 不納入版本控制的內容

以下內容屬於訓練、建置、本機環境或暫存資料，已由根目錄 `.gitignore` 排除：

- `model/`：模型訓練 notebook、訓練資料產生工具與 Python 依賴。
- `memory_test/`：開發測試用 sketch 與輸出。
- `firmware/.pio/`：PlatformIO build、libdeps、firmware binary 等產物。
- `.git/`：組員原本專案帶進來的巢狀 git metadata。
- `.vscode/`、`.DS_Store`、`.python-version`：個人開發環境檔案。
- `firmware/src/config.h`：本機 WiFi、token、腳位等設定，可能含 secret，不要提交。

## 保留在 repo 的內容

- `firmware/src/`：ESP32 主程式。
- `firmware/lib/`：音訊輸入、音訊輸出、TFLite Micro、神經網路等程式庫。
- `firmware/data/`：ESP32 播放用 wav 檔。
- `firmware/platformio.ini`：PlatformIO 專案設定。
- `firmware/README.md`：原始 firmware 使用說明。

## 建置與燒錄

在 `esp32/firmware/` 底下執行：

```sh
pio run
pio run -t upload
pio device monitor -b 115200
```

`platformio.ini` 目前的 `upload_port` 和 `monitor_port` 是 `COM10`。如果換電腦或換作業系統，要依實際序列埠調整。

## 與主系統串接方式

建議串接流程：

```text
ESP32 Serial prints "ON"
  -> Serial reader receives ON
  -> call Raspberry Pi POST /trigger
  -> Raspberry Pi captures image
  -> Raspberry Pi calls AGX POST /detect
  -> Raspberry Pi executes returned command
```

ESP32 不直接呼叫 AGX，也不直接控制 ROS 或機械手臂。`OFF` 目前只保留給未來停止、取消或測試用途，還不是主系統 API 合約的一部分。
