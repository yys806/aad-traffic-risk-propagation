#!/bin/bash
# P2 批量（v2）：源车全程保持低速，源始终在网
# 阶段：P2 ｜ 运行目录：code/outputs/analysis/P2_batch_v2/ ｜ 脚本：run_p2_propagation.py
# 2 种子 × 2 密度 × 2 强度 = 8 格，每格一对（无事件 + 事件）

set -u
PY=/d/hermes-yan/envs/aad/Scripts/python.exe
cd /d/shen/TJU/AAD || exit 1
BASE=code/outputs/analysis/P2_batch_v2
mkdir -p "$BASE"
LOG=$BASE/batch.log
: > "$LOG"

for seed in 20261119 20261120; do
  for hw in 20 30; do
    for st in strong weak; do
      out="$BASE/hw${hw}_${st}_s${seed}"
      if [ -f "$out/result.json" ]; then
        echo "skip $out" >> "$LOG"; continue
      fi
      echo "=== start $out $(date +%H:%M:%S) ===" >> "$LOG"
      "$PY" code/scripts/run_p2_propagation.py --pair --strength "$st" \
          --headway "$hw" --seed "$seed" --sigma 0 --out "$out" >> "$LOG" 2>&1
      echo "=== done  $out rc=$? $(date +%H:%M:%S) ===" >> "$LOG"
    done
  done
done
echo "ALLDONE $(date +%H:%M:%S)" >> "$LOG"
