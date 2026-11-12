# FarmCocos：給 agent 的工作規則

這個倉庫把一個 Flash 種地遊戲（原版源碼已丟失，只剩 swf、PHP 後端、xml 和圖片資源）
重寫成 Cocos Creator 客戶端（Android、PC）加 Node 服務端。開發由編排器流水線完成，
你很可能就是其中一個 agent。計劃、設計和文檔不在這裡，在 `ximo163/FarmCocos-docs`；
這個倉庫**不寫任何給人看的文檔**（README、docs/、*.md 都是受保護路徑）。

## 目錄

| 路徑 | 內容 | 誰改 |
|---|---|---|
| `legacy/swf/` | 原版 swf | 人，只讀 |
| `legacy/php/` | 原版 PHP 後端（作物、經驗、交易等規則的權威來源） | 人，只讀 |
| `legacy/xml/`、`legacy/assets/` | 原版配置 xml、png、gif 等資源 | 人，只讀 |
| `legacy/decompiled/<名字>/` | FFDec 從 swf 導出的 ActionScript、逐幀圖、`swf.xml`（時間軸） | 人用 `scripts/legacy/decompile.sh` 生成，只讀 |
| `legacy/traces/` | 錄下的原版行為軌跡（請求和響應、事件序列） | 人，只讀 |
| `spec/` | 從 legacy 提取的規格：協議、作物數據、交互映射 `interaction-map.json`、偏差清單 `deviations.json` | `pipeline:spec` 提取、人審核；其他流水線只讀 |
| `checks/` | 校驗腳本 | 人，只讀 |
| `packages/core/` | 純 TS 遊戲邏輯，客戶端和服務端共用 | agent |
| `server/` | Node 服務端：鑒權、存檔、運行 core、拉取外部數據 | agent |
| `client/` | Cocos Creator 工程（由編輯器創建）；agent 只寫 `client/assets/scripts/` 下的 TS | agent（腳本）、人（場景、prefab、資源導入） |
| `tools/` | 轉換和比對工具（swf.xml → 時間軸 JSON、軌跡回放等） | agent |
| `timelines/` | 時間軸數據（由 tools 生成） | 工具生成 |

## 原版行為就是需求

- 除非 `spec/deviations.json` 裡列出，否則行為必須和原版一致：數值、公式、時序、
  請求和響應、動畫幀上觸發的事件。
- 依據的優先順序：`legacy/traces/`（實際錄下的行為）> `legacy/php/`（服務端規則）>
  `legacy/decompiled/`（客戶端腳本和時間軸）> `legacy/xml/`。互相矛盾時以前者為準，
  並在 PR 說明裡寫出矛盾之處。
- 測試裡的每個期望值都要能指出出處：在測試上方用註釋寫明 legacy 裡的文件和位置
  （如 `// legacy/php/crop.php: harvest() 第 120 行`）。
- 規格裡找不到、legacy 裡也推不出來的行為，不要自己設計：最後一行輸出
  `BLOCKED: <缺什麼規格，在哪個文件遇到>`。

## 架構約定（不要繞過）

1. **core 是純邏輯**（`checks/core-purity.sh` 檢查）：不 import `cc` 或 Node 模塊，不聯網、
   不讀寫存儲，不直接讀時間或隨機數。時間用注入的 `Clock`，隨機數用注入的 `Rng`。
2. **意圖（Intent）**：玩家操作在 core 裡只以意圖出現（`plant`、`useTool`、`harvest`、`inspect`……），
   是可 JSON 序列化的純數據。core 不認識鼠標、觸摸等原始輸入。
3. **輸入適配器**：桌面適配器照搬原版（懸停、右鍵、快捷鍵）；觸屏適配器嚴格按
   `spec/interaction-map.json` 實現。映射表裡沒有的交互，輸出 `BLOCKED`，不要發明。
4. **GameService**：客戶端只通過 `GameService` 和遊戲邏輯交互。
   `LocalGameService` 在本地運行 core，`RemoteGameService` 連接服務端。服務端的計算結果說了算。
5. **生長驅動**：作物狀態只通過 `GrowthDriver` 計算。`PlotState` 至少包含 `stage`、
   `weather`（外部驅動）、`care`（玩家操作驅動）三個獨立維度。默認的 `TimeGrowthDriver` 完全照搬原版規則。
   經驗和等級只來自玩家操作，**不能依賴任何外部行情數據**。
6. **作物和內容用數據配置**：作物定義（`CropDef`）放在數據裡，外觀引用時間軸名，不寫死在代碼中。
7. **存檔帶版本號**，讀舊版本的存檔要能遷移。
8. **時間軸的幀語義**：原版按固定幀率推進。播放器用固定步長累加器
   （`acc += dt; while (acc >= 1/fps) step()`）保留「第 N 幀發生什麼」，不要改成秒或 tween。
9. **Cocos 資源**：不要手寫 `.meta`、`.prefab`、`.scene`（受保護，由編輯器生成）。
   代碼按 `resources` 路徑引用資源。

## 隱私和密鑰

- 測試和 fixture 裡的持倉、賬號、行情一律用虛構數據。
- 不要把密鑰、token、真實賬號寫進代碼、配置、日誌或命令行。外部接口的 key 由服務端在運行時從環境變量讀取。

## 命令

    npm ci
    npm run typecheck            # tsc，覆蓋 packages/、server/、tools/
    npm test                     # vitest
    bash checks/core-purity.sh

`client/` 由 Cocos 編輯器管理，不在 typecheck 範圍內；Cocos 構建在容器裡做不了。

## 風格

- TypeScript strict；表驅動測試；測試名說明行為（`harvest gives seed back when crop withered`）。
- 註釋說明為什麼，不復述代碼做了什麼。
- 新增 npm 依賴要在 PR 說明裡寫明理由；能用標準庫或幾十行代碼解決的不要加依賴。
- 改動保持小而集中，一個 issue 只做一件事。
