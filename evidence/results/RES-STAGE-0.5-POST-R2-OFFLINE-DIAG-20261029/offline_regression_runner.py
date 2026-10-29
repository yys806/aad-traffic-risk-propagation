"""Task-local regression runner. Native tests deselected; no simulator process."""
import json
import os
import pathlib
import sys
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[3]
OUT = ROOT / 'evidence/results/RES-STAGE-0.5-POST-R2-OFFLINE-DIAG-20261029'
TEMP = pathlib.Path('C:/Users/Lenovo/.codex/visualizations/2026/10/28/01a18194-fb3b-7643-898c-afd76f45e2a9/post_r2_full_final_20261029')
NATIVE = ['tests/test_stage_0_1_sumo.py::test_real_sumo_stage_0_1_seals_nonempty_four_cell_package_and_read_only_audit']
NATIVE += ['tests/test_stage_0_5_sumo.py::'+n for n in [
 'test_sumo_baseline_engineering_run_is_sealed_and_contract_complete',
 'test_sumo_probe_fixture_confirms_a_p2_event_in_both_adapters',
 'test_sumo_run_is_reproducible_for_the_same_seed_and_config',
 'test_sumo_internal_and_recorded_steps_are_separately_configurable',
 'test_sumo_warmup_window_is_respected_and_unbuilt_scenarios_are_refused',
 'test_sumo_smoke_runs_never_change_the_stage_gate']]
def guard(event, args):
    if event == 'subprocess.Popen':
        executable = str(args[0]).lower().replace('\\','/').rsplit('/',1)[-1]
        if executable in {'sumo','sumo.exe','sumo-gui','sumo-gui.exe','netconvert','netconvert.exe','wsl','wsl.exe'}:
            raise PermissionError('POST_R2_FORBIDDEN_NATIVE_PROCESS:'+executable)
    if event in {'socket.connect','socket.bind'}:
        raise PermissionError('POST_R2_NO_NETWORK_OR_TRACI')
    if event == 'open' and isinstance(args[0],str):
        p = args[0].lower().replace('\\','/')
        if '/dataset/' in p and ('locked_holdout' in p or '/locked/' in p):
            raise PermissionError('POST_R2_NO_LOCKED_HOLDOUT')
sys.addaudithook(guard)
class Recorder:
    def __init__(self): self.failed=[]; self.counts={}
    def pytest_runtest_logreport(self, report):
        if report.when=='call' or report.failed:
            self.counts[report.outcome]=self.counts.get(report.outcome,0)+1
        if report.failed:
            detail=str(report.longrepr)
            if 'pyarrow' in detail or 'fastparquet' in detail:
                cause='missing_Parquet_engine_explicit_traceback'
            elif 'traci' in detail and ('ModuleNotFoundError' in detail or 'ImportError' in detail):
                cause='missing_traci_explicit_traceback'
            elif 'PermissionError' in detail:
                cause='permission_error_requires_specific_review'
            else: cause='assertion_or_other_failure_requires_specific_review'
            self.failed.append(dict(nodeid=report.nodeid,phase=report.when,cause=cause,traceback=detail))
recorder=Recorder()
os.chdir(ROOT/'code')
args=['-q','--tb=short','-p','no:cacheprovider','--basetemp='+str(TEMP)]
args += ['--deselect='+n for n in NATIVE]
code=pytest.main(args,plugins=[recorder])
(OUT/'offline_regression_failures.json').write_text(json.dumps(dict(command=[sys.executable,'-B',__file__],
    pytest_arguments=args,exit_code=int(code),counts=recorder.counts,excluded_native=NATIVE,
    failures=recorder.failed,native_launches=0,traci_connections=0),indent=2)+'\n',encoding='utf-8')
sys.exit(code)

