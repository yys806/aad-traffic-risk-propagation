"""补充探针：跨零那一帧的位移公式 + setSpeed 粘性（Gemini 坑 5 / 坑 6）"""
import os, sys, json
SUMO_HOME = r"C:\Program Files (x86)\Eclipse\Sumo"
sys.path.insert(0, os.path.join(SUMO_HOME, "tools"))
import traci

NET = r"D:/shen/TJU/AAD/code/networks/hdm_recon/hdm_recon.net.xml"
DT = 0.05

cfg = [os.path.join(SUMO_HOME, "bin", "sumo.exe"), "-n", NET,
       "--step-length", str(DT), "--step-method.ballistic", "true",
       "--collision.mingap-factor", "0", "--collision.action", "warn",
       "--seed", "42", "--random", "false", "--no-step-log", "true",
       "--time-to-teleport", "-1", "--begin", "0"]
traci.start(cfg)
try:
    traci.vehicletype.copy("DEFAULT_VEHTYPE", "CLEAN")
    for k, v in (("length", 5.0), ("minGap", 2.0), ("maxSpeed", 50.0),
                 ("accel", 3.0), ("decel", 4.5), ("emergencyDecel", 9.0),
                 ("speedFactor", 1.0), ("speedDev", 0.0)):
        traci.vehicletype.setParameter("CLEAN", k, str(v))
    traci.route.add("r0", ["main"])
    traci.vehicle.add("v0", "r0", typeID="CLEAN", departPos="0", departSpeed="0", departLane="0")
    traci.vehicle.setSpeedMode("v0", 0)
    traci.vehicle.setLaneChangeMode("v0", 0)
    traci.simulationStep()

    out = {}
    # 1) 推到 0.2 m/s，然后一条指令归零 —— 真正的跨零步
    for _ in range(20):
        traci.vehicle.setSpeed("v0", 0.2); traci.simulationStep()
    x0 = traci.vehicle.getLanePosition("v0"); v0 = traci.vehicle.getSpeed("v0")
    traci.vehicle.setSpeed("v0", 0.0); traci.simulationStep()
    x1 = traci.vehicle.getLanePosition("v0"); v1 = traci.vehicle.getSpeed("v0")
    out["cross"] = dict(v_before=v0, v_after=v1, dx=x1 - x0,
                        dx_ballistic=0.5 * (v0 + v1) * DT,
                        dx_vold=v0 * DT)
    # 2) 极小速度是否被内部归零
    traci.vehicle.setSpeed("v0", 0.0005); traci.simulationStep()
    out["tiny"] = dict(v_after=traci.vehicle.getSpeed("v0"))
    # 3) setSpeed 粘性：设 5 m/s 后不再下发，看是否保持
    traci.vehicle.setSpeed("v0", 5.0)
    for _ in range(10):
        traci.simulationStep()
    out["sticky"] = dict(v_after_10_steps=traci.vehicle.getSpeed("v0"))
    print(json.dumps(out, ensure_ascii=False, indent=1))
finally:
    traci.close()
