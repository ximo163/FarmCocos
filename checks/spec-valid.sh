#!/usr/bin/env bash
# spec/ 下的規格文件都是 JSON，必須能解析，且頂層帶 "version"。
set -u
status=0
shopt -s nullglob globstar
for f in spec/**/*.json; do
  node -e '
    const f = process.argv[1];
    let d;
    try { d = JSON.parse(require("fs").readFileSync(f, "utf8")); }
    catch (e) { console.log(f + ": 不是合法的 JSON：" + e.message); process.exit(1); }
    if (typeof d !== "object" || d === null || !("version" in d)) {
      console.log(f + ": 頂層必須是對象並帶 \"version\" 字段"); process.exit(1);
    }' "$f" || status=1
done
[ $status -eq 0 ] && echo "spec: ok"
exit $status
