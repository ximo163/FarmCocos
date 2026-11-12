# FarmCocos：給 agent 的工作規則

這個倉庫把一個 Flash 種地遊戲（原版源碼已丟失，只剩部署目錄：swf、PHP 後端、xml 和圖片資源）
重寫成 Cocos Creator 客戶端（Android、PC）加 Node 服務端。開發由編排器流水線完成，
你很可能就是其中一個 agent。計劃、設計和文檔不在這裡，在 `ximo163/FarmCocos-docs`；
這個倉庫**不寫任何給人看的文檔**（README、docs/、*.md 都是受保護路徑）。

## 目錄

| 路徑 | 內容 | 誰改 |
|---|---|---|
| `legacy/deploy/` | 原版部署目錄，**按真實部署結構原樣放置**：swf、PHP 後端（規則的權威來源）、xml、png、gif 混在其中 | 人，只讀 |
| `legacy/manifest.json` | 部署目錄的說明：網站根目錄、PHP 入口、swf、配置、資源、建表 SQL、運行環境版本 | 人，只讀 |
| `legacy/decompiled/<路徑>/` | FFDec 從 swf 導出的內容；`<路徑>` 對應 swf 在 `legacy/deploy/` 裡的位置，如 `deploy/www/game/main.swf` → `decompiled/www/game/main/`。裡面有 `scripts/`（ActionScript）、`sprites/` 和 `frames/`（逐幀 PNG）、圖片和聲音、`swf.xml`（全部標籤：幀標籤、PlaceObject）、`header.txt`（swf 版本、幀率、舞台尺寸）、`xfl/`（重建的 XFL，可能不完整） | 由 `scripts/decompile-legacy.sh` 生成，只讀 |
| `legacy/traces/` | 錄下的原版行為軌跡（請求和響應、事件序列） | 人，只讀 |
| `spec/` | 從 legacy 提取的規格：協議、作物數據、交互映射 `interaction-map.json`、偏差清單 `deviations.json` | `pipeline:spec` 提取、人審核；其他流水線只讀 |
| `checks/`、`scripts/`、`ci/` | 校驗、反編譯、同步共用代碼、構建的腳本 | 人，只讀 |
| `harness/` | 自動驗收：在無界面瀏覽器裡運行新客戶端和原版（Ruffle），截圖、錄請求、比對 | 人，只讀 |
| `.github/workflows/` | 在 GitHub 上構建客戶端（網頁版、APK）並跑自動驗收 | 人，只讀 |
| `packages/core/` | 純 TS 遊戲邏輯，客戶端和服務端共用 | agent |
| `packages/<其他>/` | 其他能在容器裡測試的純 TS 包（時間軸播放器、手勢識別、佈局計算等表現層邏輯） | agent |
| `server/` | Node 服務端：鑒權、存檔、運行 core、拉取外部數據 | agent |
| `client/` | Cocos Creator 3.8.6 工程。手寫的骨架：一個空場景 `main.scene` 加啟動腳本 `Boot.ts`，沒有人會用編輯器打開它，構建在 GitHub 上完成。agent 只寫 `client/assets/scripts/` 下的 TS（薄膠水）和 `client/assets/resources/` 下的資源 | agent |
| `client/assets/scripts/shared/` | `packages/*/src` 的生成副本，client 通過它引用共用代碼 | `scripts/sync-shared.mjs` 生成，不要手改 |
| `tools/` | 轉換和比對工具（swf.xml → 時間軸 JSON、軌跡回放等） | agent |
| `timelines/` | 時間軸數據：幀率、幀數、幀標籤、每幀事件、逐幀圖的引用（由 tools 從 `swf.xml` 生成） | 工具生成 |
| `layouts/` | 界面佈局數據：每個界面的子元素、位置、層級（由 tools 從 `swf.xml` 的 PlaceObject 生成） | 工具生成 |

## 讀原版之前：先讀 legacy/manifest.json

`legacy/deploy/` 是原部署目錄的原樣副本，沒有按用途拆開，因為 PHP 的 include、swf 按相對 URL
加載 xml 和圖片，這些引用都依賴原來的結構。

- 先讀 `legacy/manifest.json`，從裡面找 PHP 入口、swf、配置 xml、資源和建表 SQL，不要在整個目錄裡盲搜。
  manifest 裡的路徑都相對 `legacy/`。
- 原版代碼裡的路徑按部署時的關係理解：PHP 的相對 include 相對於當前文件；swf 裡的相對 URL
  相對於 swf 所在目錄的 URL；`web_root` 對應網站根 URL `/`。`notes` 裡記了不明顯的關係。
- manifest 裡 `"placeholder": true` 表示部署目錄還沒放進來。需要原版依據的任務，最後一行輸出
  `BLOCKED: legacy/deploy 尚未放入原部署目錄（manifest 是佔位）`。
- 部署目錄裡的密碼、密鑰已被換成假值；不要嘗試恢復或猜測真實值。

## 原版行為就是需求

- 除非 `spec/deviations.json` 裡列出，否則行為必須和原版一致：數值、公式、時序、
  請求和響應、動畫幀上觸發的事件。
- 依據的優先順序：`legacy/traces/`（實際錄下的行為）> `legacy/deploy/` 裡的 PHP（服務端規則）>
  `legacy/decompiled/`（客戶端腳本和時間軸）> `legacy/deploy/` 裡的 xml。互相矛盾時以前者為準，
  並在 PR 說明裡寫出矛盾之處。
- 測試裡的每個期望值都要能指出出處：在測試上方用註釋寫明 legacy 裡的文件和位置
  （如 `// legacy/deploy/www/api/crop.php: harvest() 第 120 行`）。
- 規格裡找不到、legacy 裡也推不出來的行為，不要自己設計：最後一行輸出
  `BLOCKED: <缺什麼規格，在哪個文件遇到>`。
- 原版腳本可能是 AS2 也可能是 AS3，以 `header.txt` 和腳本的實際寫法為準。AS3 的交互是
  `addEventListener(MouseEvent.*)`；AS2 是 `onRelease`、`onRollOver`、`on(release)` 這類處理函數。
- 原版沒有的東西（`GameService`、輸入適配器、時間軸播放器、佈局生成、各種工具）以 issue 的描述為需求，
  測試的出處寫 `// issue #<編號>`。

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
8. **畫面用逐幀圖，時間軸只管邏輯**：動畫一律播放 FFDec 導出的逐幀 PNG（`sprites/`），
   不要還原補間、變換矩陣或嵌套剪輯，那等於重寫一個 Flash 渲染器。`timelines/*.json` 只記
   幀率、幀數、幀標籤、每幀事件和逐幀圖的引用。播放器用固定步長累加器
   （`acc += dt; while (acc >= 1/fps) step()`）保留「第 N 幀發生什麼」，不要改成秒或 tween。
9. **界面由代碼按佈局數據生成**：`client/` 裡只有一個空場景 `main.scene`，`Boot.ts` 在場景啟動後
   用代碼建立 Canvas 和相機。所有界面在運行時由代碼按 `layouts/*.json` 創建節點，不依賴 prefab
   或其他場景。不要寫 `.meta`、`.prefab`、`.scene`（受保護）：新加的腳本和資源不用配 `.meta`，
   GitHub 上構建時編輯器會自動生成。圖片、聲音放在 `client/assets/resources/` 下，代碼用
   `resources.load` 按路徑加載。
10. **client 只放薄膠水**：`client/assets/scripts/` 在容器裡編譯不了、測不了。有判斷的邏輯
    （手勢識別、佈局計算、播放器、狀態到畫面的映射）放在 `packages/` 下的純 TS 包裡並寫測試，
    client 腳本只負責把它們接到 Cocos 的節點和事件上。
11. **client 通過生成副本引用 `packages/`**：Cocos 工程只打包自己 `assets/` 下的腳本。
    `scripts/sync-shared.mjs` 把 `packages/<包>/src` 同步到 `client/assets/scripts/shared/<包>/`，
    流水線在每次 agent 運行後自動執行。client 腳本這樣引用：`import { X } from './shared/core/index'`。
    只改 `packages/` 裡的源文件，不要手改 `shared/`。`packages/` 裡的包之間用相對路徑互相引用時，
    要保證同步到 `shared/` 後路徑仍然成立（包和包之間用 `../../<包>/src/...` 這種寫法會斷，
    需要跨包引用時先停下來說明）。
12. **給自動化測試的掛鉤**：`Boot.ts` 把 `globalThis.__farm` 暴露給自動驗收（`ready`、`coreApi` 等）。
    新界面和新狀態需要被自動驗收看到時，往這個對象上加只讀的字段，不要刪已有的字段。

## 隱私和密鑰

- 測試和 fixture 裡的持倉、賬號、行情一律用虛構數據。
- 不要把密鑰、token、真實賬號寫進代碼、配置、日誌或命令行。外部接口的 key 由服務端在運行時從環境變量讀取。

## 命令

    npm ci
    npm run typecheck            # tsc，覆蓋 packages/、server/、tools/
    npm test                     # vitest
    bash checks/core-purity.sh
    bash checks/manifest-valid.sh
    node scripts/sync-shared.mjs --check   # client 裡的共用代碼副本和 packages/ 一致

`client/` 不在 typecheck 範圍內，容器裡也構建不了 Cocos。它在 GitHub Actions 上構建
（`.github/workflows/client.yml`）：`client-web` 構建網頁版，`client-smoke` 在無界面瀏覽器裡
啟動它做冒煙測試。這兩個檢查失敗時，失敗日誌會交還給你。

## 風格

- TypeScript strict；表驅動測試；測試名說明行為（`harvest gives seed back when crop withered`）。
- 註釋說明為什麼，不復述代碼做了什麼。
- 新增 npm 依賴要在 PR 說明裡寫明理由；能用標準庫或幾十行代碼解決的不要加依賴。
- 改動保持小而集中，一個 issue 只做一件事。
