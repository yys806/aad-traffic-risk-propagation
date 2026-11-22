"""0.4.0a：事件场景 Python↔SUMO 严格对账（无噪声、单种子、逐车逐帧）

按 GPT 0.4.0 评审四条修正：
  ① 头车相位：setPreviousSpeed(v) + setSpeed(v) 复现内核 v_lead*dt（探针实测误差 2.8e-11）
  ② hist_a 写到 k+1（内核第 210 行写法），不能写 k
  ③ 统计用**步末**回读状态（内核第 213 行在 x,v 更新之后）；事件数按 i=20..99 共 80 辆另报
  ④ 全程硬门：完整性/有限值/接触/瞬移/越界，几何净距 <=0 单列接触

内核：hdm_core.py，md5 adbb11799ff89c95fe283ab32d0128aa（不重写公式，直接 import）
"""
import os, sys, json
sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/hdm")
SUMO_HOME = r"C:\Program Files (x86)\Eclipse\Sumo"
sys.path.insert(0, os.path.join(SUMO_HOME, "tools"))
import numpy as np
import hdm_core as H
import traci

NET = r"D:/shen/TJU/AAD/code/networks/hdm_recon_long/hdm_recon_long.net.xml"
VT = r"D:/shen/TJU/AAD/code/networks/hdm_recon_long/vtypes.add.xml"
DT = 0.05
N = 100
HW = 45.0
TP = 1.0
BMAX = 9.0
WARM, RAMP, OBS = 40.0, 6.0, 300.0
VTGT = 3.0
X0 = 5000.0
DRAC_TH, DRAC_MIN_DUR = 3.4, 0.2


def run_arm(v_target):
    v_eq = H.equilibrium_speed(HW)
    bt = H.beta(1); sb = np.sqrt(bt)
    s0r, Tr = H.P.s0 / sb, H.P.T / sb

    cfg = [os.path.join(SUMO_HOME, "bin", "sumo.exe"), "-n", NET, "-a", VT,
           "--step-length", str(DT), "--step-method.ballistic", "true",
           "--collision.mingap-factor", "0", "--collision.action", "warn",
           "--seed", "42", "--random", "false", "--no-step-log", "true",
           "--time-to-teleport", "-1", "--begin", "0"]
    traci.start(cfg)
    try:
        traci.route.add("r0", ["main"])
        for i in range(N):
            vid = "c%d" % i
            traci.vehicle.add(vid, "r0", typeID="CLEAN",
                              departPos=str(X0 - i * HW),
                              departSpeed=str(v_eq), departLane="0")
            traci.vehicle.setSpeedMode(vid, 0)
            traci.vehicle.setLaneChangeMode(vid, 0)
        traci.simulationStep()

        nsteps = int(round((WARM + OBS) / DT))
        n_int = int(np.floor(TP / DT)); w_frac = TP / DT - n_int
        hist_x = np.zeros((nsteps + 2, N))
        hist_v = np.zeros((nsteps + 2, N))
        hist_a = np.zeros((nsteps + 2, N))
        for i in range(N):
            hist_x[0, i] = X0 - i * HW
            hist_v[0, i] = v_eq

        log_x = np.full((nsteps + 1, N), np.nan)
        log_v = np.full((nsteps + 1, N), np.nan)
        max_drac = np.zeros(N); min_gap = np.full(N, np.inf)
        drac_run = np.zeros(N); drac_max_run = np.zeros(N)
        first_arr = np.full(N, np.nan)
        bad = dict(frames_bad=[], disappear=[], collisions=0, teleports=0,
                   out_of_bounds=0, gap_le0_frames=0, nonfinite=0)
        steps_warm = int(round(WARM / DT))
        xs = np.array([hist_x[0, i] for i in range(N)])
        vs = np.array([hist_v[0, i] for i in range(N)])

        for k in range(nsteps):
            ids = traci.vehicle.getIDList()
            if len(ids) != N:
                bad["disappear"].append(dict(k=k, n=len(ids)))
                break
            x = np.empty(N); v = np.empty(N)
            for i in range(N):
                vid = "c%d" % i
                pi = traci.vehicle.getLanePosition(vid)
                vi = traci.vehicle.getSpeed(vid)
                x[i] = pi; v[i] = vi
                if not (np.isfinite(pi) and np.isfinite(vi)):
                    bad["nonfinite"] += 1
            if bad["nonfinite"]:
                bad["frames_bad"].append(k); break
            if k == 0:
                d0 = float(np.max(np.abs(x - hist_x[0])))
                if d0 > 1e-9:
                    bad["frames_bad"].append(dict(k=0, note="initial mismatch", d=d0))
            log_x[k], log_v[k] = x, v
            hist_x[k], hist_v[k] = x, v
            if np.max(x) > 13000.0:
                bad["out_of_bounds"] += 1

            t = k * DT
            if v_target is None:
                v_lead = v_eq
            elif t < WARM:
                v_lead = v_eq
            else:
                v_lead = v_eq + (v_target - v_eq) * (min(t - WARM, RAMP) / RAMP)
            v[0] = v_lead
            new_acc = np.zeros(N)
            kd = max(k - n_int, 0); kd2 = max(k - n_int - 1, 0)
            for i in range(1, N):
                xi = (1 - w_frac) * hist_x[kd, i] + w_frac * hist_x[kd2, i]
                vi = (1 - w_frac) * hist_v[kd, i] + w_frac * hist_v[kd2, i]
                ai = (1 - w_frac) * hist_a[kd, i] + w_frac * hist_a[kd2, i]
                j = i - 1
                xj = (1 - w_frac) * hist_x[kd, j] + w_frac * hist_x[kd2, j]
                vj = (1 - w_frac) * hist_v[kd, j] + w_frac * hist_v[kd2, j]
                s = max(xj - xi - H.P.L, 0.2)
                dv = vi - vj
                s_pr = max(s - TP * dv, 0.1)
                v_pr = vi + TP * ai
                afree = H.P.a * (1.0 - (max(v_pr, 0.0) / H.P.v0) ** 4)
                aint = H.idm_acc(v_pr, s_pr, dv, s0r, Tr) - afree
                aint = max(aint, -(BMAX + afree))
                new_acc[i] = afree + aint
            new_acc = np.minimum(np.maximum(new_acc, -BMAX), H.P.a)
            v_new = np.maximum(v + new_acc * DT, 0.0)
            for i in range(N):
                vid = "c%d" % i
                traci.vehicle.setPreviousSpeed(vid, float(v[i]))
                traci.vehicle.setSpeed(vid, float(v_new[i]))
            traci.simulationStep()
            hist_a[k + 1] = new_acc

            # ---- 统计：用步末回读 ----
            for i in range(N):
                xs[i] = traci.vehicle.getLanePosition("c%d" % i)
                vs[i] = traci.vehicle.getSpeed("c%d" % i)
            if k >= steps_warm:
                for i in range(1, N):
                    gap = xs[i - 1] - xs[i] - H.P.L
                    min_gap[i] = min(min_gap[i], gap)
                    if gap <= 0:
                        bad["gap_le0_frames"] += 1
                    dvv = vs[i] - vs[i - 1]
                    dr = (dvv * dvv / (2.0 * gap)) if (gap > 0 and dvv > 0) else 0.0
                    max_drac[i] = max(max_drac[i], dr)
                    if dr >= DRAC_TH:
                        drac_run[i] += DT
                        drac_max_run[i] = max(drac_max_run[i], drac_run[i])
                    else:
                        drac_run[i] = 0.0
                    if np.isnan(first_arr[i]) and vs[i] < v_eq - 0.5:
                        first_arr[i] = (k + 1) * DT - WARM
        log_x[nsteps], log_v[nsteps] = xs, vs
        bad["collisions"] = len(traci.simulation.getCollisions())
        bad["teleports"] = traci.simulation.getStartingTeleportNumber()
        return dict(log_x=log_x, log_v=log_v, max_drac=max_drac, min_gap=min_gap,
                    event=(drac_max_run >= DRAC_MIN_DUR), arrival=first_arr,
                    bad=bad, v_eq=v_eq, nsteps=nsteps)
    finally:
        traci.close()


def main():
    out = {"config": dict(N=N, hw=HW, Tprime=TP, bmax=BMAX, warm=WARM, ramp=RAMP,
                          obs=OBS, v_target=VTGT, x0=X0, dt=DT,
                          kernel_md5="adbb11799ff89c95fe283ab32d0128aa")}
    for arm, vt in (("source", VTGT), ("control", None)):
        r = run_arm(vt)
        ref = H.run(N=N, hw=HW, n_a=1, Tprime=TP, seed=0, v_target=vt,
                    warm=WARM, observe=OBS, noise=False, bmax=BMAX, record=True)
        n = r["nsteps"]
        shift = X0 - ref["hist_x"][0, 0]
        rx = ref["hist_x"][:n + 1] + shift
        rv = ref["hist_v"][:n + 1]
        ex = np.abs(r["log_x"] - rx); ev = np.abs(r["log_v"] - rv)
        ei = np.unravel_index(np.nanargmax(ex), ex.shape)
        out[arm] = dict(
            sumo_events_all=int(r["event"][1:].sum()),
            py_events_all=int(ref["event"][1:].sum()),
            sumo_events_80=int(r["event"][20:].sum()),
            py_events_80=int(ref["event"][20:].sum()),
            sumo_peak=float(np.nanmax(r["max_drac"][1:])),
            py_peak=float(np.nanmax(ref["max_drac"][1:])),
            sumo_min_gap=float(np.min(r["min_gap"][1:])),
            py_min_gap=float(np.min(ref["min_gap"][1:])),
            max_err_x=float(np.nanmax(ex)),
            max_err_v=float(np.nanmax(ev)),
            worst_frame_car=[int(ei[0]), int(ei[1])],
            event_mismatch=int(np.sum(r["event"][1:] != ref["event"][1:])),
            frames=int(n),
            bad=r["bad"],
        )
        print(arm, json.dumps(out[arm], ensure_ascii=False), flush=True)
        np.savez_compressed("recon_040a_%s.npz" % arm,
                            log_x=r["log_x"], log_v=r["log_v"],
                            ref_x=rx, ref_v=rv,
                            max_drac=r["max_drac"], min_gap=r["min_gap"],
                            event=r["event"], arrival=r["arrival"])
    json.dump(out, open("recon_040a.json", "w"), indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
