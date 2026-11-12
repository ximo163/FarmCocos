// 在無界面瀏覽器裡用 Ruffle 運行原版 swf：截圖，並把它發出的全部網絡請求錄成 HAR。
// 這是「原版這一側」自動化的基礎：錄行為軌跡、截參考圖都建立在它上面，不需要人來玩。
// 用法：node ruffle-run.mjs <網站根目錄> <swf 相對網站根目錄的路徑> [輸出目錄] [等待毫秒]
//   網站根目錄一般是 legacy/deploy 裡的 web_root，swf 按相對 URL 加載的 xml 和圖片都從這裡取。
// 輸出：<輸出目錄>/ruffle.png、ruffle.har、ruffle.json（swf 的幀率、尺寸、AS 版本）
import { mkdirSync, writeFileSync, cpSync, mkdtempSync, existsSync } from "node:fs";
import { resolve, join, dirname } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { serve } from "./lib/serve.mjs";
import { launch } from "./lib/browser.mjs";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(process.argv[2] ?? "");
const swf = process.argv[3];
const out = resolve(process.argv[4] ?? "out");
const waitMs = Number(process.argv[5] ?? 3000);
if (!swf || !existsSync(join(root, swf))) {
  console.log("用法：node ruffle-run.mjs <網站根目錄> <swf 相對路徑> [輸出目錄] [等待毫秒]；找不到 " + join(root, swf ?? ""));
  process.exit(1);
}
mkdirSync(out, { recursive: true });

// 播放頁和 Ruffle 放在一個臨時目錄裡，網站根目錄掛在 /site/ 下，原版的目錄不用改動
const stage = mkdtempSync(join(tmpdir(), "ruffle-"));
cpSync(join(here, "node_modules/@ruffle-rs/ruffle"), join(stage, "ruffle"), { recursive: true });
cpSync(root, join(stage, "site"), { recursive: true });
writeFileSync(join(stage, "index.html"), `<!doctype html><body style="margin:0;background:#fff"><div id="c"></div>
<script src="ruffle/ruffle.js"></script>
<script>
const p = window.RufflePlayer.newest().createPlayer();
document.getElementById("c").appendChild(p);
// canvas 渲染器：軟件渲染的 WebGL 下 Ruffle 會彈出「硬件加速已關閉」的提示擋住畫面
p.load({ url: ${JSON.stringify("site/" + swf)}, base: ${JSON.stringify("site/" + swf.replace(/[^/]*$/, ""))}, autoplay: "on", unmuteOverlay: "hidden",
         splashScreen: false, preferredRenderer: "canvas", letterbox: "off" })
  .then(() => { window.loaded = true; }).catch((e) => { window.err = String(e); });
</script></body>`);

const site = await serve(stage);
const browser = await launch();
const context = await browser.newContext({ recordHar: { path: join(out, "ruffle.har") }, viewport: { width: 1280, height: 960 } });
const page = await context.newPage();
const errors = [];
page.on("pageerror", (e) => errors.push(String(e)));
await page.goto(site.url);
await page.waitForFunction(() => window.loaded || window.err, null, { timeout: 120000 });
const info = await page.evaluate(() => {
  const p = document.querySelector("ruffle-player");
  const m = p.metadata ?? {};
  p.style.width = (m.width || 800) + "px";
  p.style.height = (m.height || 600) + "px";
  return { error: window.err ?? null, metadata: m };
});
await page.waitForTimeout(waitMs);
await page.locator("ruffle-player").screenshot({ path: join(out, "ruffle.png") });
await context.close();
await browser.close();
await site.close();

writeFileSync(join(out, "ruffle.json"), JSON.stringify({ swf, ...info, errors }, null, 2));
if (info.error) { console.log("Ruffle 加載失敗：" + info.error); process.exit(1); }
console.log(`Ruffle 運行完成：${JSON.stringify(info.metadata)}，輸出在 ${out}`);
