測試已經通過；你要找的是測試發現不了的問題。先讀 CLAUDE.md，違反其中規則的一律駁回。

以下任一成立就駁回：

- 實現只對測試裡出現的輸入成立（硬編碼期望值、針對特定輸入的分支）。
- 和原版行為不一致，且 `spec/deviations.json` 裡沒有列出。挑一兩處核心公式，自己對照 `legacy/deploy/` 裡的 PHP（位置見 `legacy/manifest.json`）或 `legacy/decompiled/` 核實。
- 違反架構約定：core 裡出現 I/O、真實時間、隨機數或 `cc`；原始輸入事件進了 core；繞過 `GrowthDriver` 直接決定作物狀態；客戶端繞過 `GameService`；經驗或等級依賴了行情數據。
- 觸屏交互不在 `spec/interaction-map.json` 裡，或和映射表的規定不一致。
- 手寫了 `.meta`、`.prefab`、`.scene`，或在 client/ 裡改了腳本以外的東西。
- 有判斷的邏輯寫在了 `client/assets/scripts/` 裡而不是 `packages/` 下可測的包裡；或者去還原補間、變換矩陣，而不是播放逐幀圖。
- 密鑰、真實賬號或真實持倉出現在代碼、測試、日誌或配置裡。
- 新增依賴沒有充分理由。
- 有無關改動、死代碼、調試殘留，或新增了給人看的文檔（README、*.md）。

測試有問題時說明是哪一種：

- 缺少 issue 需要的測試：照常 `VERDICT: REJECT`，寫明要補哪些測試，實現階段可以新增測試文件。
- 已有的測試寫錯了（和 legacy 對不上）：最後一行 `VERDICT: REJECT TESTS`，工作會退回寫測試的階段。

不要因為風格偏好駁回。
