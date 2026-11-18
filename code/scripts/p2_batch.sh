#!/bin/bash
# P2 批量：种子 × 密度 × 强度
# 阶段：P2 ｜ 运行目录：code/outputs/analysis/P2_batch/ ｜ 脚本：run_p2_propagation.py
#
# 每格 = 一对（无事件 + 事件）。plain 臂在同 (seed, headway) 下会被重复跑一次，
# 换来的是逻辑简单、不会因为复用文件而串数据。8 格约 20 分钟。

set -u
PY=/d/hermes-yan/envs/aad/Scripts/python.exe
cd /d/shen/TJU/AAD || exit 1
mkdir -p code/outputs/analysis/P2_batch
LOG=code/outputs/analysis/P2_batch/batch.log
: > "$LOG"

for seed in 20261119 20261120; do
  for hw in 20 30; do
    for st in strong weak; do
      out="code/outputs/analysis/P2_batch/hw${hw}_${st}_s${seed}"
      if [ -f "$out/result.json" ]; then
        echo "skip $out (exists)" >> "$LOG"
        continue
      fi
      echo "=== start $out $(date +%H:%M:%S) ===" >> "$LOG"
      "$PY" code/scripts/run_p2_propagation.py --pair --strength "$st" \
          --headway "$hw" --seed "$seed" --sigma 0 --out "$out" >> "$LOG" 2>&1
      echo "=== done  $out rc=$? $(date +%H:%M:%S) ===" >> "$LOG"
    done
  done
done
echo "ALLDONE $(date +%H:%M:%S)" >> "$LOG"
