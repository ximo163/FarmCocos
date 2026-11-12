// 把 packages/*/src 下的 TypeScript 同步到 client/assets/scripts/shared/<包名>/。
// Cocos 工程只打包自己 assets/ 目錄下的腳本，引用不了工程外的源碼，所以共用代碼以
// 生成副本的形式進入 client。流水線每次 agent 運行後自動執行（generated.cmd），
// 不要手改 shared/ 下的文件：改 packages/ 裡的源文件。
// 用法：node scripts/sync-shared.mjs [--check]   --check 只檢查是否一致，不寫文件
import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync } from "node:fs";
import { join, relative } from "node:path";

const src = "packages";
const dst = "client/assets/scripts/shared";
const check = process.argv.includes("--check");

function listTs(dir) {
  if (!existsSync(dir)) return [];
  const out = [];
  for (const name of readdirSync(dir).sort()) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) out.push(...listTs(p));
    else if (name.endsWith(".ts") && !name.endsWith(".test.ts")) out.push(p);
  }
  return out;
}

const wanted = new Map(); // 目標路徑 -> 源路徑
for (const pkg of existsSync(src) ? readdirSync(src).sort() : []) {
  const root = join(src, pkg, "src");
  for (const file of listTs(root)) wanted.set(join(dst, pkg, relative(root, file)), file);
}
// .meta 由 Cocos 編輯器在構建時生成，不屬於同步內容
const existing = listTs(dst);

const problems = [];
for (const [to, from] of wanted) {
  if (!existsSync(to) || readFileSync(to, "utf8") !== readFileSync(from, "utf8")) problems.push(`過期或缺少：${to}（來自 ${from}）`);
}
for (const file of existing) if (!wanted.has(file)) problems.push(`多餘：${file}（packages/ 裡已經沒有對應的源文件）`);

if (check) {
  if (problems.length) {
    console.log("client/assets/scripts/shared/ 和 packages/ 不一致：\n  " + problems.join("\n  "));
    console.log("運行 node scripts/sync-shared.mjs 重新生成，不要手改 shared/ 下的文件。");
    process.exit(1);
  }
  console.log(`shared: ok（${wanted.size} 個文件）`);
} else {
  for (const file of existing) if (!wanted.has(file)) rmSync(file);
  for (const [to, from] of wanted) {
    mkdirSync(join(to, ".."), { recursive: true });
    cpSync(from, to);
  }
  console.log(`shared: 已同步 ${wanted.size} 個文件`);
}
