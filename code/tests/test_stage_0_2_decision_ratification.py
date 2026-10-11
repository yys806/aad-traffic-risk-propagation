import sys
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from run_stage_0_2_decision_ratification import contribution, burden, effect_interval, weighted_median

def test_status_and_region_bounds():
 assert contribution("valid",True,True,2,2)==pytest.approx((0.36787944117,)*2)
 assert contribution("not_applicable",True,True,None,2)==(0,0)
 assert contribution("invalid",True,True,None,2)==(0,1)
 assert contribution("valid",False,True,2,2)==(0,0)
 assert contribution("valid",None,True,2,2)==(0,1)
 assert contribution("not_applicable",True,False,None,2)==(0,1)

def test_fixed_denominator_and_equal_vehicle_weight():
 assert burden([[(1,0,0)],[(1,1,1)]],2)==(.25,.75)
 assert burden([[],[]],2)==(0,1)

def test_interval_did():
 assert effect_interval((1,2),(3,4),(5,6),(7,8))==(-2,2)

def test_weighted_median():
 assert weighted_median([1,3,9],[1,8,1])==3
