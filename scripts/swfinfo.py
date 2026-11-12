# 查看 swf 的 ActionScript 版本（AS3 還是 AS1/AS2）、swf 版本、幀率、幀數和舞台尺寸。
# 只用 Python 標準庫。用法：python3 scripts/swfinfo.py <swf 文件或目錄>...（目錄會遞歸查找）
# 解不開的文件（加密、加殼、被改過文件頭）不會中斷，會打印診斷信息。
import sys, os, zlib, lzma, struct

def scan(body, pos, end, c):
    # 逐個標籤掃描；DefineSprite(39) 裡面還有一層標籤（剪輯自己的幀腳本）
    while pos + 2 <= end:
        h = struct.unpack("<H", body[pos:pos + 2])[0]; pos += 2
        code, n = h >> 6, h & 0x3F
        if n == 0x3F:
            if pos + 4 > end: break
            n = struct.unpack("<I", body[pos:pos + 4])[0]; pos += 4
        c["tags"] += 1
        if code == 69 and n and pos < end and body[pos] & 0x08: c["as3"] += 1   # FileAttributes 的 AS3 標誌
        elif code in (72, 82): c["as3"] += 1                          # DoABC：AS3 代碼塊
        elif code in (12, 59): c["as2"] += 1                          # DoAction / DoInitAction：AS1/2 幀腳本
        elif code in (7, 34): c["as2"] += 1                           # 按鈕（AS1/2 寫法，AS3 裡極少用）
        elif code in (26, 70) and n and pos < end and body[pos] & 0x80: c["as2"] += 1   # 放置對象時帶的 onClipEvent
        elif code == 87: c["binary"] += 1                             # DefineBinaryData：內嵌的二進制數據，常用來藏加密的 swf
        elif code == 39: scan(body, pos + 4, min(pos + n, end), c)
        elif code == 0: c["ended"] = True; break
        pos += n

def inflate(data):
    # 返回 (解出的數據, 用了哪種辦法)。數據不完整時盡量返回已解出的部分：掃標籤只需要前面一段。
    tries = [("標準 zlib", 0, 15), ("沒有 zlib 頭的原始 deflate", 0, -15)]
    # 有的保護手法在文件頭後面插幾個字節：往後找 zlib 頭（0x78 開頭）
    for off in range(1, 64):
        if data[off:off + 1] == b"\x78" and data[off + 1:off + 2] in (b"\x01", b"\x5e", b"\x9c", b"\xda"):
            tries.append((f"跳過 {off} 個多餘字節後的 zlib", off, 15))
    for name, off, wbits in tries:
        try:
            out = zlib.decompressobj(wbits).decompress(data[off:])
            if len(out) > 16: return out, name
        except zlib.error:
            pass
    return None, None

def info(path):
    d = open(path, "rb").read()
    if len(d) < 8: return print(f"{path}: 文件太小，不是 swf")
    sig, ver, length = d[:3], d[3], struct.unpack("<I", d[4:8])[0]
    how = ""
    if sig == b"FWS": body = d[8:]
    elif sig == b"CWS":
        body, how = inflate(d[8:])
        if body is None:
            return print(f"{path}: 解不開 —— 文件頭是 CWS（zlib 壓縮），但後面不是合法的壓縮數據，很可能被加密或加殼了。"
                         f"\n    文件 {len(d)} 字節，文件頭聲明解壓後 {length} 字節，swf 版本 {ver}"
                         f"\n    前 32 字節：{d[:32].hex(' ')}")
    elif sig == b"ZWS":
        try: body = lzma.decompress(d[12:17] + struct.pack("<Q", length - 8) + d[17:], format=lzma.FORMAT_ALONE)
        except Exception as e: return print(f"{path}: 解不開 —— 文件頭是 ZWS（LZMA 壓縮），解壓失敗：{e}\n    前 32 字節：{d[:32].hex(' ')}")
    else:
        return print(f"{path}: 不是標準的 swf（文件頭不是 FWS/CWS/ZWS），可能整個文件被加密了。前 32 字節：{d[:32].hex(' ')}")
    try:
        nbits = body[0] >> 3
        size = (5 + 4 * nbits + 7) // 8
        bits = int.from_bytes(body[:size], "big") >> ((-(5 + 4 * nbits)) % 8)
        v = [(bits >> (nbits * i)) & ((1 << nbits) - 1) for i in (3, 2, 1, 0)]
        fps = body[size + 1] + body[size] / 256
        frames = struct.unpack("<H", body[size + 2:size + 4])[0]
        c = {"as3": 0, "as2": 0, "tags": 0, "binary": 0, "ended": False}
        scan(body, size + 4, len(body), c)
    except Exception as e:
        return print(f"{path}: 解壓成功但內容不像 swf（{e}），可能被加密了。解壓後前 32 字節：{body[:32].hex(' ')}")
    lang = "AS3" if c["as3"] else ("AS1/AS2" if c["as2"] else "沒有腳本（純資源文件）")
    notes = []
    if how and how != "標準 zlib": notes.append("壓縮數據不標準：" + how)
    if not c["ended"]: notes.append("標籤沒有正常結束，文件可能不完整或後半段被加密")
    if c["binary"]: notes.append(f"內嵌 {c['binary']} 塊二進制數據（可能是被加密的子 swf）")
    print(f"{path}: {lang} | swf 版本 {ver} | {fps:g} fps | {frames} 幀 | 舞台 {(v[1]-v[0])//20}x{(v[3]-v[2])//20} | "
          f"標籤 {c['tags']} 個, AS3 標記 {c['as3']} 處, AS1/2 標記 {c['as2']} 處" + ("".join("\n    注意：" + n for n in notes)))

for arg in sys.argv[1:] or ["."]:
    if os.path.isdir(arg):
        for root, _, files in os.walk(arg):
            for f in sorted(files):
                if f.lower().endswith(".swf"):
                    try: info(os.path.join(root, f))
                    except Exception as e: print(f"{os.path.join(root, f)}: 讀取出錯：{e}")
    else:
        try: info(arg)
        except Exception as e: print(f"{arg}: 讀取出錯：{e}")
