# 查看 swf 的 ActionScript 版本（AS3 還是 AS1/AS2）、swf 版本、幀率、幀數和舞台尺寸。
# 只用 Python 標準庫。用法：python3 scripts/swfinfo.py <swf 文件或目錄>...（目錄會遞歸查找）
# 對 AS3 的 swf 還會列出它引用了哪些網絡相關的類、數據格式的線索、有沒有被混淆的跡象：
# 默認只輸出類名和數量；加 --detail 才列出代碼裡提到的 .php 和 http 地址。
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
        elif code in (72, 82):                                        # DoABC：AS3 代碼塊
            c["as3"] += 1
            start = pos
            if code == 82:                                            # 帶標誌和名字的版本：跳過 4 字節標誌和以 0 結尾的名字
                z = body.find(b"\0", pos + 4, min(pos + n, end))
                start = z + 1 if z >= 0 else pos + n
            try: abc_strings(body, start, min(pos + n, end), c["strings"])
            except Exception: c["abc_errors"] += 1
        elif code in (12, 59): c["as2"] += 1                          # DoAction / DoInitAction：AS1/2 幀腳本
        elif code in (7, 34): c["as2"] += 1                           # 按鈕（AS1/2 寫法，AS3 裡極少用）
        elif code in (26, 70) and n and pos < end and body[pos] & 0x80: c["as2"] += 1   # 放置對象時帶的 onClipEvent
        elif code == 87: c["binary"] += 1                             # DefineBinaryData：內嵌的二進制數據，常用來藏加密的 swf
        elif code == 39: scan(body, pos + 4, min(pos + n, end), c)
        elif code == 0: c["ended"] = True; break
        pos += n

def abc_strings(body, pos, end, out):
    # 讀 AS3 代碼塊（ABC）開頭的常量池，只取字符串池：類名、方法名、字符串常量都以明文存在這裡
    def u30():
        nonlocal pos
        v = shift = 0
        while True:
            x = body[pos]; pos += 1
            v |= (x & 0x7F) << shift; shift += 7
            if not x & 0x80 or shift >= 35: return v
    pos += 4                                        # 版本號
    for _ in range(max(u30() - 1, 0)): u30()        # 整數池
    for _ in range(max(u30() - 1, 0)): u30()        # 無符號整數池
    doubles = u30()                                 # 浮點數池（先讀個數再跳：u30 會改 pos，不能寫在同一個 += 裡）
    pos += 8 * max(doubles - 1, 0)
    for _ in range(max(u30() - 1, 0)):              # 字符串池
        n = u30()
        if pos + n > end: break
        out.add(body[pos:pos + n].decode("utf-8", "replace")); pos += n

NET_CLASSES = ["URLLoader", "URLStream", "NetConnection", "NetStream", "Socket", "XMLSocket", "SecureSocket",
               "LocalConnection", "SharedObject", "ExternalInterface", "Loader", "FileReference", "navigateToURL", "sendToURL"]

def describe_code(strings, detail):
    lines = []
    used = [k for k in NET_CLASSES if k in strings]
    php = sorted(x for x in strings if ".php" in x.lower())
    urls = sorted(x for x in strings if x.lower().startswith(("http://", "https://")))
    lines.append("網絡：" + (", ".join(used) if used else "沒有引用網絡相關的類")
                 + f" | 提到 .php 的字符串 {len(php)} 個，http(s) 地址 {len(urls)} 個")
    fmt = []
    low = {x.lower() for x in strings}
    if "NetConnection" in strings and ("call" in strings or any("gateway" in x or "amf" in x for x in low)):
        fmt.append("AMF 遠程調用（NetConnection.call，後端多半是 amfphp 這類網關）")
    if "registerClassAlias" in strings or "ObjectEncoding" in strings or "readObject" in strings or "writeObject" in strings:
        fmt.append("AMF 對象序列化（readObject/writeObject/registerClassAlias）")
    if "JSON" in strings or any("json" in x for x in low): fmt.append("JSON")
    if "XML" in strings or "XMLList" in strings or "XMLDocument" in strings: fmt.append("XML")
    if "URLVariables" in strings: fmt.append("表單參數（URLVariables）")
    if "Socket" in strings or "XMLSocket" in strings: fmt.append("長連接（Socket）")
    lines.append("數據格式的線索：" + ("；".join(fmt) if fmt else "沒有明顯線索"))
    # 混淆的跡象：標識符裡有不可見字符，或大量 _-xx 這種工具生成的名字
    names = [x for x in strings if 0 < len(x) <= 40 and " " not in x]
    weird = [x for x in names if any(ord(ch) < 32 or ch == "\ufffd" for ch in x) or (x.startswith("_-") and len(x) <= 8)]
    ratio = len(weird) / max(len(names), 1)
    verdict = "明顯被混淆" if ratio > 0.2 else ("可能部分混淆" if ratio > 0.03 else "沒有發現混淆的跡象")
    lines.append(f"混淆：{verdict}（{len(names)} 個短字符串裡有 {len(weird)} 個不正常的名字）")
    if detail:
        for title, items in (("提到 .php 的字符串", php), ("http(s) 地址", urls)):
            if items: lines.append(title + "：\n        " + "\n        ".join(items[:200]))
    return lines

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

def info(path, detail=False):
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
        c = {"as3": 0, "as2": 0, "tags": 0, "binary": 0, "ended": False, "strings": set(), "abc_errors": 0}
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
    if c["abc_errors"]: print("    注意：有 AS3 代碼塊的常量池讀不出來，下面的結果可能不全")
    if c["strings"]:
        for line in describe_code(c["strings"], detail): print("    " + line)

detail = "--detail" in sys.argv
for arg in [a for a in sys.argv[1:] if a != "--detail"] or ["."]:
    if os.path.isdir(arg):
        for root, _, files in os.walk(arg):
            for f in sorted(files):
                if f.lower().endswith(".swf"):
                    try: info(os.path.join(root, f), detail)
                    except Exception as e: print(f"{os.path.join(root, f)}: 讀取出錯：{e}")
    else:
        try: info(arg, detail)
        except Exception as e: print(f"{arg}: 讀取出錯：{e}")
