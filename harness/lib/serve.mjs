// 最小的靜態文件服務：把一個目錄掛到 127.0.0.1 的隨機端口上，返回 { url, close }。
import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, join, normalize } from "node:path";

const types = {
  ".html": "text/html", ".js": "text/javascript", ".mjs": "text/javascript", ".json": "application/json",
  ".css": "text/css", ".wasm": "application/wasm", ".png": "image/png", ".jpg": "image/jpeg", ".gif": "image/gif",
  ".swf": "application/x-shockwave-flash", ".xml": "text/xml", ".mp3": "audio/mpeg", ".bin": "application/octet-stream",
};

export function serve(root) {
  const server = createServer(async (req, res) => {
    const path = decodeURIComponent(new URL(req.url, "http://x").pathname);
    const file = join(root, normalize(path === "/" ? "/index.html" : path));
    if (!file.startsWith(root)) { res.writeHead(403).end(); return; }
    try {
      const data = await readFile(file);
      res.writeHead(200, { "content-type": types[extname(file).toLowerCase()] ?? "application/octet-stream" }).end(data);
    } catch {
      res.writeHead(404).end();
    }
  });
  return new Promise((resolve) => server.listen(0, "127.0.0.1", () => resolve({
    url: `http://127.0.0.1:${server.address().port}`,
    close: () => new Promise((done) => server.close(done)),
  })));
}
