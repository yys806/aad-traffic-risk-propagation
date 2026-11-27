"""AAD 0.6.0-A 空间目标区重跑（纯 Python 内核，参数化窗口）

目的：把主结局从「车号 20–99」改为「固定空间窗内的事件段数」，并与旧口径同批对照。
窗口默认 [3981.1, 5879.6] m（源车触发点 5889.56 m 上游 10 m 起、向上游 1898.5 m）。

口径（写死）：
  · 事件 = DRAC ≥ 3.4 m/s²、合并间隙 0.30 s、有效 ≥ 0.20 s 的去重段（沿用 hdm_msg.count_episodes）
  · 先在**全域**切段，再按**起始帧车头位置**归窗：窗内 / 上游溢出 / 下游溢出
  · 敏感性：仅用窗内帧切段（边界会把段切断），单独输出
  · 分析车辆：i = 1..99（排除源车 #0）；另出 20..99 旧口径便于对照

用法：
  AAD06_OBS=360 AAD06_OUT=recon_060A_400.json python run_060A_spatial.py
  AAD06_OBS=560 AAD06_OUT=recon_060A_600.json python run_060A_spatial.py
  AAD06_SEEDS=1 python run_060A_spatial.py        # 冒烟
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
OBS = float(os.environ.get("AAD06_OBS", "360.0"))
VTGT = 3.0
X0 = 5000.0
DRAC_TH = 3.4
MERGE_GAP = 0.30
LO = float(os.environ.get("AAD06_LO", "3981.1"))
HI = float(os.environ.get("AAD06_HI", "5879.6"))
SEEDS = int(os.environ.get("AAD06_SEEDS", "10"))
OUT = os.environ.get("AAD06_OUT", "recon_060A.json")
ARMS = {"A0": None, "A2": [20, 30, 40, 50, 60, 70, 80, 90], "A3": list(range(20, 100, 4))}
COMMON = dict(N=N, hw=HW, n_a=1, Tprime=TP, ramp=RAMP, warm=WARM, observe=OBS,
              noise=True, bmax=BMAX, record=True, drac_log=True, x0=X0)


def run_base(seed):
    return H.run(seed=seed, v_target=VTGT, **COMMON)


def run_msg(args):
    arm, seed, t_src, x_src, v_src = args
    msg = Message(event_id=seed, t_src=t_src, x_src=x_src, v_src=v_src,
                  receivers=ARMS[arm], t_deliver=t_src + 0.6, factor=0.70, rate=1.0)
    ms = MsgState(receivers=ARMS[arm], t_deliver=t_src + 0.6, factor=0.70, rate=1.0,
                  N=N, message=msg)
    return arm, seed, H.run(seed=seed, v_target=VTGT, msg_state=ms, **COMMON)


def segments(r, k_src, cars):
    """全域切段，返回 [(k_start, k_end, dur, x_start, car)]"""
    hx = r["hist_x"]; d = r["drac"]; out = []
    for i in cars:
        for a, b, dd in count_episodes(d[k_src:, i], DT, th=DRAC_TH, merge_gap_s=MERGE_GAP):
            k = a + k_src
            x = float(hx[min(k + 1, len(hx) - 1), i])
            out.append((int(k), int(b + k_src), float(dd), x, int(i)))
    return out


def masked_segments(r, k_src, cars):
    """敏感性：先把窗外帧的 DRAC 置 0，再切段（边界会切断事件）"""
    hx = r["hist_x"]; d = r["drac"].copy()
    mask = (hx < LO) | (hx > HI)
    d[mask] = 0.0
    out = 0
    for i in cars:
        out += len(count_episodes(d[k_src:, i], DT, th=DRAC_TH, merge_gap_s=MERGE_GAP))
    return out


def car_seconds(r, k_src, cars):
    hx = r["hist_x"]
    m = (hx[k_src:] >= LO) & (hx[k_src:] <= HI)
    return float(m[:, list(cars)].sum() * DT)


def main():
    t0 = time.time()
    steps_warm = int(round(WARM / DT))
    cars_all = list(range(1, N))          # 排除源车
    cars_legacy = list(range(20, 100))

    base = {}
    with ProcessPoolExecutor(max_workers=6) as ex:
        for seed, r in zip(range(SEEDS), ex.map(run_base, range(SEEDS))):
            base[seed] = r
            print(f"base seed{seed}", flush=True)

    # t_src 与 x_src（每个种子各自）
    meta = {}
    for s, r in base.items():
        hv = r["hist_v"]; k = int(np.where(hv[:, 0] < r["v_eq"] - 0.5)[0][0])
        meta[s] = dict(t_src=k * DT, x_src=float(r["hist_x"][k, 0]), v_src=float(hv[k, 0]), k_src=k)

    tasks = [(arm, s, meta[s]["t_src"], meta[s]["x_src"], meta[s]["v_src"])
             for arm in ("A2", "A3") for s in range(SEEDS)]
    msgs = {}
    with ProcessPoolExecutor(max_workers=6) as ex:
        for arm, seed, r in ex.map(run_msg, tasks):
            msgs[(arm, seed)] = r
            print(f"msg {arm} seed{seed}", flush=True)

    res = {"config": dict(N=N, hw=HW, Tprime=TP, bmax=BMAX, warm=WARM, ramp=RAMP,
                          obs=OBS, dt=DT, x0=X0, drac_th=DRAC_TH, merge_gap=MERGE_GAP,
                          zone=[LO, HI], arms={k: v for k, v in ARMS.items()},
                          cars="1..99 (源车除外)", legacy="20..99"),
           "meta": meta, "seeds": {}}

    def summarize(r, k_src):
        s_all = segments(r, k_src, cars_all)
        s_leg = segments(r, k_src, cars_legacy)
        in_zone = [x for x in s_all if LO <= x[3] <= HI]
        up = [x for x in s_all if x[3] > HI]
        down = [x for x in s_all if x[3] < LO]
        return dict(
            total_all=len(s_all), in_zone=len(in_zone),
            overflow_up=len(up), overflow_down=len(down),
            total_legacy=len(s_leg),
            in_zone_legacy=sum(1 for x in s_leg if LO <= x[3] <= HI),
            masked_only=masked_segments(r, k_src, cars_all),
            zone_carsec=car_seconds(r, k_src, cars_all),
            safety=r["safety"],
        )

    for s in range(SEEDS):
        k = meta[s]["k_src"]
        row = {"A0": summarize(base[s], k)}
        for arm in ("A2", "A3"):
            row[arm] = summarize(msgs[(arm, s)], k)
        res["seeds"][str(s)] = row

    # 汇总：逐种子配对差
    def agg(arm, key):
        d = [res["seeds"][str(s)][arm][key] for s in range(SEEDS)]
        base_ = [res["seeds"][str(s)]["A0"][key] for s in range(SEEDS)]
        diff = [a - b for a, b in zip(d, base_)]
        return dict(median=float(np.median(d)), range=[float(min(d)), float(max(d))],
                    diffs=diff, diff_median=float(np.median(diff)),
                    seeds_down=sum(1 for x in diff if x < 0), seeds_up=sum(1 for x in diff if x > 0))

    res["summary"] = {"A0": {k: agg("A0", k) for k in ("total_all", "in_zone", "overflow_up", "overflow_down", "total_legacy", "in_zone_legacy", "masked_only")}}
    for arm in ("A2", "A3"):
        res["summary"][arm] = {k: agg(arm, k) for k in
                               ("total_all", "in_zone", "overflow_up", "overflow_down", "total_legacy", "in_zone_legacy", "masked_only")}

    res["wall_s"] = round(time.time() - t0, 1)
    path = os.path.join(r"D:/shen/TJU/AAD/code/scripts/hdm", OUT)
    json.dump(res, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("saved", path, "wall", res["wall_s"], "s")

    for arm in ("A0", "A2", "A3"):
        sm = res["summary"][arm]
        print(arm, "in_zone med", sm["in_zone"]["median"], "total_all med", sm["total_all"]["median"])
    for arm in ("A2", "A3"):
        sm = res["summary"][arm]
        print(arm, "vs A0: in_zone diff", round(sm["in_zone"]["diff_median"], 1),
              "down/up", sm["in_zone"]["seeds_down"], sm["in_zone"]["seeds_up"],
              "| total_all diff", round(sm["total_all"]["diff_median"], 1),
              "down/up", sm["total_all"]["seeds_down"], sm["total_all"]["seeds_up"])


if __name__ == "__main__":
    main()
