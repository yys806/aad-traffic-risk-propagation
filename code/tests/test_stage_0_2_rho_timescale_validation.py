from pathlib import Path
import importlib.util
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('rho',ROOT/'scripts/run_stage_0_2_rho_timescale_validation.py'); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)

def test_rho_contribution_semantics():
 assert mod.validate_contribution('valid',True,True,mod.TAU,mod.TAU)[0] == np.exp(-1)
 assert mod.validate_contribution('not_applicable',True,True,None,mod.TAU)==(0.0,0.0)
 assert mod.validate_contribution('invalid',True,True,None,mod.TAU)==(0.0,1.0)
 assert mod.validate_contribution('valid',False,True,mod.TAU,mod.TAU)==(0.0,0.0)
 assert mod.validate_contribution('valid',None,True,mod.TAU,mod.TAU)==(0.0,1.0)

def test_weighted_quantile_is_time_weighted():
 assert mod.weighted_quantile([1,3,9],[1,8,1],.5)==3
 assert mod.weighted_quantile([],[],.5)!=mod.weighted_quantile([],[],.5)
