#!/bin/bash
# 預覽批次改名，不會真的動檔案

for f in matal_*_*_*.py; do
  [[ -f "$f" ]] || continue
  base="${f%.py}"
  IFS='_' read -r prefix r c cls <<<"$base"

  # 類別映射
  mapcls="$cls"
  [[ "$cls" == "general" ]] && mapcls="trash"

  # iron 特例：去掉類別
  if [[ "$cls" == "iron" ]]; then
    new="matal_${r}_${c}.py"
  else
    new="${mapcls}_${r}_${c}.py"
  fi

  printf "%-28s -> %s\n" "$f" "$new"
done
