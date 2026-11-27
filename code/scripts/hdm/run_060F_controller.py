"""AAD 0.6.0-F 控制器对照（八臂，空间口径）

臂：
  C0        无事件、无控制（自由流基线）
  A0        有事件、无控制
  A2_ideal  有事件 + 8 辆早报 + 永不撤销（0.5.0 原口径锚点）
  A2_ttl60 / A2_ttl90 / A2_ttl120  同 A2，限时限速（从逐车实际送达时刻起算）
  A2_const  有事件 + 同 8 辆从 t=0 起常开 0.70 倍限速（与事件无关）
  C0_const  无事件 + 同 8 辆从 t=0 起常开 0.70 倍限速

指标：空间窗事件（窗内/上游溢出/下游溢出/全域）、延误两栏（[0,末] 与 [t_src,末]）、
最小净距、限幅帧、TTL 到期诊断（到期速度、到期后峰值）。

用法：
  AAD06F_OBS=360 AAD06F_WORKERS=2 python run_060F_controller.py
"""
import os, sys, json, time
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/hdm")
import numpy as np
import hdm_core_v2 as H
from hdm_msg import MsgState, Message, count_episodes
from concurrent.futures import ProcessPoolExecutor

DT = 0.05
N = 100
HW = 45.0
TP = 1.0
BMAX = 9.0
WARM, RAMP = 40.0, 6.0
OBS = float(os.environ.get("AAD06F_OBS", "360.0"))
VTGT = 3.0
X0 = 5000.0
DRAC_TH = 3.4
MERGE_GAP = 0.30
LO = float(os.environ.get("AAD06F_LO", "3981.1"))
HI = float(os.environ.get("AAD06F_HI", "5879.6"))
SEEDS = int(os.environ.get("AAD06F_SEEDS", "10"))
WORKERS = int(os.environ.get("AAD06F_WORKERS", "4"))
OUT = os.environ.get("AAD06F_OUT", "recon_060F.json")
RECV = [20, 30, 40, 50, 60, 70, 80, 90]
CARS = list(range(1, N))
COMMON = dict(N=N, hw=HW, n_a=1, Tprime=TP, ramp=RAMP, warm=WARM, observe=OBS,
              noise=True, bmax=BMAX, record=True, drac_log=True, x0=X0)


class ConstCap:
    """常开限速：从首次调用起把指定车辆的指令速度锁在 factor × 当时速度。"""

    def __init__(self, receivers, factor=0.70, rate=1.0, N=100):
        self.receivers = list(receivers)
        self.factor = float(factor)
        self.rate = float(rate)
        self.v_cap = np.full(N, np.nan)
        self.cap_bind_frames = np.zeros(N, dtype=int)
        self.t_action = np.full(N, np.nan)

    def apply(self, v_new, v_prev, t, dt, x=None):
        modified = np.zeros(N, dtype=bool)
        for i in self.receivers:
            if np.isnan(self.v_cap[i]):
                self.v_cap[i] = self.factor * float(v_prev[i])
                self.t_action[i] = t
                continue
            v_allowed = max(self.v_cap[i], float(v_prev[i]) - self.rate * dt)
            if v_new[i] > v_allowed + 1e-15:
                v_new[i] = v_allowed
                modified[i] = True
                self.cap_bind_frames[i] += 1
        return v_new, modified

    def summary(self):
        return dict(receivers=self.receivers, factor=self.factor, rate=self.rate,
                    cap_bind_frames={int(i): int(self.cap_bind_frames[i]) for i in self.receivers},
                    t_action={int(i): (None if np.isnan(self.t_action[i]) else float(self.t_action[i]))
                              for i in self.receivers})


def metrics(r, k0):
    hx = r["hist_x"]; d = r["drac"]; hv = r["hist_v"]; v_eq = r["v_eq"]
    segs = []
    for i in CARS:
        for a, b, dd in count_episodes(d[k0:, i], DT, th=DRAC_TH, merge_gap_s=MERGE_GAP):
            k = a + k0
            segs.append(float(hx[min(k + 1, len(hx) - 1), i]))
    segs = np.array(segs) if segs else np.array([])
    in_zone = int(np.sum((segs >= LO) & (segs <= HI))) if len(segs) else 0
    up = int(np.sum(segs > HI)) if len(segs) else 0
    down = int(np.sum(segs < LO)) if len(segs) else 0
    delay_all = float(np.sum((1.0 - hv[:, CARS] / v_eq) * DT))
    delay_post = float(np.sum((1.0 - hv[k0:, CARS] / v_eq) * DT))
    gap = hx[:-1] - hx[1:] - 4.5
    min_gap = float(np.min(gap[k0:, :-1]))
    zone_carsec = float(np.sum(((hx[k0:, CARS] >= LO) & (hx[k0:, CARS] <= HI))) * DT)
    return dict(events_total=int(len(segs)), events_in_zone=in_zone,
                overflow_up=up, overflow_down=down,
                delay_all=delay_all, delay_post=delay_post,
                min_gap=min_gap, zone_carsec=zone_carsec)


def meta_for(seed):
    r = H.run(seed=seed, v_target=VTGT, **COMMON)
    k = int(np.where(r["hist_v"][:, 0] < r["v_eq"] - 0.5)[0][0])
    return dict(seed=seed, k_src=k, t_src=k * DT,
                x_src=float(r["hist_x"][k, 0]), v_src=float(r["hist_v"][k, 0]))


def run_arm(args):
    arm, meta = args
    seed = meta["seed"]
    vt = None if arm in ("C0", "C0_const") else VTGT
    k0 = meta["k_src"] if vt is not None else int(round(WARM / DT))
    ms = None
    if arm.startswith("A2"):
        msg = Message(event_id=seed, t_src=meta["t_src"], x_src=meta["x_src"], v_src=meta["v_src"],
                      receivers=RECV, t_deliver=meta["t_src"] + 0.6, factor=0.70, rate=1.0)
        ttl = None
        if arm.startswith("A2_ttl"):
            ttl = float(arm.replace("A2_ttl", ""))
        ms = MsgState(receivers=RECV, t_deliver=meta["t_src"] + 0.6, factor=0.70, rate=1.0,
                      N=N, message=msg, ttl=ttl)
    elif arm.endswith("_const"):
        ms = ConstCap(RECV, factor=0.70, rate=1.0, N=N)
    r = H.run(seed=seed, v_target=vt, msg_state=ms, **COMMON)
    out = dict(arm=arm, seed=seed, **metrics(r, k0), safety=r["safety"], t_src=meta["t_src"])
    if ms is not None:
        out["cap"] = ms.summary()
        if hasattr(ms, "t_expire"):
            ex = {int(i): (None if np.isnan(ms.t_expire[i]) else float(ms.t_expire[i])) for i in RECV}
            out["t_expire"] = ex
            if any(v is not None for v in ex.values()):
                hv = r["hist_v"]
                out["expire_diag"] = [
                    dict(car=i, t=te,
                         v_exp=float(hv[min(int(round(te / DT)), len(hv) - 1), i]),
                         v_max_after=float(np.max(hv[min(int(round(te / DT)), len(hv) - 1):, i])))
                    for i, te in ex.items() if te is not None]
    return out


def main():
    t0 = time.time()
    arms = ["C0", "A0", "A2_ideal", "A2_ttl60", "A2_ttl90", "A2_ttl120", "A2_const", "C0_const"]
    metas = [meta_for(s) for s in range(SEEDS)]
    print("meta done", flush=True)
    tasks = [(a, m) for a in arms for m in metas]
    rows = []
    with ProcessPoolExecutor(max_workers=WORKERS) as ex:
        for out in ex.map(run_arm, tasks):
            rows.append(out)
            print(f"{out['arm']} seed{out['seed']} in_zone={out['events_in_zone']}", flush=True)

    idx = {(r_["arm"], r_["seed"]): r_ for r_ in rows}
    summ = {}
    for arm in arms:
        vals = [idx[(arm, s)] for s in range(SEEDS)]
        ref = [idx[("C0", s)] if arm == "C0_const" else idx[("A0", s)] for s in range(SEEDS)]
        d_in = [v["events_in_zone"] - b["events_in_zone"] for v, b in zip(vals, ref)]
        d_all = [v["delay_all"] - b["delay_all"] for v, b in zip(vals, ref)]
        d_post = [v["delay_post"] - b["delay_post"] for v, b in zip(vals, ref)]
        summ[arm] = dict(
            in_zone_median=float(np.median([v["events_in_zone"] for v in vals])),
            in_zone_range=[int(min(v["events_in_zone"] for v in vals)),
                           int(max(v["events_in_zone"] for v in vals))],
            total_median=float(np.median([v["events_total"] for v in vals])),
            overflow_up_median=float(np.median([v["overflow_up"] for v in vals])),
            overflow_down_median=float(np.median([v["overflow_down"] for v in vals])),
            d_in_zone_median=float(np.median(d_in)),
            d_in_zone_down=sum(1 for x in d_in if x < 0), d_in_zone_up=sum(1 for x in d_in if x > 0),
            delay_all_median=float(np.median([v["delay_all"] for v in vals])),
            delay_post_median=float(np.median([v["delay_post"] for v in vals])),
            d_delay_all_median=float(np.median(d_all)),
            d_delay_post_median=float(np.median(d_post)),
            min_gap_min=float(min(v["min_gap"] for v in vals)),
            cap_bind_median=int(np.median([sum(v.get("cap", {}).get("cap_bind_frames", {}).values())
                                           for v in vals])),
        )
    res = {"config": dict(obs=OBS, seeds=SEEDS, zone=[LO, HI], recv=RECV, cars="1..99",
                          arms=arms, workers=WORKERS),
           "meta": metas, "summary": summ, "rows": rows,
           "wall_s": round(time.time() - t0, 1)}
    path = os.path.join(r"D:/shen/TJU/AAD/code/scripts/hdm", OUT)
    json.dump(res, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved", path, "wall", res["wall_s"])
    for arm in arms:
        s = summ[arm]
        print(f"{arm:10s} in_zone={s['in_zone_median']:7.1f} d={s['d_in_zone_median']:+7.1f} "
              f"down/up={s['d_in_zone_down']}/{s['d_in_zone_up']} "
              f"delay_all={s['delay_all_median']:9.1f} dAll={s['d_delay_all_median']:+9.1f} "
              f"dPost={s['d_delay_post_median']:+9.1f} minGap={s['min_gap_min']:.3f} "
              f"capbind={s['cap_bind_median']}")


if __name__ == "__main__":
    main()
