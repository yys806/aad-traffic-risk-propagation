import json
import shutil
from pathlib import Path

import pandas as pd
import pytest

from riskprop.stage_0_1_sumo import (
    analyze_physical_path_from_archived_tables,
    analyze_real_sumo_stage_0_1,
    run_real_sumo_stage_0_1,
)


def _topology() -> dict[str, object]:
    return {
        "schema_version": "stage_0_1.topology.v1",
        "directed_edges": [
            {"edge_id": "src", "from_node": "a", "to_node": "b"},
            {"edge_id": "tgt", "from_node": "c", "to_node": "d"},
        ],
    }


def test_archived_time_expanded_path_audit_does_not_infer_a_path_across_disconnected_corridors():
    state = pd.DataFrame(
        [
            {"time_s": 0.0, "vehicle_id": "source_0", "edge_id": "src", "leader_id": None},
            {"time_s": 1.0, "vehicle_id": "source_0", "edge_id": "src", "leader_id": None},
            {"time_s": 0.0, "vehicle_id": "target_0", "edge_id": "tgt", "leader_id": None},
            {"time_s": 1.0, "vehicle_id": "target_0", "edge_id": "tgt", "leader_id": None},
        ]
    )

    result = analyze_physical_path_from_archived_tables(
        state, _topology(), source_vehicle_id="source_0", target_vehicle_id="target_0"
    )

    assert result["topology_reachable"] is False
    assert result["reachable"] is False
    assert result["status"] == "disconnected_topology"


def test_archived_time_expanded_path_audit_detects_an_actual_time_ordered_crossing():
    topology = _topology()
    topology["directed_edges"].append(
        {"edge_id": "bridge", "from_node": "b", "to_node": "c"}
    )
    state = pd.DataFrame(
        [
            {"time_s": 0.0, "vehicle_id": "source_0", "edge_id": "src", "leader_id": None},
            {"time_s": 1.0, "vehicle_id": "source_0", "edge_id": "bridge", "leader_id": None},
            {"time_s": 2.0, "vehicle_id": "source_0", "edge_id": "tgt", "leader_id": None},
            {"time_s": 2.0, "vehicle_id": "target_0", "edge_id": "tgt", "leader_id": "source_0"},
        ]
    )

    result = analyze_physical_path_from_archived_tables(
        state, topology, source_vehicle_id="source_0", target_vehicle_id="target_0"
    )

    assert result["topology_reachable"] is True
    assert result["reachable"] is True
    assert result["tau_p"] == pytest.approx(2.0)


def test_archived_time_expanded_path_audit_rejects_a_broken_vehicle_edge_sequence():
    topology = _topology()
    topology["directed_edges"].append(
        {"edge_id": "bridge", "from_node": "b", "to_node": "c"}
    )
    topology["source_edge"] = "src"
    topology["target_edge"] = "tgt"
    state = pd.DataFrame(
        [
            {"time_s": 0.0, "vehicle_id": "source_0", "edge_id": "src", "leader_id": None},
            {"time_s": 1.0, "vehicle_id": "source_0", "edge_id": "tgt", "leader_id": None},
            {"time_s": 1.0, "vehicle_id": "target_0", "edge_id": "tgt", "leader_id": "source_0"},
        ]
    )

    result = analyze_physical_path_from_archived_tables(
        state, topology, source_vehicle_id="source_0", target_vehicle_id="target_0"
    )

    assert result["topology_reachable"] is True
    assert result["reachable"] is False
    assert result["status"] == "right_censored"


def test_archived_time_expanded_path_audit_reconstructs_a_multivehicle_chain():
    topology = {
        "schema_version": "stage_0_1.topology.v1",
        "source_edge": "road",
        "target_edge": "road",
        "directed_edges": [{"edge_id": "road", "from_node": "a", "to_node": "b"}],
    }
    state = pd.DataFrame(
        [
            {"time_s": 0.0, "vehicle_id": "source_0", "edge_id": "road", "leader_id": None},
            {"time_s": 1.0, "vehicle_id": "source_0", "edge_id": "road", "leader_id": None},
            {"time_s": 2.0, "vehicle_id": "source_0", "edge_id": "road", "leader_id": None},
            {"time_s": 0.0, "vehicle_id": "middle_0", "edge_id": "road", "leader_id": None},
            {"time_s": 1.0, "vehicle_id": "middle_0", "edge_id": "road", "leader_id": "source_0"},
            {"time_s": 2.0, "vehicle_id": "middle_0", "edge_id": "road", "leader_id": None},
            {"time_s": 0.0, "vehicle_id": "target_0", "edge_id": "road", "leader_id": None},
            {"time_s": 1.0, "vehicle_id": "target_0", "edge_id": "road", "leader_id": None},
            {"time_s": 2.0, "vehicle_id": "target_0", "edge_id": "road", "leader_id": "middle_0"},
        ]
    )

    result = analyze_physical_path_from_archived_tables(
        state,
        topology,
        source_vehicle_id="source_0",
        target_vehicle_id="target_0",
        source_start_time_s=0.0,
    )

    assert result["reachable"] is True
    assert result["tau_p"] == pytest.approx(2.0)


@pytest.mark.skipif(shutil.which("sumo") is None, reason="SUMO is not installed")
def test_real_sumo_stage_0_1_seals_nonempty_four_cell_package_and_read_only_audit(tmp_path: Path):
    package = run_real_sumo_stage_0_1(
        tmp_path,
        run_id="sumo_e2e",
        seed=2026080701,
        repo_root=Path(__file__).resolve().parents[2],
        command=["pytest", "test_real_sumo_stage_0_1"],
    )

    result = analyze_real_sumo_stage_0_1(package)
    assert result["four_cell_audit"]["cell_ids"] == ["s0c0", "s0c1", "s1c0", "s1c1"]
    assert result["physical_path_audit"]["reachable"] is False
    assert result["pre_treatment_audit"]["equivalence_pass"] is True
    assert result["pre_treatment_audit"]["treatment_start_s"] == pytest.approx(2.0)
    assert result["protocol_summary"]["s1c1"]["adopted_count"] == 1
    assert result["protocol_summary"]["s0c1"]["delivered_count"] == 1
    assert result["cell_summaries"]["s0c1"]["risk_inclusion_statuses"] == ["stage_0_1_validation"]
    for cell in ("s0c0", "s0c1", "s1c0", "s1c1"):
        counts = result["cell_summaries"][cell]["row_counts"]
        assert all(counts[name] > 0 for name in counts)
        assert (package / cell / "topology.json").is_file()
        assert (package / cell / "clock.parquet").is_file()
        assert (package / cell / "vehicle_lifecycle.parquet").is_file()
        config = json.loads((package / cell / "config_frozen.json").read_text(encoding="utf-8"))
        assert config["scientific_claim_eligible"] is False
        assert config["source_event_time_s"] == pytest.approx(2.0)
        state = pd.read_parquet(package / cell / "state.parquet")
        clock = pd.read_parquet(package / cell / "clock.parquet")
        assert state["time_s"].min() == pytest.approx(0.2)
        state_clock = clock[clock["stream_name"] == "state"]
        assert set(state["time_s"].unique()) == set(state_clock["time_s"])
        provenance = json.loads((package / cell / "provenance.json").read_text(encoding="utf-8"))
        assert provenance["sumo"]["version"]
        assert len(provenance["sumo"]["executable_sha256"]) == 64
        assert len(provenance["implementation_sha256"]) == 5
        assert all(len(value) == 64 for value in provenance["implementation_sha256"].values())
        cell_audit = json.loads((package / cell / "audit.json").read_text(encoding="utf-8"))
        assert cell_audit["physical_path_audit"] == result["physical_path_audit"]
