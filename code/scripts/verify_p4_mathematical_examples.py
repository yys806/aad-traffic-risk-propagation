"""Independent stdlib arithmetic: no riskprop or production measurement imports."""
import argparse
from fractions import Fraction as F
import json
import math
from pathlib import Path


def verify(root):
    root=Path(root)
    def read(name): return json.loads((root/name).read_text(encoding="utf-8"))
    checks=[]
    def check(ok,label):
        if not ok: raise AssertionError(label)
        checks.append(label)
    def near(a,b): return math.isclose(a,float(b),rel_tol=1e-12,abs_tol=1e-12)
    # Hand derivation: full L=3; two proven units at .25 are absent for
    # member 2, and all three units for member 3 are unknown [0,1].
    exact=[(F(3,2),F(3,2)),(F(1,4),F(9,4)),(F(0),F(3))]
    interval=read("interval_bundle.json")["records"]
    members={x["member_id"]:x for x in interval["cohort_member"]}
    windows=interval["vehicle_window"]
    check(set(members)=={"m1","m2","m3"} and len(windows)==3,"fixed three-member roster")
    for i, (lo,hi) in enumerate(exact,1):
        w=next(x for x in windows if x["member_id"]=="m"+str(i))
        check(w["fixed_window_s"]==3,"fixed full denominator m"+str(i))
        check(near(w["lower_integral"],lo) and near(w["upper_integral"],hi),"exact integral m"+str(i))
        check(near(w["lower_mean"],lo/3) and near(w["upper_mean"],hi/3),"exact mean m"+str(i))
    regional_lo=sum(lo/3 for lo,hi in exact)/3
    regional_hi=sum(hi/3 for lo,hi in exact)/3
    check(regional_lo==F(7,36) and regional_hi==F(3,4),"hand formula 7/36 to 3/4")
    o=interval["regional_outcome"][0]
    check(near(o["lower_outcome"],regional_lo) and near(o["upper_outcome"],regional_hi),"program matches independent interval")
    point=read("point_bundle.json")["records"]["regional_outcome"][0]
    expected_point=(F(1,2)+F(1,4)+F(1,2))/3
    check(point["outcome_status"]=="POINT_IDENTIFIED" and near(point["lower_outcome"],expected_point)
        and near(point["upper_outcome"],expected_point),"complete point 5/12")
    unknown=read("unknown_scope_bundle.json")["records"]["regional_outcome"][0]
    check(unknown["outcome_status"]=="UNKNOWN_SCOPE" and unknown["lower_outcome"] is None
        and unknown["upper_outcome"] is None,"unproven complete scope has no numeric Y")
    bad=read("same_N_wrong_identity.json")
    check(bad["expected_N"]==bad["received_N"]==3 and bad["status"]=="REJECTED"
        and bad["error_code"]=="EXTRA_OR_WRONG_MEMBER","same N wrong member rejected")
    return {"usage":"SYNTHETIC_VALIDATION_ONLY","method":"independent fractions; no production imports",
        "checks_passed":len(checks),"checks_failed":0,"checks":checks,
        "exact_interval":[str(regional_lo),str(regional_hi)],"exact_point":str(expected_point),
        "causal_effect_estimated":False,"new_traffic_experiments":0}


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("examples",type=Path)
    p.add_argument("--output",type=Path)
    a=p.parse_args();result=verify(a.examples)
    content=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
    if a.output: a.output.write_text(content,encoding="utf-8")
    print(content)
