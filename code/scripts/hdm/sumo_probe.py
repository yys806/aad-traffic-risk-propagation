"""配置探针（不是正式实验）：在本地 SUMO 1.26.0 上实测 6 个坑到底存不存在。

依据：Gemini 0.3.9 二审意见（Test A + Test B 的合并版）。
本脚本只回答「SUMO 会怎么表现」，不产生任何科学结论。

测什么：
  P1 显式干净 vType 下，setSpeed 是否被完全服从（|读回-下发|）
  P2 位移是否为 ballistic（0.5(v_prev+v_new)dt）
  P3 跨零刹停那一帧的位移公式
  P4 净距口径：getLanePosition 差 − 车长，与 getLeader 返回值（扣 minGap）的关系
  P5 碰撞口径：gap<minGap 是否报碰撞；gap<0 是否报碰撞、是否瞬移
  P6 默认 --time-to-teleport 300 是否会把停住的车瞬移掉（用 -1 对照）
"""
import os, sys, json
SUMO_HOME = r"C:\Program Files (x86)\Eclipse\Sumo"
sys.path.insert(0, os.path.join(SUMO_HOME, "tools"))
import traci

NET = r"D:/shen/TJU/AAD/code/networks/hdm_recon/hdm_recon.net.xml"
DT = 0.05


def start(extra=()):
    cfg = [os.path.join(SUMO_HOME, "bin", "sumo.exe"), "-n", NET,
           "--step-length", str(DT),
           "--step-method.ballistic", "true",
           "--collision.mingap-factor", "0",
           "--collision.action", "warn",
           "--seed", "42", "--random", "false",
           "--no-step-log", "true", "--begin", "0"] + list(extra)
    traci.start(cfg)


def clean_type():
    """显式干净 vType：无速度偏差、无 Krauss 安全钳位影响、足够大的加减速"""
    tid = "CLEAN"
    traci.vehicletype.copy("DEFAULT_VEHTYPE", tid)
    traci.vehicletype.setLength(tid, 5.0)
    traci.vehicletype.setMinGap(tid, 2.0)
    traci.vehicletype.setSpeedFactor(tid, 1.0)
    traci.vehicletype.setSpeedDeviation(tid, 0.0)
    traci.vehicletype.setMaxSpeed(tid, 50.0)
    traci.vehicletype.setAccel(tid, 3.0)
    traci.vehicletype.setDecel(tid, 4.5)
    traci.vehicletype.setEmergencyDecel(tid, 9.0)
    traci.vehicletype.setParameter(tid, "sigma", "0.0")
    return tid


def p1_p2_p3():
    start(["--time-to-teleport", "-1"])
    try:
        tid = clean_type()
        traci.route.add("r0", ["main"])
        traci.vehicle.add("v0", "r0", typeID=tid, departPos="0", departSpeed="0", departLane="0")
        traci.vehicle.setSpeedMode("v0", 0)
        traci.vehicle.setLaneChangeMode("v0", 0)
        traci.vehicle.setMaxSpeed("v0", 50.0)
        traci.simulationStep()          # 让车真正入网
        ids = traci.vehicle.getIDList()
        rec = dict(inserted=list(ids),
                   pos0=traci.vehicle.getLanePosition("v0"),
                   v0=traci.vehicle.getSpeed("v0"))
        # 速度序列：0 -> 10 (2s) -> 30 (2s) -> -3 m/s^2 到跨零 -> 恒 0
        cmds = []
        for k in range(40):
            cmds.append(10.0)
        for k in range(40):
            cmds.append(30.0)
        v = 30.0
        while v > 0:
            v = v - 3.0 * DT
            cmds.append(max(0.0, v))
        cmds += [0.0] * 40
        errs_v, errs_x, cross = [], [], None
        vprev = traci.vehicle.getSpeed("v0")
        for k, c in enumerate(cmds):
            x0 = traci.vehicle.getLanePosition("v0"); v0 = traci.vehicle.getSpeed("v0")
            traci.vehicle.setSpeed("v0", c)
            traci.simulationStep()
            x1 = traci.vehicle.getLanePosition("v0"); v1 = traci.vehicle.getSpeed("v0")
            errs_v.append(abs(v1 - c))
            errs_x.append(abs((x1 - x0) - 0.5 * (v0 + v1) * DT))
            if cross is None and v0 > 0 and v1 == 0.0:
                cross = dict(k=k, v_before=v0, dx_actual=x1 - x0,
                             dx_ballistic=0.5 * (v0 + v1) * DT,
                             dx_stop_exact=v0 * v0 / (2 * 3.0))
            vprev = v1
        rec.update(max_err_v=max(errs_v), max_err_x=max(errs_x), zero_cross=cross)
        return rec
    finally:
        traci.close()


def p4_p5():
    start(["--time-to-teleport", "-1"])
    try:
        tid = clean_type()
        traci.route.add("r0", ["main"])
        # 前车静止在 400 m，后车从 300 m 以 10 m/s 逼近
        traci.vehicle.add("lead", "r0", typeID=tid, departPos="400", departSpeed="0", departLane="0")
        traci.vehicle.add("ego", "r0", typeID=tid, departPos="300", departSpeed="10", departLane="0")
        for v in ("lead", "ego"):
            traci.vehicle.setSpeedMode(v, 0)
            traci.vehicle.setLaneChangeMode(v, 0)
        traci.simulationStep()
        out = dict(inserted=list(traci.vehicle.getIDList()))
        gap_checks, coll = [], None
        for k in range(600):
            if "lead" not in traci.vehicle.getIDList() or "ego" not in traci.vehicle.getIDList():
                out["vanished_at"] = k; break
            lp = traci.vehicle.getLanePosition("lead"); ep = traci.vehicle.getLanePosition("ego")
            gap = lp - ep - 5.0
            leader = traci.vehicle.getLeader("ego", 1000)
            if k in (0, 100) or (gap < 2.5 and len(gap_checks) < 3):
                gap_checks.append(dict(k=k, gap_geom=gap,
                                       leader=leader,
                                       idlist=len(traci.vehicle.getIDList())))
            traci.vehicle.setSpeed("lead", 0.0)
            traci.vehicle.setSpeed("ego", 10.0)
            traci.simulationStep()
            cl = traci.simulation.getCollisions()
            if cl and coll is None:
                coll = dict(k=k, collisions=[dict(a=c.collider, b=c.victim,
                                                  type=str(c.type), lane=c.lane) for c in cl])
            if gap < -2.0:
                out["final"] = dict(k=k, gap=gap, idlist=list(traci.vehicle.getIDList()))
                break
        out.update(gap_checks=gap_checks, first_collision=coll,
                   teleports=traci.simulation.getStartingTeleportNumber())
        return out
    finally:
        traci.close()


if __name__ == "__main__":
    res = {}
    try:
        res["P1P2P3"] = p1_p2_p3()
    except Exception as e:
        res["P1P2P3"] = {"error": repr(e)}
    try:
        res["P4P5"] = p4_p5()
    except Exception as e:
        res["P4P5"] = {"error": repr(e)}
    print(json.dumps(res, ensure_ascii=False, indent=1))
