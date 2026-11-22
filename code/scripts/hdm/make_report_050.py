"""0.5.0 报表数字生成器：所有对外数字一律从这里出，禁止手抄。

背景（Gemini 第三轮审计）：结果档 v3 的 §5.2/§5.3/§5.4 数字全是改时钟前手抄的旧值，
与当前 JSON 不一致。根治办法是让报表数字由脚本从 JSON 直接生成。

用法：
  D:/miniconda/python.exe make_report_050.py            # 读 recon_050.json（400 s）
  AAD050_OUT=recon_050_window600b.json ... make_report_050.py
输出：
  report_050.md    人类可读
  report_050.json  机读
"""
import os
import json
import numpy as np
import sys

sys.path.insert(0, r"D:/shen/TJU/AAD/code/scripts/hdm")
from hdm_msg import count_episodes

BASE = r"D:/shen/TJU/AAD/code/scripts/hdm/"
F400 = os.environ.get("AAD050_OUT", "recon_050.json")
F600 = "recon_050_window600b.json"
DT, DRAC_TH, ZONE = 0.05, 3.4, list(range(20, 100))
MSG_ARMS = ("A1", "A2", "A3", "A2L", "A3L", "A2P", "A3P")


def load(fn):
    p = BASE + fn
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else None


def arm_series(d, arm, key):
    return np.array([d["seeds"][str(s)]["arms"][arm][key] for s in range(10)], dtype=float)


def paired(d, arm, key="episodes_total"):
    b = arm_series(d, "A0", key)
    a = arm_series(d, arm, key)
    return a, b, a - b


def sign_test_p(diffs):
    """双侧符号检验 p（n<=10 精确二项）。"""
    d = np.asarray([x for x in diffs if x != 0], dtype=float)
    n = len(d)
    if n == 0:
        return 1.0
    k = int(min((d < 0).sum(), (d > 0).sum()))
    from math import comb
    p = sum(comb(n, i) for i in range(k + 1)) / 2 ** n * 2
    return min(1.0, p)


def summarize(d, tag):
    out = {"window": tag, "A0": dict(median=float(d["A0"]["median"]),
                                      range=d["A0"]["range"]), "arms": {}, "pairs": {}}
    have = set(d["seeds"]["0"]["arms"].keys())
    for arm in MSG_ARMS:
        if arm not in have:
            continue
        a, b, diff = paired(d, arm)
        s = d["summary"][arm]
        out["arms"][arm] = dict(
            median=float(np.median(a)), range=[float(a.min()), float(a.max())],
            diff_median=float(np.median(diff)), rel=float(np.median(diff) / np.median(b)),
            seeds_down=int((diff < 0).sum()), seeds_up=int((diff > 0).sum()),
            sign_p=sign_test_p(diff),
            peak_rel=float(s["peak_rel"]), rate_rel=float(s["rate_rel"]),
            delay_diff_median=float(s["delay_diff_median"]))
    for early, late in (("A2", "A2L"), ("A3", "A3L"), ("A2", "A2P"), ("A3", "A3P")):
        if early in out["arms"] and late in out["arms"] and late in have:
            e = arm_series(d, early, "episodes_total"); l = arm_series(d, late, "episodes_total")
            dd = e - l
            out["pairs"][f"{early}_vs_{late}"] = dict(
                early_median=float(np.median(e)), late_median=float(np.median(l)),
                early_minus_late_median=float(np.median(dd)),
                diffs=[int(x) for x in dd],
                early_better=int((dd < 0).sum()), late_better=int((dd > 0).sum()),
                sign_p=sign_test_p(dd))
    return out


def main():
    d4 = load(F400)
    if d4 is None:
        print("缺少", F400); sys.exit(1)
    d6 = load(F600)
    rep = {"source": F400, "t400": summarize(d4, "400s"),
           "gates": d4["gates"], "n_fail": len(d4["gates"]["fails"])}
    if d6:
        rep["t600"] = summarize(d6, "600s")

    # 分区（前 20–59 / 后 60–99）
    parts = {}
    for arm in [x for x in ("A2", "A3", "A2L", "A3L", "A2P", "A3P")
                if x in d4["seeds"]["0"]["arms"]]:
        lo = arm_series(d4, arm, "episodes_lowhalf"); lo0 = arm_series(d4, "A0", "episodes_lowhalf")
        hi = arm_series(d4, arm, "episodes_highhalf"); hi0 = arm_series(d4, "A0", "episodes_highhalf")
        parts[arm] = dict(low_diff_median=float(np.median(lo - lo0)),
                          low_seeds_down=int(((lo - lo0) < 0).sum()),
                          high_diff_median=float(np.median(hi - hi0)),
                          high_seeds_down=int(((hi - hi0) < 0).sum()))
    rep["halves"] = parts

    # 最小净距与延误最坏值
    worst = {}
    for arm in [x for x in ("A0",) + MSG_ARMS if x in d4["seeds"]["0"]["arms"]]:
        mg = arm_series(d4, arm, "min_gap")
        worst[arm] = dict(min_gap_worst=float(mg.min()), min_gap_argmin=int(mg.argmin()))
    rep["min_gap"] = worst
    dly = {}
    for arm in [x for x in MSG_ARMS if x in d4["seeds"]["0"]["arms"]]:
        _, _, dd = paired(d4, arm, "delay")
        dly[arm] = dict(max_increase=float(dd.max()), seeds_up=int((dd > 0).sum()),
                        diff_median=float(np.median(dd)))
    rep["delay"] = dly

    # 接收 vs 非接收（标明是低速车·秒归一率）
    split = {}
    for arm in [x for x in ("A2", "A3", "A2L", "A3L", "A2P", "A3P")
                if x in d4["seeds"]["0"]["arms"]]:
        # A0 的基线只有 recv_A2/nonrecv_A2 与 recv_A3/nonrecv_A3；
        # A2L/A2P 的接收车集合与 A2 相同，可直接复用
        base_k = "A2" if arm.startswith("A2") else "A3"
        for label, own_key, base_key in (("recv", "recv", f"recv_{base_k}"),
                                         ("nonrecv", "nonrecv", f"nonrecv_{base_k}")):
            r0 = np.array([d4["seeds"][str(x)]["arms"]["A0"]["split"][base_key]["rate"]
                           for x in range(10)], dtype=float)
            r1 = np.array([d4["seeds"][str(x)]["arms"][arm]["split"][own_key]["rate"]
                           for x in range(10)], dtype=float)
            dd = r1 - r0
            split[f"{arm}_{label}"] = dict(
                rel_rate=float(np.median(dd) / np.median(r0)) if np.median(r0) else 0.0,
                seeds_down=int((dd < 0).sum()))
    rep["split_rate"] = split

    json.dump(rep, open(BASE + "report_050.json", "w"), indent=1, ensure_ascii=False)

    L = [f"# 0.5.0 报表自动生成（源 {F400}）", "",
         f"硬门：{rep['gates']['ok']}｜失败 {rep['n_fail']} 项 {rep['gates']['fails']}", "",
         f"## 400 s 窗（A0 中位 {rep['t400']['A0']['median']}）", "",
         "| 臂 | 事件中位 | 相对A0 | 降/升 | 符号检验p | 峰值相对 | 暴露归一 | 延误差中位 |",
         "|---|---|---|---|---|---|---|---|"]
    for arm, v in rep["t400"]["arms"].items():
        L.append(f"| {arm} | {v['median']:.1f} | {v['rel']*100:+.2f}% | "
                 f"{v['seeds_down']}/{v['seeds_up']} | {v['sign_p']:.4f} | "
                 f"{v['peak_rel']*100:+.2f}% | {v['rate_rel']*100:+.2f}% | {v['delay_diff_median']:+.2f} |")
    L += ["", "## 早 vs 晚 配对", ""]
    for k, v in rep["t400"]["pairs"].items():
        L.append(f"- {k}: 早 {v['early_median']:.1f} vs 晚 {v['late_median']:.1f}，"
                 f"差 {v['early_minus_late_median']:+.1f}，早更好 {v['early_better']}/10，"
                 f"符号检验 p={v['sign_p']:.4f}，逐种子 {v['diffs']}")
    if "t600" in rep:
        L += ["", f"## 600 s 窗（A0 中位 {rep['t600']['A0']['median']}）", "",
              "| 臂 | 事件中位 | 相对A0 | 降/升 | 符号检验p |", "|---|---|---|---|---|"]
        for arm, v in rep["t600"]["arms"].items():
            L.append(f"| {arm} | {v['median']:.1f} | {v['rel']*100:+.2f}% | "
                     f"{v['seeds_down']}/{v['seeds_up']} | {v['sign_p']:.4f} |")
        L += ["", "## 600 s 早 vs 晚", ""]
        for k, v in rep["t600"]["pairs"].items():
            L.append(f"- {k}: 差 {v['early_minus_late_median']:+.1f}，"
                     f"早更好 {v['early_better']}/10，p={v['sign_p']:.4f}")
    L += ["", "## 分区（前 20–59 / 后 60–99）", "",
          "| 臂 | 前半差中位 | 前半降 | 后半差中位 | 后半降 |", "|---|---|---|---|---|"]
    for arm, v in rep["halves"].items():
        L.append(f"| {arm} | {v['low_diff_median']:+.1f} | {v['low_seeds_down']}/10 | "
                 f"{v['high_diff_median']:+.1f} | {v['high_seeds_down']}/10 |")
    L += ["", "## 最小净距最坏值", ""]
    for arm, v in rep["min_gap"].items():
        L.append(f"- {arm}: {v['min_gap_worst']:.4f} m（seed {v['min_gap_argmin']}）")
    L += ["", "## 延误（相对 A0，车·秒）", ""]
    for arm, v in rep["delay"].items():
        L.append(f"- {arm}: 最大上升 {v['max_increase']:+.2f}，升 {v['seeds_up']}/10，"
                 f"配对差中位 {v['diff_median']:+.2f}")
    L += ["", "## 接收 vs 非接收（低速车·秒归一率，标注：不是原始段数）", ""]
    for k, v in rep["split_rate"].items():
        L.append(f"- {k}: {v['rel_rate']*100:+.2f}%（降 {v['seeds_down']}/10）")

    txt = "\n".join(L)
    open(BASE + "report_050.md", "w", encoding="utf-8").write(txt)
    print(txt)


if __name__ == "__main__":
    main()
