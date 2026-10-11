from pathlib import Path
import pandas as pd
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/formal/calibration/stage_0_2_task_2_5_2_20261011_r1'

def test_center_event_and_nearby_are_distinct():
 d=pd.read_csv(OUT/'key_difference_cases.csv')
 assert len(d)>=10
 assert d.center_event_membership_verified.all()
 assert (d.nearby_event_count_3s>=d[['P1_strict_nearby_event_count','P2_middle_nearby_event_count','P3_sensitive_nearby_event_count']].max(axis=1)).all()

def test_difference_pools_are_present():
 d=pd.read_csv(OUT/'key_difference_cases.csv')
 assert {'P2_without_P1','P3_without_P2','all_three_confirmation_spread'} <= set(d.selection_class)
 assert (d[d.selection_class=='P2_without_P1']['P2_middle_center_triggered']).all()
 assert (~d[d.selection_class=='P2_without_P1']['P1_strict_center_triggered']).all()
 assert (d[d.selection_class=='P3_without_P2']['P3_sensitive_center_triggered']).all()
 assert (~d[d.selection_class=='P3_without_P2']['P2_middle_center_triggered']).all()

def test_new_casebook_pages_and_unverified_truth():
 d=pd.read_csv(OUT/'key_difference_cases.csv')
 assert len(PdfReader(str(OUT/'key_difference_casebook.pdf')).pages)==len(d)
 assert set(d.physical_truth_status)=={'Unverified'}

def test_all_confirmation_times_are_observed_member_times():
 d=pd.read_csv(OUT/'key_difference_cases.csv')
 for rule in ['P1_strict','P2_middle','P3_sensitive']:
  x=d[d[f'{rule}_center_triggered']]
  assert (x[f'{rule}_center_confirm_s']>=x[f'{rule}_center_onset_s']).all()
