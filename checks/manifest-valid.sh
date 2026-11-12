#!/usr/bin/env bash
# legacy/manifest.json 告訴 agent 原部署目錄裡什麼是什麼。它寫錯了，agent 會讀錯地方，
# 所以任務開始前（preflight）先檢查：能解析、必填項都填了、寫的路徑都存在。
# "placeholder": true 時部署目錄還沒放進來，只提示、不擋任務。
set -u
node - <<'JS'
const fs = require("fs");
const path = require("path");
const file = "legacy/manifest.json";
const fail = (msg) => { console.log(file + ": " + msg); process.exit(1); };
let m;
try { m = JSON.parse(fs.readFileSync(file, "utf8")); }
catch (e) { fail("讀不到或不是合法的 JSON：" + e.message); }
if (m.version !== 1) fail("\"version\" 必須是 1");
if (m.placeholder === true) {
  console.log(file + ": 還是佔位（placeholder: true），legacy/deploy/ 尚未放入原部署目錄；需要原版依據的任務會 BLOCKED");
  process.exit(0);
}
const errors = [];
if (typeof m.web_root !== "string" || !m.web_root) errors.push("\"web_root\" 必須填寫（相對 legacy/ 的網站根目錄，如 \"deploy/www\"）");
if (!Array.isArray(m.server?.entries) || m.server.entries.length === 0) errors.push("\"server.entries\" 至少寫一個 PHP 入口文件");
if (!Array.isArray(m.client?.swf) || m.client.swf.length === 0) errors.push("\"client.swf\" 至少寫一個 swf 文件");
const paths = [];
const collect = (v) => {
  if (typeof v === "string") paths.push(v);
  else if (Array.isArray(v)) v.forEach(collect);
};
collect(m.web_root);
for (const k of ["entries", "include_roots"]) collect(m.server?.[k]);
collect(m.client?.swf);
for (const k of ["config_xml", "assets", "db_schema"]) collect(m[k]);
collect(m.runtime?.source);
for (const k of Object.keys(m.notes ?? {})) collect(k);
for (const p of paths) {
  if (p.startsWith("/") || p.split("/").includes("..")) errors.push(p + "：路徑必須相對 legacy/，不能以 / 開頭或含 ..");
  else if (!fs.existsSync(path.join("legacy", p))) errors.push(p + "：legacy/ 下不存在這個路徑");
}
if (errors.length) fail("\n  - " + errors.join("\n  - "));
console.log(file + ": ok（" + paths.length + " 個路徑）");
JS
