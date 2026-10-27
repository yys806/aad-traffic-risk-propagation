"""Scientific proposals must not masquerade as approved tolerances."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_aad_week_protocol_v1 import threshold_proposals


def budget():
    return {'group_bounds':dict(numerical_errors=0,timestep_errors=.003,analyzer_errors=1e-15,reconstruction_errors=.007)}


def test_joint_sources_and_arm_errors_are_not_confused_with_sesoi():
    result=threshold_proposals(budget());p=result['preferred']
    assert p['delta_eq_per_arm_fixture']==pytest.approx(.01)
    assert p['delta_eq_paired_fixture']==pytest.approx(.02)
    assert p['delta_eq_four_arm_fixture']==pytest.approx(.04)
    assert p['h']==min(.25*p['delta_R'],.5*(p['delta_plan']-p['delta_R']))
    assert result['B']['value'] is None
    assert result['planning']['paired_variance'] is None
    assert result['planning']['confirmatory_sample_size'] is None
    assert result['status'].startswith('Proposed')


@pytest.mark.parametrize('bad',[None,float('nan'),float('inf'),True,-.1])
def test_missing_or_invalid_error_source_cannot_turn_into_zero(bad):
    values=budget();values['group_bounds']['reconstruction_errors']=bad
    with pytest.raises(ValueError):threshold_proposals(values)


def test_all_four_sources_are_required():
    values=budget();values['group_bounds'].pop('reconstruction_errors')
    with pytest.raises(ValueError):threshold_proposals(values)
