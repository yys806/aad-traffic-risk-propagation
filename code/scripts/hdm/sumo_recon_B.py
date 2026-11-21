"""测试 B：净距与碰撞边界（0.3.9 v9 §三，B1/B2/B3 三段）

B1 几何净距 ≥ minGap 时，getLeader 返回值 = 几何净距 − 2.0
B2 几何净距 < minGap 时，getLeader 返回 0，且 mingap-factor 0 下不报碰撞
B3 几何净距 < 0 时报碰撞 1 次，两车仍在 getIDList，teleported == []

固定处置：--collision.mingap-factor 0 --collision.action warn --time-to-teleport -1
"""
import os, sys, json
SUMO_HOME = r"C:\Program Files (x86)\Eclipse\Sumo"
sys.path.insert(0, os.path.join(SUMO_HOME, "tools"))
import traci

NET = r"D:/shen/TJU/AAD/code/networks/hdm_recon/hdm_recon.net.xml"
VT = r"D:/shen/TJU/AAD/code/networks/hdm_recon/vtypes.add.xml"
DT = 0.05
L = 5.0
MINGAP = 2.0


def run():
    cfg = [os.path.join(SUMO_HOME, "bin", "sumo.exe"), "-n", NET, "-a", VT,
           "--step-length", str(DT), "--step-method.ballistic", "true",
           "--collision.mingap-factor", "0", "--collision.action", "warn",
           "--seed", "42", "--random", "false", "--no-step-log", "true",
           "--time-to-teleport", "-1", "--begin", "0"]
    traci.start(cfg)
    try:
        traci.route.add("r0", ["main"])
        # 前车静止在 400；后车从 300 以 10 m/s 逼近
        traci.vehicle.add("lead", "r0", typeID="CLEAN", departPos="400", departSpeed="0", departLane="0")
        traci.vehicle.add("ego", "r0", typeID="CLEAN", departPos="300", departSpeed="10", departLane="0")
        for v in ("lead", "ego"):
            traci.vehicle.setSpeedMode(v, 0)
            traci.vehicle.setLaneChangeMode(v, 0)
        traci.simulationStep()

        b1, b2, b3 = [], [], []
        coll_seen = 0
        for k in range(900):
            ids = traci.vehicle.getIDList()
            if len(ids) != 2:
                return dict(error="vehicle vanished at k=%d ids=%s" % (k, list(ids)))
            lp = traci.vehicle.getLanePosition("lead")
            ep = traci.vehicle.getLanePosition("ego")
            gap = lp - ep - L
            leader = traci.vehicle.getLeader("ego", 1000)
            lead_dist = leader[1] if leader else None

            if gap >= MINGAP:
                expect = gap - MINGAP
                if lead_dist is None or abs(lead_dist - expect) > 1e-6:
                    b1.append(dict(k=k, gap=gap, got=lead_dist, expect=expect))
                elif len(b1) == 0 and k % 200 == 0:
                    b1.append(dict(k=k, gap=gap, got=lead_dist, expect=expect, ok=True))
            elif gap > 0:
                if lead_dist is not None and abs(lead_dist) > 1e-6:
                    b2.append(dict(k=k, gap=gap, got=lead_dist))
                if traci.simulation.getCollisionCount() if hasattr(traci.simulation, "getCollisionCount") else 0:
                    b2.append(dict(k=k, note="collision in 0<gap<minGap", gap=gap))
            else:
                cl = traci.simulation.getCollisions()
                if cl:
                    coll_seen += len(cl)
                if k == 0:
                    pass
                if len(b3) < 3:
                    b3.append(dict(k=k, gap=gap, collisions=len(cl), n_ids=len(ids)))

            traci.vehicle.setSpeed("lead", 0.0)
            traci.vehicle.setSpeed("ego", 10.0)
            traci.simulationStep()
            if gap < -5.0:
                break
        return dict(B1_failures=b1[:5], B1_note="空=全通过",
                    B2_failures=b2[:5], B2_note="空=全通过",
                    B3_samples=b3, collisions_total=coll_seen,
                    final_ids=list(traci.vehicle.getIDList()),
                    teleports=traci.simulation.getStartingTeleportNumber())
    finally:
        traci.close()


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=1))
