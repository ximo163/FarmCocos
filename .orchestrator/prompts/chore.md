做這個腳手架或配置類的改動。先讀 CLAUDE.md。

- 只做 issue 要求的事；不順手實現遊戲邏輯，那屬於默認流水線（先寫測試）。
- 不改 legacy/、spec/、checks/，不寫給人看的文檔。
- 新增 npm 依賴時在最後的回答裡寫明理由，並同時提交 package-lock.json。
- 改完後 `npm ci`、`npm run typecheck`、`npm test` 都要能通過。
- 最後的回答裡概括改了什麼，以及人需要在本地或 Cocos 編輯器裡做的後續步驟（如果有）。
