#!/usr/bin/env bash
# 由人運行（agent 容器裡沒有 Java 和 FFDec）：找出 legacy/deploy/ 下所有 swf，
# 導出到 legacy/decompiled/ 下的對應路徑，例如
#   legacy/deploy/www/game/main.swf -> legacy/decompiled/www/game/main/
#
# 每個 swf 導出：
#   scripts/ images/ shapes/ sounds/ texts/ buttons/ ...  腳本和資源
#   sprites/  frames/                                      每個 sprite、主時間軸的逐幀 PNG
#   swf.xml                                                整個 swf 的標籤（幀標籤、PlaceObject、幀腳本位置）
#   header.txt                                             swf 版本、幀率、舞台尺寸
#   xfl/                                                   FFDec 重建的 XFL（DOMDocument.xml、LIBRARY/*.xml）
#
# 需要 Java 和 JPEXS FFDec：https://github.com/jindrapetrik/jpexs-decompiler/releases
# 用法：FFDEC_JAR=/path/to/ffdec.jar scripts/decompile-legacy.sh
# 參數對照的是 FFDec 源碼裡的 CommandLineArgumentParser；舊版本可能不支持 xfl、button、
# symbolclass 這幾項，所以它們單獨導出，失敗只提示、不中斷。
set -euo pipefail
: "${FFDEC_JAR:?請設置 FFDEC_JAR=/path/to/ffdec.jar}"
ffdec() { java -jar "$FFDEC_JAR" "$@"; }
src=legacy/deploy
count=0
while IFS= read -r -d '' swf; do
  rel=${swf#"$src"/}
  out="legacy/decompiled/${rel%.*}"
  rm -rf "$out"
  mkdir -p "$out"
  ffdec -format sprite:png,frame:png -export script,image,shape,morphshape,sound,text,binarydata,frame,sprite "$out" "$swf"
  ffdec -swf2xml "$swf" "$out/swf.xml"
  ffdec -header "$swf" > "$out/header.txt" || echo "提示：這個版本的 FFDec 不支持 -header，幀率請從 swf.xml 的頂層屬性裡看"
  for extra in button symbolclass; do
    ffdec -export "$extra" "$out/$extra" "$swf" || echo "提示：這個版本的 FFDec 不支持導出 $extra，已跳過"
  done
  ffdec -export xfl "$out/xfl" "$swf" || echo "提示：XFL 重建失敗或不支持，已跳過（swf.xml 仍然可用）"
  echo "$swf -> $out"
  count=$((count + 1))
done < <(find "$src" -type f -iname '*.swf' -print0 | sort -z)
[ "$count" -gt 0 ] || { echo "$src 下沒有 .swf 文件：先把原部署目錄原樣放進 $src"; exit 1; }
