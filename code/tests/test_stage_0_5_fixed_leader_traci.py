from __future__ import annotations

import pandas as pd

from riskprop.stage_0_5_fixed_leader_traci import load_traci


def test_official_sumo_tools_binding_can_be_loaded_from_windows_install():
    traci = load_traci()
    assert hasattr(traci, "start")
