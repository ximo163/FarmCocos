這個倉庫是把 Flash 種地遊戲重寫成 Cocos 客戶端加 Node 服務端。拆分時遵守：

- 依賴順序：規格（`pipeline:spec`，從 legacy 提取到 spec/）→ core 邏輯 → 服務端 → 客戶端腳本。後面的子 issue 用「依赖 #N」寫明依賴前面的。
- 每個子 issue 寫明對應的 legacy 文件（`legacy/deploy/...` 裡的 PHP 和 xml、`legacy/decompiled/...`；位置見 `legacy/manifest.json`）和 spec 文件，寫明怎麼算做完。
- 標籤：從 legacy 提取規格的用 `pipeline:spec`；腳手架、依賴、構建配置的用 `pipeline:chore`；能先寫失敗測試的邏輯不打 pipeline 標籤（走默認流水線）。
- 按遊戲系統拆（作物生長、地塊、背包、商店、經驗等級、好友、時間軸播放器……），不要按文件拆。
- 整個項目無人值守，不要安排需要人動手的步驟。界面由代碼按佈局數據生成，不用 prefab 和場景；客戶端在 GitHub 上構建。
- 需要改 `harness/`、`.github/`、`scripts/`、`checks/`、`.orchestrator/` 的工作 agent 做不了（受保護）：不拆進計劃，在最後單獨列出來說明需要什麼。
