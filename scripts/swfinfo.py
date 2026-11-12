# 查看 swf 的 ActionScript 版本（AS3 還是 AS1/AS2）、swf 版本、幀率、幀數和舞台尺寸。
# 只用 Python 標準庫。用法：python3 scripts/swfinfo.py <swf 文件或目錄>...（目錄會遞歸查找）
import sys, os, zlib, lzma, struct

def scan(body, pos, end, c):
    # 逐個標籤掃描；DefineSprite(39) 裡面還有一層標籤（剪輯自己的幀腳本）
    while pos + 2 <= end:
        h = struct.unpack("<H", body[pos:pos + 2])[0]; pos += 2
        code, n = h >> 6, h & 0x3F
        if n == 0x3F: n = struct.unpack("<I", body[pos:pos + 4])[0]; pos += 4
        if code == 69 and n and body[pos] & 0x08: c["as3"] += 1      # FileAttributes 的 AS3 標誌
        elif code in (72, 82): c["as3"] += 1                          # DoABC：AS3 代碼塊
        elif code in (12, 59): c["as2"] += 1                          # DoAction / DoInitAction：AS1/2 幀腳本
        elif code in (7, 34): c["as2"] += 1                           # 按鈕（AS1/2 寫法，AS3 裡極少用）
        elif code in (26, 70) and n and body[pos] & 0x80: c["as2"] += 1   # 放置對象時帶的 onClipEvent
        elif code == 39: scan(body, pos + 4, pos + n, c)
        elif code == 0: break
        pos += n

def info(path):
    d = open(path, "rb").read()
    sig, ver, length = d[:3], d[3], struct.unpack("<I", d[4:8])[0]
    if sig == b"FWS": body = d[8:]
    elif sig == b"CWS": body = zlib.decompress(d[8:])
    elif sig == b"ZWS": body = lzma.decompress(d[12:17] + struct.pack("<Q", length - 8) + d[17:], format=lzma.FORMAT_ALONE)
    else: return print(f"{path}: 不是 swf 文件")
    nbits = body[0] >> 3
    size = (5 + 4 * nbits + 7) // 8
    bits = int.from_bytes(body[:size], "big") >> ((-(5 + 4 * nbits)) % 8)
    v = [(bits >> (nbits * i)) & ((1 << nbits) - 1) for i in (3, 2, 1, 0)]
    fps = body[size + 1] + body[size] / 256
    frames = struct.unpack("<H", body[size + 2:size + 4])[0]
    c = {"as3": 0, "as2": 0}
    scan(body, size + 4, len(body), c)
    lang = "AS3" if c["as3"] else ("AS1/AS2" if c["as2"] else "沒有腳本（純資源文件）")
    print(f"{path}: {lang} | swf 版本 {ver} | {fps:g} fps | {frames} 幀 | 舞台 {(v[1]-v[0])//20}x{(v[3]-v[2])//20} | AS3 標記 {c['as3']} 處, AS1/2 標記 {c['as2']} 處")

for arg in sys.argv[1:] or ["."]:
    if os.path.isdir(arg):
        for root, _, files in os.walk(arg):
            for f in sorted(files):
                if f.lower().endswith(".swf"): info(os.path.join(root, f))
    else: info(arg)
