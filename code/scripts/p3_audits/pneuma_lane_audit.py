"""pNEUMA 车道验收：用 OSM 路网确认「两车是否真的同车道直跟」

阶段：P3-B（结构门槛）｜ 依据：GPT 2026-11-18（gpt16.md 第 1、3 节）

问题：几何最近邻不等于同车道直接前车。弯道、路口、并道处，最近的车可能在邻道。
做法：用本地 OSM 路网（dataset/pNEUMA/osm/athens_d1_bbox_20260907.osm），
     把两车位置投影到最近道路中心线，比较横向偏移：
       横向偏移差 < 一个车道宽  → 判为同车道
       否则                     → 判为邻道（不合格）
     同时检查沿中心线的前后顺序是否与「前车在前」一致。

输出三类：确认同车道直跟 / 邻道（淘汰） / 无法判定（离所有道路都远）
"""
from __future__ import annotations

import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np

OSM = Path(r"D:\shen\TJU\AAD\dataset\pNEUMA\osm\athens_d1_bbox_20260907.osm")
EV = Path(r"D:\shen\TJU\AAD\code\outputs\analysis\P3B_pneuma\events_20s.json")
OUT = EV.parent

LANE_W = 3.25          # 雅典城市道路典型车道宽 m
MAX_ROAD_DIST = 25.0   # 离中心线超过这个距离就不当作在该路上

print("解析 OSM ...")
tree = ET.parse(OSM)
root = tree.getroot()

nodes = {}
for n in root.findall("node"):
    la, lo = n.get("lat"), n.get("lon")
    if la is None or lo is None:
        continue
    nodes[n.get("id")] = (float(la), float(lo))

ways = []
for w in root.findall("way"):
    tags = {t.get("k"): t.get("v") for t in w.findall("tag")}
    hw = tags.get("highway")
    if hw is None or hw in ("footway", "cycleway", "path", "steps", "pedestrian",
                            "construction", "proposed", "bus_stop", "platform"):
        continue
    refs = [nd.get("ref") for nd in w.findall("nd")]
    pts = [nodes[r] for r in refs if r in nodes]
    if len(pts) < 2:
        continue
    ways.append({
        "id": w.get("id"),
        "highway": hw,
        "lanes": tags.get("lanes"),
        "oneway": tags.get("oneway"),
        "pts": pts,
    })
print(f"  道路 way {len(ways):,} 条")

# 局部平面坐标（用事件点附近的参考点）
evs = json.loads(EV.read_text(encoding="utf-8"))
print(f"待验收事件 {len(evs)} 个")

# 参考点：所有事件点的均值（events_20s 里存的是局部米坐标，由 step2 用同一 lat0/lon0 生成）
# 这里需要回到经纬度，重新解析原始轨迹取 lat/lon
import csv
SRC = Path(r"D:\shen\TJU\AAD\dataset\pNEUMA\20181101_d1_0800_0830.csv")
want = {e["lead_id"] for e in evs} | {e["fol_id"] for e in evs}
traj = {}
with SRC.open("r", encoding="utf-8", errors="replace", newline="") as f:
    rd = csv.reader(f, delimiter=";")
    next(rd)
    for r in rd:
        if len(r) < 16 or r[0].strip() not in want:
            continue
        try:
            vals = np.array([float(x) for x in r[4:] if x.strip() != ""])
        except ValueError:
            continue
        n = len(vals) // 6
        v = vals[: n * 6].reshape(n, 6)
        o = np.argsort(v[:, 5])
        traj[r[0].strip()] = {"t": v[o, 5], "lat": v[o, 0], "lon": v[o, 1]}
print(f"  取到 {len(traj)} 辆相关车的经纬度轨迹")


def lonlat_to_xy(lat, lon, lat0, lon0):
    return ((lon - lon0) * 111320.0 * math.cos(math.radians(lat0)),
            (lat - lat0) * 110540.0)


def project_to_way(px, py, way, lat0, lon0):
    """把点投影到 way 折线，返回 (横向距离, 沿路里程)"""
    best = (1e18, None, None)
    acc = 0.0
    for (la1, lo1), (la2, lo2) in zip(way["pts"][:-1], way["pts"][1:]):
        x1, y1 = lonlat_to_xy(la1, lo1, lat0, lon0)
        x2, y2 = lonlat_to_xy(la2, lo2, lat0, lon0)
        dx, dy = x2 - x1, y2 - y1
        L2 = dx * dx + dy * dy
        if L2 < 1e-9:
            continue
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / L2))
        cx, cy = x1 + t * dx, y1 + t * dy
        d = math.hypot(px - cx, py - cy)
        if d < best[0]:
            best = (d, acc + t * math.sqrt(L2), way["id"])
        acc += math.sqrt(L2)
    return best


lat0 = np.mean([d["lat"].mean() for d in traj.values()])
lon0 = np.mean([d["lon"].mean() for d in traj.values()])

ok = bad_lane = bad_road = no_data = 0
detail = []
for e in evs:
    gl, gf = traj.get(e["lead_id"]), traj.get(e["fol_id"])
    if gl is None or gf is None:
        no_data += 1
        continue
    t = e["t"]
    la_l = float(np.interp(t, gl["t"], gl["lat"]))
    lo_l = float(np.interp(t, gl["t"], gl["lon"]))
    la_f = float(np.interp(t, gf["t"], gf["lat"]))
    lo_f = float(np.interp(t, gf["t"], gf["lon"]))
    xl, yl = lonlat_to_xy(la_l, lo_l, lat0, lon0)
    xf, yf = lonlat_to_xy(la_f, lo_f, lat0, lon0)

    # 找两车共同最近的 way
    cands = []
    for w in ways:
        dl, sl, _ = project_to_way(xl, yl, w, lat0, lon0)
        if dl > MAX_ROAD_DIST:
            continue
        df, sf, _ = project_to_way(xf, yf, w, lat0, lon0)
        if df > MAX_ROAD_DIST:
            continue
        cands.append((dl + df, w, dl, df, sl, sf))
    if not cands:
        bad_road += 1
        detail.append((e["lead_id"], e["fol_id"], "离路太远", None))
        continue
    cands.sort(key=lambda z: z[0])
    _, w, dl, df, sl, sf = cands[0]
    lateral_diff = abs(dl - df)
    ahead = sl > sf      # 前车沿路里程应更大
    if lateral_diff <= LANE_W and ahead:
        ok += 1
        detail.append((e["lead_id"], e["fol_id"], f"同车道（横向差 {lateral_diff:.1f} m）", w["id"]))
    elif lateral_diff > LANE_W:
        bad_lane += 1
        detail.append((e["lead_id"], e["fol_id"], f"邻道（横向差 {lateral_diff:.1f} m）", w["id"]))
    else:
        bad_road += 1
        detail.append((e["lead_id"], e["fol_id"], f"顺序不符（前车里程 {sl:.0f} < 后车 {sf:.0f}）", w["id"]))

print(f"\n=== 车道验收结果 ===")
print(f"  确认同车道直跟：{ok} 个")
print(f"  判为邻道（淘汰）：{bad_lane} 个")
print(f"  顺序不符 / 离路太远：{bad_road} 个")
print(f"  数据缺失：{no_data} 个")
print(f"  合计 {len(evs)} 个")
print(f"\n通过率 {100*ok/max(len(evs),1):.0f}%")
print("\n前 15 条明细：")
for r in detail[:15]:
    print(f"  {r[0]:>5} → {r[1]:>5}  {r[2]}")

(OUT / "lane_audit.json").write_text(
    json.dumps({"ok": ok, "bad_lane": bad_lane, "bad_road": bad_road,
                "no_data": no_data, "total": len(evs), "detail": detail},
               ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\n结果：{OUT/'lane_audit.json'}")
