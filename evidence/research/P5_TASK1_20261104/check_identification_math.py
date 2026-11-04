"""Exact finite-population examples; no riskprop import, randomness, or traffic run.

DETERMINISTIC_IDENTIFICATION_CHECK_ONLY / SYNTHETIC_VALIDATION_ONLY.
Illustrative fractions are not scientific parameters, sample sizes, or results.
"""

from __future__ import annotations

import argparse
import json
from fractions import Fraction as F
from itertools import product
from pathlib import Path


def run_checks() -> dict:
    checks = []

    def check(name, condition, **details):
        if not condition:
            raise AssertionError(name)
        checks.append({"name": name, "status": "PASS", **details})

    def mean(values):
        return sum(values, F(0)) / len(values)

    p, tau_q, tau_nonq, tau_s0 = F(1, 4), -F(1, 5), F(1, 10), F(1, 20)
    tau_s1 = p * tau_q + (1 - p) * tau_nonq
    tau_sc = tau_s1 - tau_s0
    check("total_expectation", tau_s1 == F(1, 40), tau_s1=str(tau_s1))
    check("interaction_decomposition", tau_sc == -F(1, 40), tau_sc=str(tau_sc))
    check("qualified_effect_not_interaction", tau_q != tau_sc,
          tau_q=str(tau_q), tau_sc=str(tau_sc))
    alternatives = [p * tau_q + (1-p) * t - tau_s0 for t in [F(0), F(1, 2)]]
    check("unobserved_nonq_not_zero_by_design", alternatives[0] != alternatives[1],
          same_qualified_effect=str(tau_q), possible_interactions=list(map(str, alternatives)))

    # Potential outcomes for two equally weighted latent types.
    # Q(1) is observed only when S=1, not in source-absent cells.
    worlds = []
    for reverse in [False, True]:
        rows = []
        for q in [0, 1]:
            rows.append({"q1": q, "y00": F(1, 2),
                         "y01": F(1-q if reverse else q),
                         "y10": F(1, 2), "y11": F(1, 2)})
        observed = {
            "s0c0": sorted(str(r["y00"]) for r in rows),
            "s0c1": sorted(str(r["y01"]) for r in rows),
            "s1c0": sorted((r["q1"], str(r["y10"])) for r in rows),
            "s1c1": sorted((r["q1"], str(r["y11"])) for r in rows),
        }
        qualified = [r for r in rows if r["q1"] == 1]
        interaction = lambda group: mean([r["y11"]-r["y10"]-r["y01"]+r["y00"] for r in group])
        worlds.append({"observed": observed, "population_interaction": interaction(rows),
                       "principal_interaction": interaction(qualified),
                       "qualified_source_effect": mean([r["y11"]-r["y10"] for r in qualified])})
    check("principal_worlds_same_observed_distribution", worlds[0]["observed"] == worlds[1]["observed"])
    check("principal_worlds_same_population_interaction",
          worlds[0]["population_interaction"] == worlds[1]["population_interaction"] == 0)
    check("principal_worlds_same_qualified_effect",
          worlds[0]["qualified_source_effect"] == worlds[1]["qualified_source_effect"] == 0)
    check("principal_interaction_not_identified",
          [w["principal_interaction"] for w in worlds] == [-F(1, 2), F(1, 2)],
          possible_principal_interactions=[str(w["principal_interaction"]) for w in worlds])

    # Bound a latent conditional mean from a known marginal mean and prevalence.
    p, marginal = F(2, 5), F(7, 10)
    lower = max(F(0), (marginal - (1-p))/p)
    upper = min(F(1), marginal/p)
    outside_at_lower = (marginal-p*lower)/(1-p)
    outside_at_upper = (marginal-p*upper)/(1-p)
    check("latent_mean_bounds_feasible_and_attained",
          (lower, upper) == (F(1, 4), F(1)) and
          0 <= outside_at_lower <= 1 and 0 <= outside_at_upper <= 1,
          lower=str(lower), upper=str(upper))

    treatment = [(F(1, 5), F(2, 5)), (F(2, 5), F(3, 5))]
    control = [(F(2, 5), F(4, 5)), (F(3, 5), F(1))]
    interval = (mean([x[0] for x in treatment])-mean([x[1] for x in control]),
                mean([x[1] for x in treatment])-mean([x[0] for x in control]))
    all_effects = []
    for a, b, c, d in product(*(treatment+control)):
        all_effects.append(mean([a,b])-mean([c,d]))
    check("itt_interval_independent_endpoint_enumeration",
          interval == (min(all_effects), max(all_effects)) == (-F(3, 5), F(0)),
          lower=str(interval[0]), upper=str(interval[1]))
    cells = [(F(1,10), F(3,10)), (F(2,10), F(4,10)),
             (F(4,10), F(6,10)), (F(3,10), F(5,10))]
    lo = cells[0][0]-cells[1][1]-cells[2][1]+cells[3][0]
    hi = cells[0][1]-cells[1][0]-cells[2][0]+cells[3][1]
    combinations = [a-b-c+d for a,b,c,d in product(*cells)]
    check("four_cell_interval_endpoint_enumeration",
          (lo,hi) == (min(combinations),max(combinations)) == (-F(3,5),F(1,5)),
          lower=str(lo),upper=str(hi))
    return {"task_id": "AAD-P5-TASK1-20261104",
            "usage": "DETERMINISTIC_IDENTIFICATION_CHECK_ONLY",
            "data_status": "SYNTHETIC_VALIDATION_ONLY",
            "checks_passed": len(checks), "checks": checks,
            "new_traffic_runs": 0, "new_seeds": 0, "causal_effect_estimated": False}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = run_checks()
    serialized = json.dumps(result, ensure_ascii=True, indent=2) + "\n"
    if args.output:
        args.output.write_text(serialized, encoding="utf-8")
    print(serialized)
