// 冒煙測試：新客戶端的網頁版能在無界面瀏覽器裡啟動並渲染。
// 用法：node smoke.mjs <web-mobile 構建目錄> [輸出目錄]
// 檢查：啟動掛鉤 __farm.ready、沒有未捕獲的錯誤、共用代碼接上了（coreApi）、
//       沒提交 .meta 的資源能加載（probe）、屏幕正中是啟動標記的顏色。
import { mkdirSync, writeFileSync, existsSync } from "node:fs";
import { resolve, join } from "node:path";
import { serve } from "./lib/serve.mjs";
import { launch } from "./lib/browser.mjs";
import { readPng, pixel, near } from "./lib/png.mjs";

const dir = resolve(process.argv[2] ?? "");
const out = resolve(process.argv[3] ?? "out");
if (!existsSync(join(dir, "index.html"))) {
  console.log(`找不到 ${join(dir, "index.html")}：Cocos 的 web-mobile 構建沒有產出，先看構建日誌`);
  process.exit(1);
}
mkdirSync(out, { recursive: true });

const MARKER = [16, 192, 64]; // client/assets/scripts/Boot.ts 畫的啟動標記
const W = 960, H = 640;
const site = await serve(dir);
const browser = await launch();
const page = await browser.newPage({ viewport: { width: W, height: H } });
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
// 加載失敗的資源按 URL 記（瀏覽器控制台的那條消息不帶 URL）；favicon 不算
page.on("console", (m) => { if (m.type() === "error" && !m.text().startsWith("Failed to load resource")) errors.push(m.text()); });
page.on("response", (r) => { if (r.status() >= 400 && !r.url().endsWith("/favicon.ico")) errors.push(`${r.status()} ${r.url()}`); });

const failures = [];
let hook = null;
try {
  await page.goto(site.url);
  await page.waitForFunction(() => globalThis.__farm && globalThis.__farm.ready, null, { timeout: 120000 });
  await page.waitForFunction(() => globalThis.__farm.probe !== "pending", null, { timeout: 30000 }).catch(() => {});
  await page.waitForTimeout(1000);
  hook = await page.evaluate(() => ({ ...globalThis.__farm }));
} catch (e) {
  failures.push("客戶端沒有在 120 秒內啟動（__farm.ready 沒有變成 true）：" + String(e).split("\n")[0]);
}
const shot = join(out, "smoke.png");
await page.screenshot({ path: shot });
await browser.close();
await site.close();

if (hook) {
  if (typeof hook.coreApi !== "number") failures.push("__farm.coreApi 不是數字：client 沒有接上 packages/core 的共用代碼");
  if (hook.probe !== "ok") failures.push("resources/probe.png 沒有加載成功（" + hook.probe + "）：沒提交 .meta 的資源在構建時沒有被導入");
  const center = pixel(readPng(shot), W / 2, H / 2);
  if (!near(center, MARKER, 12)) failures.push(`屏幕正中的顏色是 ${center}，應該是啟動標記 ${MARKER}：畫面沒有渲染出來`);
}
if (errors.length) failures.push("頁面報錯：\n    " + errors.slice(0, 10).join("\n    "));

writeFileSync(join(out, "smoke.json"), JSON.stringify({ ok: failures.length === 0, hook, failures, errors }, null, 2));
if (failures.length) {
  console.log("冒煙測試失敗：\n  - " + failures.join("\n  - "));
  console.log(`截圖：${shot}`);
  process.exit(1);
}
console.log(`冒煙測試通過：coreApi=${hook.coreApi} probe=${hook.probe}，截圖 ${shot}`);
