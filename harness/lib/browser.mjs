// 啟動無界面 Chromium。WebGL 用軟件渲染（SwiftShader），這樣沒有顯卡的 CI 機器和容器裡
// 也能跑 Cocos 的網頁版。PW_CHROMIUM 可以指向一個已經裝好的 Chromium。
import { chromium } from "playwright";

export function launch() {
  return chromium.launch({
    executablePath: process.env.PW_CHROMIUM || undefined,
    args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist", "--enable-webgl"],
  });
}
