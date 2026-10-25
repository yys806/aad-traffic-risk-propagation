"""Independent offline event/member and physical-gap checks; no simulation."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import pandas as pd


def verify(root):
    for line in (root/'SHA256SUMS').read_text().splitlines():
        expected, name=line.split('  ',1)
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
            raise AssertionError('artifact_hash:'+name)
    reports=[]
    for window in ['us101__0750_0805','us101__0805_0820']:
        folder=root/window;d=pd.read_parquet(folder/'repaired_measured_state.parquet')
        lookup=d.set_index(['time_s','vehicle_id'])
        selected=d.loc[d.leader_id.notna()]
        leader=lookup.reindex(pd.MultiIndex.from_arrays([selected.time_s,selected.leader_id])).reset_index(drop=True)
        assert (leader.native_lane_id.to_numpy()==selected.native_lane_id.to_numpy()).all()
        expected=leader.native_position_m.to_numpy()-selected.leader_length_m.to_numpy()-selected.native_position_m.to_numpy()
        assert np.allclose(expected,selected.net_gap_m,rtol=0,atol=1e-9)
        r=json.loads((folder/'after_events.json').read_text())
        risk=d.loc[d.reliable_following_eligible & d.ttc_valid & d.measurement_status.eq('valid') & d.ttc_s.gt(0)&d.ttc_s.lt(2)]
        oracle=[]
        for _,g in risk.groupby(['vehicle_id','leader_id','native_lane_id']):
            g=g.sort_values('time_s')
            for _,segment in g.groupby(g.time_s.diff().sub(.1).abs().gt(1e-9).cumsum()):
                if segment.time_s.iloc[-1]-segment.time_s.iloc[0]>=.2-1e-9:
                    oracle.append(tuple(zip(segment.vehicle_id,segment.leader_id,segment.time_s)))
        actual=pd.read_parquet(folder/'after_event_members.parquet')
        actual_members=[tuple(zip(g.vehicle_id,g.leader_id,g.time_s)) for _,g in actual.groupby('event_id')]
        assert set(oracle)==set(actual_members)
        assert len(oracle)==len(r['events'])
        comparison=pd.read_parquet(folder/'row_ttc_comparison.parquet').set_index(['vehicle_id','time_s'])
        before=pd.read_parquet(folder/'before_event_members.parquet')
        changes=[]
        for event_id,members in before.groupby('event_id'):
            c=comparison.reindex(pd.MultiIndex.from_arrays([members.vehicle_id,members.time_s]))
            changes.append(dict(event_id=event_id,members=len(c),
                repaired_unavailable_states=int(c.measurement_status_new.isin(['missing','invalid']).sum()),
                changed_leader_states=int(c.leader_id_old.fillna('').ne(c.leader_id_new.fillna('')).sum()),
                repaired_TTC_below_2_states=int((c.ttc_valid_new&c.ttc_s_new.gt(0)&c.ttc_s_new.lt(2)).sum())))
        reports.append(dict(window=window,physical_gap_rows_verified=len(selected),
            independent_full_context_event_count=len(oracle),event_members_match=True,old_event_changes=changes))
    return dict(status='passed',trajectory_attempts=0,reports=reports)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    if a.report.exists():raise ValueError('refuse_overwrite')
    result=verify(a.root)
    a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('C6_C7_INDEPENDENT_VERIFICATION_OK')
