import { readFileSync } from "node:fs";
import { PNG } from "pngjs";

export function readPng(file) {
  return PNG.sync.read(readFileSync(file));
}

// 返回 (x, y) 處的 [r, g, b]
export function pixel(png, x, y) {
  const i = (png.width * y + x) * 4;
  return [png.data[i], png.data[i + 1], png.data[i + 2]];
}

export function near(a, b, tolerance) {
  return a.every((v, i) => Math.abs(v - b[i]) <= tolerance);
}
