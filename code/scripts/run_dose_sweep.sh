#!/usr/bin/env bash
# Dose sweep for the path-3 response.
#
# Each level scales the content-graded peak and the blanket sham dose by the SAME factor, so
# every level remains a dose-matched comparison between content and no-content. Only the dose
# changes across levels.
#
# Baseline (scale=1.0): peak HIGH = 1.2 s, sham = 0.43 s.
set -u
cd /d/shen/TJU/AAD || exit 1
PY=D:/hermes-yan/envs/aad/Scripts/python.exe
OUT=code/outputs/analysis/stage1_path3_dose_sweep_20261117

rm -rf "$OUT"
mkdir -p "$OUT"

for spec in "0.083:0.10:0.036" "0.25:0.30:0.107" "0.583:0.70:0.250" "1.0:1.20:0.430" "1.667:2.00:0.717"; do
    scale=$(echo "$spec" | cut -d: -f1)
    peak=$(echo "$spec" | cut -d: -f2)
    sham=$(echo "$spec" | cut -d: -f3)
    tag="peak${peak}"
    echo "=== level peak=${peak}s scale=${scale} sham=${sham}s ==="
    timeout 1700 "$PY" code/scripts/run_stage1_path3.py \
        --seeds 2 --risk-mode braking --response headway \
        --peak-scale "$scale" --sham-delta "$sham" \
        --out "$OUT/$tag" > "/tmp/dose_${tag}.log" 2>&1
    echo "exit=$? for $tag"
    grep -E "相对 sham|Δ\(opn1-sham\)|Δ\(sham-opn0\)" "/tmp/dose_${tag}.log" | tail -3
done
echo "ALL DONE"