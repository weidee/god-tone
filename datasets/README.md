# 資料集

這個資料夾用來放本機訓練資料、訓練 notebook 與訓練好的 YOLO 權重。

建議結構：

```text
datasets/
├── README.md
├── yolo_training.ipynb
├── best.pt
├── raw/
│   ├── metal/
│   ├── plastic/
│   └── paper/
└── processed/
```

目前專題分類固定為三類：

| 類別 | Label | Bin |
| --- | --- | --- |
| 金屬 | `metal` | `bin_a` |
| 塑膠 | `plastic` | `bin_b` |
| 紙類 | `paper` | `bin_c` |

`yolo_training.ipynb` 是訓練 notebook；`best.pt` 是訓練完成後給 AGX 推論使用的權重。AGX 範例設定使用 `YOLO_MODEL_PATH = "../datasets/best.pt"`，所以從 `agx/` 目錄啟動 server 時不用再複製模型到 `agx/models/`。

`raw/` 和 `processed/` 會被 git 忽略，避免把大量圖片資料提交到版本控制。YOLO 權重通常也不要提交到版本控制；交作業或搬到 AGX 時再用檔案傳輸方式放到相同路徑。
