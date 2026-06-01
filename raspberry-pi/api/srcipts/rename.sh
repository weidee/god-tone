#!/bin/bash
# 批次重新命名腳本：iron 去掉類別，general 改 trash，其它類別搬到前面

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

  if [[ -e "$new" ]]; then
    echo "SKIP: $f -> $new (目標已存在)"
  else
    echo "RENAME: $f -> $new"
    mv -- "$f" "$new"
  fi
done
