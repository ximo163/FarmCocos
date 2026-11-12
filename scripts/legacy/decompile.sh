#!/usr/bin/env bash
# 由人運行（agent 容器裡沒有 Java 和 FFDec）：找出 legacy/deploy/ 下所有 swf，
# 導出到 legacy/decompiled/ 下的對應路徑，例如
#   legacy/deploy/www/game/main.swf -> legacy/decompiled/www/game/main/
# 內容包括 ActionScript、圖片、聲音、sprite 逐幀圖，和整個 swf 的 XML
# （幀標籤、PlaceObject 等時間軸數據都在 swf.xml 裡）。
# 需要 Java 和 JPEXS FFDec：https://github.com/jindrapetrik/jpexs-decompiler/releases
# 用法：FFDEC_JAR=/path/to/ffdec.jar scripts/legacy/decompile.sh
# 導出項目的名字以 `java -jar ffdec.jar --help` 為準，不同版本可能有差別。
set -euo pipefail
: "${FFDEC_JAR:?請設置 FFDEC_JAR=/path/to/ffdec.jar}"
src=legacy/deploy
count=0
while IFS= read -r -d '' swf; do
  rel=${swf#"$src"/}
  out="legacy/decompiled/${rel%.*}"
  rm -rf "$out"
  mkdir -p "$out"
  java -jar "$FFDEC_JAR" -export script,image,shape,morphshape,sound,text,binaryData,frame,sprite "$out" "$swf"
  java -jar "$FFDEC_JAR" -swf2xml "$swf" "$out/swf.xml"
  echo "$swf -> $out"
  count=$((count + 1))
done < <(find "$src" -type f -iname '*.swf' -print0 | sort -z)
[ "$count" -gt 0 ] || { echo "$src 下沒有 .swf 文件：先把原部署目錄原樣放進 $src"; exit 1; }
