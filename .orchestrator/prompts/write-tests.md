只寫這個任務的測試，不做實現。先讀 CLAUDE.md。

- 需求來自原版：期望值從 `legacy/traces/`、`legacy/deploy/`（先看 `legacy/manifest.json` 找到 PHP 和 xml 在哪）、`legacy/decompiled/` 和 `spec/` 推出來，不要憑感覺猜。每個期望值上方用註釋寫明出處（文件和位置）。
- 只讀需要的部分：先 `rg -n` 找名字，再讀前後幾十行。legacy 裡的反編譯代碼和 xml 很大，整個文件讀進來會很快耗光輪數。
- 測試放在被測代碼旁邊：`packages/core/test/`、`server/test/`、`tools/**/*.test.ts`。表驅動，測試名說明行為。
- 涉及時間的邏輯，用注入的 `Clock` 控制時間；涉及隨機的，用注入的 `Rng`。測試不能 sleep、不能聯網、不能依賴真實時間。
- 被測代碼還不存在時，加最小的能編譯的 stub：簽名正確，函數體 `throw new Error("not implemented")`。不要做任何實現。
- 新測試必須在實現之前失敗；已有的測試必須照樣通過。
- 只有 issue 改變了某個已有測試檢查的行為時，才能改那個測試，並在上方註釋 `// changed for #<issue>: <原因>`。
- 測試數據裡的持倉、賬號、行情一律虛構。大段 fixture 放在 `fixtures/` 目錄下。
- legacy 和 spec 裡都推不出某個行為時，最後一行輸出 `BLOCKED: <缺什麼，在哪裡遇到>`，不要自己設計。
- 最後的回答裡列出新增的測試，以及改過的已有測試。
