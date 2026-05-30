# 資料集

這個資料夾用來放本機訓練資料與標註資料。

建議結構：

```text
datasets/
├── README.md
├── raw/
│   ├── tissue/
│   ├── foil_pack/
│   └── plastic_bottle/
└── processed/
```

`raw/` 和 `processed/` 會被 git 忽略，避免把大量圖片資料提交到版本控制。
