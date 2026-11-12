#!/usr/bin/env bash
# packages/core 必須是純邏輯：不碰引擎、網絡、存儲、真實時間和隨機數，
# 這樣它才能同時跑在 Cocos 客戶端和 Node 服務端，並且能確定性地回放行為軌跡。
# 時間和隨機數由調用方注入（Clock、Rng 接口）。
set -u
dir=packages/core/src
[ -d "$dir" ] || exit 0
q="[\"']"
pattern="from[[:space:]]+${q}cc${q}|require\(${q}cc${q}\)|from[[:space:]]+${q}(node:)?(fs|path|net|http|https|child_process|os)${q}|\bfetch\(|XMLHttpRequest|WebSocket|localStorage|sessionStorage|Date\.now\(|new Date\(\)|performance\.now\(|Math\.random\(|setTimeout\(|setInterval\(|process\.env"
if grep -rnE --include='*.ts' "$pattern" "$dir"; then
  echo
  echo "packages/core/src 裡出現了上面這些行：core 不能 import cc 或 Node 模塊，不能聯網、讀寫存儲，"
  echo "不能直接讀時間（Date.now / new Date()）或用 Math.random。改成從參數傳入 Clock / Rng，"
  echo "I/O 放到 server/ 或 client/ 的適配器裡。"
  exit 1
fi
echo "core purity: ok"
