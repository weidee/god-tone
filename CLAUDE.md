# Claude 開發入口

請先閱讀：

1. `README.md`：專案規格、系統流程、API 合約。
2. `AGENTS.md`：AI 開發規則、模組邊界、禁止事項。

不要在本檔案維護另一份規格。若規格需要更新，請更新 `README.md`；若 AI 開發規則需要更新，請更新 `AGENTS.md`。

目前預設實作範圍是 `agx/` AGX 模組與 `raspberry-pi/` mock / file / HTTP 流程。即使暫時使用一般電腦執行，也一律視為 AGX。除非使用者明確要求，否則不要修改 `esp32/`，也不要實作真實 ROS / ArmPi 硬體控制。
