"""Targeted guards for the bounded closure preparation (no native execution)."""
import importlib.util
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

SPEC = importlib.util.spec_from_file_location(
    'round2_closure', Path(__file__).resolve().parents[1] / 'scripts/prepare_stage_0_5_round2_closure.py')
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


def test_only_min_gap_is_allowed_in_the_two_real_arms():
    a = ET.fromstring('<routes>' + ''.join(f'<vType id="c{i}" tau="{i+1}" minGap="2.5"/>' for i in range(5)) + '</routes>')
    b = ET.fromstring(ET.tostring(a))
    for t in b:
        t.set('minGap', '1.0')
    audit.require_only_min_gap(audit.xml_differences(a, b))
    b[0].set('tau', '9')
    with pytest.raises(ValueError, match='Unexpected arm difference'):
        audit.require_only_min_gap(audit.xml_differences(a, b))


def test_child_or_text_changes_cannot_hide_behind_min_gap():
    a = ET.fromstring('<r><vType minGap="2.5"/><vehicle id="v"/></r>')
    b = ET.fromstring('<r><vType minGap="1.0"/>new text</r>')
    fields = {d['field'] for d in audit.xml_differences(a, b)}
    assert 'children' in fields
    with pytest.raises(ValueError):
        audit.require_only_min_gap(audit.xml_differences(a, b))


@pytest.mark.parametrize('substitute', [{'road_connection_witness': True}, {'lane_id_change': True}, {'topology': 'connected'}, {}])
def test_missing_b_witness_stays_unknown(substitute):
    result = audit.assess_b(substitute)
    assert result['witness_contract_status'] == 'Unknown'
    assert len(result['missing_requirements']) == 5
    assert result['physical_truth_verified_by_this_checker'] is False


def test_b_documentation_is_not_a_physical_truth_certificate():
    evidence = {k: {'status': 'Verified', 'evidence_reference': 'test-only fixture'} for k in audit.REQUIRED_B}
    assert audit.assess_b(evidence)['witness_contract_status'] == 'Documented'
    assert audit.assess_b(evidence)['physical_truth_verified_by_this_checker'] is False
    evidence[audit.REQUIRED_B[0]]['evidence_reference'] = ''
    assert audit.assess_b(evidence)['witness_contract_status'] == 'Unknown'
