#!/usr/bin/env bash
# 由人運行一次（agent 容器裡沒有 Java 和 FFDec）：把 legacy/swf/*.swf 導出到
# legacy/decompiled/<名字>/，包括 ActionScript、圖片、聲音、sprite 逐幀圖和整個 swf 的 XML
# （幀標籤、PlaceObject 等時間軸數據都在 swf.xml 裡）。
# 需要 Java 和 JPEXS FFDec：https://github.com/jindrapetrik/jpexs-decompiler/releases
# 用法：FFDEC_JAR=/path/to/ffdec.jar scripts/legacy/decompile.sh
# 導出項目的名字以 `java -jar ffdec.jar --help` 為準，不同版本可能有差別。
set -euo pipefail
: "${FFDEC_JAR:?請設置 FFDEC_JAR=/path/to/ffdec.jar}"
shopt -s nullglob
swfs=(legacy/swf/*.swf)
[ ${#swfs[@]} -gt 0 ] || { echo "legacy/swf/ 下沒有 .swf 文件"; exit 1; }
for swf in "${swfs[@]}"; do
  name=$(basename "$swf" .swf)
  out="legacy/decompiled/$name"
  rm -rf "$out"
  mkdir -p "$out"
  java -jar "$FFDEC_JAR" -export script,image,shape,morphshape,sound,text,binaryData,frame,sprite "$out" "$swf"
  java -jar "$FFDEC_JAR" -swf2xml "$swf" "$out/swf.xml"
  echo "$swf -> $out"
done
