"""生成表 1（全臂汇总，LaTeX booktabs）与配套 CSV
所有数字从 recon_050_a2s.json / recon_050_window600b.json 直接计算，不手填。
列：臂 | 接收车 | 送达时刻 | 400s 事件中位 | 相对A0 | 下降种子 | P | 600s 相对A0 | 峰值相对 | 暴露归一 | 延误差中位 | 有效限幅
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, r"D:/shen/TJU/AAD/figures/050_p3a")
from style050 import (F400, OUT, MSG_ARMS, NSEED, sign_test_p)  # noqa: E402

# 600 s 窗必须用含 A2S 的那份（旧 window600b 在 A2S 之前跑）
F600 = r"D:/shen/TJU/AAD/code/scripts/hdm/recon_050_window600c.json"

d4 = json.load(open(F400, encoding="utf-8"))
d6 = json.load(open(F600, encoding="utf-8"))

RECV_CNT = {"A1": 1, "A2": 8, "A3": 20, "A2L": 8, "A3L": 20, "A2S": 8, "A2P": 8, "A3P": 20}
# 注意：LaTeX 侧不接受 Unicode 减号 U+2212，这里统一用 ASCII 连字符，正文里再包 $...$
DELIVER = {"A1": "t+0.6", "A2": "t+0.6", "A3": "t+0.6", "A2L": "grp.+0.6",
           "A3L": "grp.+0.6", "A2S": "Tphys-8", "A2P": "Tphys+0.6", "A3P": "Tphys+0.6"}
DELIVER_TEX = {"A1": "$t+0.6$", "A2": "$t+0.6$", "A3": "$t+0.6$",
               "A2L": "grp.$+0.6$", "A3L": "grp.$+0.6$",
               "A2S": "$T_{\\mathrm{phys}}-8$",
               "A2P": "$T_{\\mathrm{phys}}+0.6$", "A3P": "$T_{\\mathrm{phys}}+0.6$"}


def ev(d, arm, key="episodes_total"):
    return np.array([d["seeds"][str(s)]["arms"][arm][key] for s in range(NSEED)], float)


def capsum(d, arm):
    return int(sum(sum(d["seeds"][str(s)]["arms"][arm]["msg"]["cap_bind_frames"].values())
                   for s in range(NSEED)))


base4 = ev(d4, "A0"); base6 = ev(d6, "A0")
capA0_ref = capsum(d4, "A2")

rows = []
for arm in MSG_ARMS:
    a4 = ev(d4, arm); dif4 = a4 - base4
    a6 = ev(d6, arm); dif6 = a6 - base6
    p = sign_test_p(dif4)
    rows.append(dict(
        arm=arm, nrecv=RECV_CNT[arm], deliver=DELIVER[arm],
        med400=float(np.median(a4)),
        rel400=float(np.median(dif4) / np.median(base4)),
        down=int((dif4 < 0).sum()), p=p,
        rel600=float(np.median(dif6) / np.median(base6)),
        peak=float(d4["summary"][arm]["peak_rel"]),
        rate=float(d4["summary"][arm]["rate_rel"]),
        delay=float(d4["summary"][arm]["delay_diff_median"]),
        cap=capsum(d4, arm),
        # 每辆接收车每种子的平均限幅帧数——跨臂可比的唯一口径
        cap_per=int(round(capsum(d4, arm) / (RECV_CNT[arm] * NSEED))),
        cap_pct=capsum(d4, arm) / capA0_ref * 100,
        # 质量状态：未闭合事件段（跨窗被截断）与接触数，逐种子清点
        open_tail=sum(int(d4["seeds"][str(s)]["arms"][arm]["open_tail_segments"])
                      for s in range(NSEED)),
        contact=sum(int(d4["seeds"][str(s)]["arms"][arm]["contact"]) for s in range(NSEED)),
    ))

# ---------- CSV ----------
os.makedirs(OUT, exist_ok=True)
csv = os.path.join(OUT, "table1_all_arms.csv")
with open(csv, "w", encoding="utf-8") as f:
    f.write("arm,n_receivers,delivery,events_400s_median,rel_A0_400s,seeds_lower,sign_test_P,"
            "rel_A0_600s,peak_rel,exposure_rate_rel,delay_diff_median,"
            "capping_frames_total,capping_frames_per_receiver_per_seed,capping_pct_of_A2,"
            "open_tail_segments,contacts\n")
    f.write(f"A0,0,-,{np.median(base4):.1f},0.000,0,1.000,0.000,0.000,0.000,0.00,0,0,0.00,0,0\n")
    for r in rows:
        f.write(f"{r['arm']},{r['nrecv']},{DELIVER[r['arm']]},{r['med400']:.1f},{r['rel400']:.4f},"
                f"{r['down']},{r['p']:.4f},{r['rel600']:.4f},{r['peak']:.4f},{r['rate']:.4f},"
                f"{r['delay']:.2f},{r['cap']},{r['cap_per']},{r['cap_pct']:.2f},"
                f"{r['open_tail']},{r['contact']}\n")
print("saved", csv)

# ---------- 表注里引用的实测区间（从 JSON 算，不手写） ----------
def _vcap_range(d, arm):
    v = []
    for s in range(NSEED):
        t = d["seeds"][str(s)]["arms"][arm]["trace"].get("v_cap") or {}
        v += [x for x in t.values() if x is not None]
    return min(v), max(v)


def _lead_set(d, arm):
    out = set()
    for s in range(NSEED):
        m = d["seeds"][str(s)]["arms"][arm]["msg"]
        for i, t in (m.get("t_deliver_per_car") or {}).items():
            if t is None:
                continue
            a = (m.get("action") or {}).get(i)
            if not a or a.get("t_action") is None or a.get("lead") is None:
                continue
            out.add(round(a["t_action"] + a["lead"] - t, 2))
    return out


_lo_p, _hi_p = _vcap_range(d4, "A2P")
_lo_e, _hi_e = _vcap_range(d4, "A2")
VC_P = f"{_lo_p:.2f}--{_hi_p:.2f}\\,m\\,s$^{{-1}}$"
VC_EARLY = f"{_lo_e:.2f}--{_hi_e:.2f}\\,m\\,s$^{{-1}}$"
VC_LEAD = "%.2f" % sorted(_lead_set(d4, "A2P"))[0]   # 纯数字，反斜杠由模板给
assert len(_lead_set(d4, "A2P")) == 1, "A2P 提前量应只有一个值"

# ---------- LaTeX ----------
tex = os.path.join(OUT, "table1_all_arms.tex")
with open(tex, "w", encoding="utf-8") as f:
    f.write(r"""\begin{table}[t]
\centering
\caption{All experimental arms in the single-lane message pilot (10 noise-paired seeds of one
deterministic source event). Events are the number of de-duplicated intervals in which the
required deceleration exceeds 3.4~m\,s$^{-2}$ for the 80 vehicles of the target zone.
$P$ is a two-sided exact sign test over the 10 noise seeds within this single source event;
it is not a cross-event statistic. Percentages are relative to the median paired change; in the
600\,s window the raw medians of A2 and A3 are 115.5 and 119.0 events, i.e.\ the 20-receiver arm is
not strictly better than the 8-receiver arm (dose inversion), although A3 is lower in 7/10 seeds. Delivery: $t+0.6$ = broadcast 0.6\,s after source detection;
grp.+0.6 = whole-group broadcast at the \emph{earliest} receiver's wave-arrival time plus 0.6\,s;
$T_{\mathrm{phys}}-8$ = per-vehicle delivery 8\,s before its own wave arrival;
$T_{\mathrm{phys}}+0.6$ = per-vehicle delivery 0.6\,s after its own wave arrival
(i.e.\ a delivery lead time of {VC_LEAD}\,s, so the physical wave has already passed and the frozen
speed cap is set from a lower speed: {VC_P} versus {VC_EARLY} for the early-broadcast arms).
Delay is the median paired difference, relative to A0, in the cumulative speed deficit
$\int (v_{\mathrm{free}} - v)\,\mathrm{d}t$ summed over the 80 target-zone vehicles,
in vehicle-seconds; it is not a stopped-vehicle waiting time.
Quality is the number of event intervals still open at the last simulated frame, summed over the
10 seeds; contacts are vehicle--vehicle collisions. Capping is the mean number of frames in which
the local speed cap is the binding constraint, per receiver and per seed.}
\label{tab:all_arms}
\footnotesize
\setlength{\tabcolsep}{2.6pt}

\resizebox{\columnwidth}{!}{%
\begin{tabular}{lcccccccccccc}
\toprule
Arm & $n_{\mathrm{recv}}$ & Delivery & Events & vs A0 & Lower & $P$ & vs A0 & Peak & Exposure & Delay & Capping & Quality \\
 & & & (400\,s) & (400\,s) & seeds & & (600\,s) & & norm. & veh$\cdot$s & frames/veh./seed & \\
\midrule
""")
    out_row = "A0 & 0 & --- & %.1f & --- & --- & --- & --- & --- & --- & --- & --- & --- " % np.median(base4)
    f.write(out_row + "\\\\" + chr(10))
    f.write("\\midrule\n")
    for r in rows:
        f.write(f"{r['arm']} & {r['nrecv']} & {DELIVER_TEX[r['arm']]} & {r['med400']:.1f} & "
                f"{r['rel400']*100:+.2f}\\% & {r['down']}/10 & {r['p']:.3f} & "
                f"{r['rel600']*100:+.2f}\\% & {r['peak']*100:+.2f}\\% & "
                f"{r['rate']*100:+.2f}\% & {r['delay']:+.2f} & {r['cap_per']:,} & "
                f"{'---' if r['open_tail']==0 else str(r['open_tail'])+' open'} \\\\\n")
    f.write(r"""\bottomrule
\end{tabular}}
\end{table}
""")
# 表注是 raw string，f-string 不生效 → 显式替换占位符
_t = open(tex, encoding="utf-8").read()
_t = (_t.replace("{VC_LEAD}", VC_LEAD).replace("{VC_P}", VC_P)
         .replace("{VC_EARLY}", VC_EARLY))
assert "{" + "VC_" not in _t, "表注占位符未替换"
open(tex, "w", encoding="utf-8").write(_t)
print("saved", tex)
print(json.dumps(rows, ensure_ascii=False, indent=1)[:800])