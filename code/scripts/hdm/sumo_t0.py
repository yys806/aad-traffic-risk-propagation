"""T0 单步服从测试：SUMO 侧执行 + 逐帧日志（规格 0.3.9 v5 §三）

只做接口验收，不产生科学结论。运行前置：
  - 网络：D:\\shen\\TJU\\AAD\\code\\networks\\hdm_recon\\hdm_recon.net.xml（6000 m 单车道，限速 60）
  - SUMO：Eclipse SUMO 1.26.0
  - 必须显式 --step-method.ballistic true、--collision.mingap-factor 0、--collision.action warn

T0 速度剖面（步 k 覆盖 [0.05k, 0.05(k+1))）：
  [0,20) 5, [20,40) 10, [40,60) 15, [60,80) 20, [80,100) 25,
  [100,350) 每步 v-0.1（-2 m/s^2）, [350,390) 恒 0
"""
import os, sys, json
SUMO_HOME = r"C:\Program Files (x86)\Eclipse\Sumo"
sys.path.insert(0, os.path.join(SUMO_HOME, "tools"))
import traci  # noqa

NET = r"D:/shen/TJU/AAD/code/networks/hdm_recon/hdm_recon.net.xml"
OUT = sys.argv[1] if len(sys.argv) > 1 else "t0_log.jsonl"
DT = 0.05
NSTEPS = 390


def target_speed(k, v_prev):
    t0 = k * DT
    if k < 20:
        return 5.0
    if k < 40:
        return 10.0
    if k < 60:
        return 15.0
    if k < 80:
        return 20.0
    if k < 100:
        return 25.0
    if k < 350:
        return max(0.0, v_prev - 0.1)
    return 0.0


def main():
    cfg = [os.path.join(SUMO_HOME, "bin", "sumo.exe"),
           "-n", NET,
           "--step-length", str(DT),
           "--step-method.ballistic", "true",
           "--collision.mingap-factor", "0",
           "--collision.action", "warn",
           "--seed", "42", "--random", "false",
           "--no-step-log", "true", "--duration-log.statistics", "false",
           "--begin", "0"]
    traci.start(cfg)
    try:
        traci.route.add("r0", ["main"])
        traci.vehicle.add("veh0", "r0", typeID="DEFAULT_VEHTYPE",
                          departPos="0", departSpeed="0", departLane="0")
        # 车辆级约束
        traci.vehicle.setSpeedMode("veh0", 0)
        traci.vehicle.setLaneChangeMode("veh0", 0)
        traci.vehicle.setMaxSpeed("veh0", 40.0)
        v_prev = 0.0
        with open(OUT, "w", encoding="utf-8") as f:
            for k in range(NSTEPS):
                x0 = traci.vehicle.getPosition("veh0")[0]
                v0 = traci.vehicle.getSpeed("veh0")
                a0 = traci.vehicle.getAcceleration("veh0")
                mode = traci.vehicle.getSpeedMode("veh0")
                allowed = traci.vehicle.getAllowedSpeed("veh0")
                vcmd = target_speed(k, v_prev)
                traci.vehicle.setSpeed("veh0", vcmd)
                traci.simulationStep()
                x1 = traci.vehicle.getPosition("veh0")[0]
                v1 = traci.vehicle.getSpeed("veh0")
                rec = dict(k=k, t=round(k * DT, 3), x_before=x0, v_before=v0, a_before=a0,
                           v_cmd=vcmd, v_after=v1, x_after=x1,
                           dv_actual=(v1 - v0) / DT, dx_actual=x1 - x0,
                           dx_ballistic=0.5 * (v0 + v1) * DT,
                           speed_mode=mode, allowed_speed=allowed)
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                v_prev = v1
    finally:
        traci.close()


if __name__ == "__main__":
    main()
