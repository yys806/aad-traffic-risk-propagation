from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from riskprop.stage_0_5_fixed_leader_replay import (
    FixedLeaderReplayError,
    InMemoryLeaderSink,
    replay_trace,
    validate_trace,
)


def _trace(step: float = 0.05) -> pd.DataFrame:
    t = np.arange(0.0, 1.0 + 1e-9, step)
    return pd.DataFrame({"time_s": t, "leader_y_m": 10.0 + 12.0 * t, "leader_speed_mps": np.full_like(t, 12.0)})


def test_trace_contract_and_in_memory_readback():
    trace = _trace()
    assert validate_trace(trace)["status"] == "Verified_trace_contract"
    result = replay_trace(trace, InMemoryLeaderSink())
    assert result["status"] == "PASS_READBACK"
    assert result["max_abs_position_error_m"] == pytest.approx(0.0)


def test_trace_rejects_nonuniform_grid():
    trace = _trace()
    trace.loc[3, "time_s"] += 0.01
    with pytest.raises(FixedLeaderReplayError, match="nonuniform_trace_grid"):
        validate_trace(trace)


def test_trace_rejects_negative_speed():
    trace = _trace()
    trace.loc[2, "leader_speed_mps"] = -1.0
    with pytest.raises(FixedLeaderReplayError, match="negative_leader_speed"):
        validate_trace(trace)
