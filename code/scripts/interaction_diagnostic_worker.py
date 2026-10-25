"""One SUMO process, fixed existing network, lane-speed supply only; run with -S.

Connection retries never relaunch SUMO. Native FCD/summary plus independent getter
counts are retained locally. Python audit scope is not an OS/native monitor.
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import socket
import subprocess
import sys


def execute(work: Path, binary: Path, tools: Path, supply_pulse: bool):
    work, binary, tools = work.resolve(), binary.resolve(), tools.resolve()
    sys.path.insert(0, str(tools))
    denied, processes = [], []
    repo = Path(__file__).resolve().parents[2]

    def audit(event, args):
        if event == "open" and isinstance(args[0], (str, bytes)):
            path = Path(args[0]).resolve()
            if path.is_relative_to(repo) and not path.is_relative_to(work) and path != Path(__file__).resolve():
                denied.append(str(path));raise PermissionError("worker_outside_capsule")
            if any(marker in str(path).lower() for marker in ["locked_holdout", "0820_0835"]):
                denied.append(str(path));raise PermissionError("worker_denied_validation")
        if event == "subprocess.Popen":
            if Path(args[0]).resolve() != binary or processes:
                raise PermissionError("only_one_fixed_SUMO_process")
            processes.append(str(binary))

    sys.addaudithook(audit)
    import traci
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0));port = listener.getsockname()[1]
    native = subprocess.Popen([str(binary), "-c", str(work / "run.sumocfg"),
                               "--remote-port", str(port), "--no-step-log", "true"])
    connection = None
    result = {"sumo_process_attempts": 1, "python_file_denials": denied,
              "isolation_limit": "Python audit only; no claim of OS/native complete monitoring"}
    try:
        traci.init(port=port, numRetries=10, proc=native, label="interaction")
        connection = traci.getConnection("interaction")
        lanes = sorted(lane for lane in connection.lane.getIDList() if lane.startswith("main_2_"))
        if len(lanes) != 5:
            raise ValueError("unexpected_existing_downstream_lanes")
        inserted = arrived = 0
        with (work / "getter_counts.csv").open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["time_s", "running", "inserted_cumulative", "arrived_cumulative", "pending", "main2_limit_min_mps", "main2_limit_max_mps"])
            writer.writeheader()
            previous = None
            for tick in range(8401):
                now = round(tick * .05, 2)
                if abs(connection.simulation.getTime() - now) > 1e-7:
                    raise ValueError("worker_clock_mismatch")
                target = 5. if supply_pulse and 180 <= now < 240 else 10.
                if target != previous:
                    for lane in lanes:
                        connection.lane.setMaxSpeed(lane, target)
                    previous = target
                if tick % 2 == 0:
                    speeds = [connection.lane.getMaxSpeed(lane) for lane in lanes]
                    if any(abs(speed - target) > 1e-9 for speed in speeds):
                        raise ValueError("supply_not_imposed")
                    writer.writerow(dict(time_s=now, running=len(connection.vehicle.getIDList()),
                        inserted_cumulative=inserted, arrived_cumulative=arrived,
                        pending=len(connection.simulation.getPendingVehicles()),
                        main2_limit_min_mps=min(speeds), main2_limit_max_mps=max(speeds)))
                if tick == 8400:
                    break
                connection.simulationStep()
                inserted += len(connection.simulation.getDepartedIDList())
                arrived += len(connection.simulation.getArrivedIDList())
                if connection.simulation.getCollidingVehiclesNumber() or connection.simulation.getStartingTeleportNumber():
                    raise ValueError("collision_or_teleport")
        result.update(status="completed", inserted=inserted, arrived=arrived, duration_s=420.)
    except BaseException as error:
        result.update(status="failed", failure=f"{type(error).__name__}:{error}")
        raise
    finally:
        if connection is not None:
            connection.close()
        try:
            result["sumo_exit_code"] = native.wait(timeout=10)
        except subprocess.TimeoutExpired:
            native.terminate();result["sumo_exit_code"] = native.wait(timeout=10)
        (work / "worker_result.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--tools", type=Path, required=True)
    parser.add_argument("--supply-pulse", action="store_true")
    args = parser.parse_args()
    parser.error("trajectory generation paused: initialization policy and frozen plan require researcher confirmation")
