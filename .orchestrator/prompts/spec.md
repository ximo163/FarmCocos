從 legacy/ 提取規格，寫進 spec/。只能改 spec/。先讀 CLAUDE.md，再讀 `legacy/manifest.json` 找到要讀的文件。

- spec/ 下的文件都是 JSON，頂層帶 `"version": 1`，`checks/spec-valid.sh` 會檢查。
- 規格只描述原版**是什麼**，不做設計。每一條都帶 `source` 字段，寫明出處（如 `"legacy/deploy/www/api/farm.php: harvest() 第 88-120 行"`，或 `"legacy/decompiled/www/game/main/scripts/Farm.as: onTileOver"`）。
- 推不確定的地方不要猜：用 `"unknown": "<說明>"` 標出來，交給人補。
- 數值、公式、枚舉照原樣抄，不換單位、不取整；原版用幀數的就寫幀數並註明幀率。
- 只讀需要的部分：先 `rg -n` 找名字，再讀附近的行。
- 最後的回答裡列出新增或修改的規格文件，以及標成 unknown 的條目。
