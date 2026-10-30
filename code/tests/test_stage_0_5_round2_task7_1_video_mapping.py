"""Small synthetic checks; never load traffic data or launch a simulator."""
import importlib.util
from pathlib import Path
import numpy as np

path = Path(__file__).resolve().parents[1] / 'scripts/audit_stage_0_5_round2_task7_1_video_mapping.py'
spec = importlib.util.spec_from_file_location('task71', path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def points(offset=0):
    coef = np.array([[100.0+offset,200.0],[-0.7,-0.7],[0.7,-0.7]])
    rows=[]
    for x,y in [(0,0),(10,0),(0,20),(10,20),(5,10)]:
        g=np.array([1,x,y])@coef
        rows.append(dict(Local_X=x,Local_Y=y,Global_X=g[0],Global_Y=g[1]))
    return rows,coef

def test_affine_fit_and_inverse_roundtrip():
    rows,expected=points()
    actual=module.affine_fit(rows)
    np.testing.assert_allclose(actual,expected,atol=1e-10)
    for r in rows:
        local=(np.array([r['Global_X'],r['Global_Y']])-actual[0])@np.linalg.inv(actual[1:])
        np.testing.assert_allclose(local,[r['Local_X'],r['Local_Y']],atol=1e-10)

def test_residual_reports_survey_foot_conversion():
    rows,coef=points()
    for r in rows:r['Global_X']+=1
    result=module.residuals(rows,coef)
    assert abs(result['rmse_m']-1200/3937)<1e-10
    assert result['n']==5

def test_window_origin_difference_must_not_be_hidden_by_pooling():
    a,_=points();b,_=points(offset=40)
    pooled=module.affine_fit(a+b)
    assert module.residuals(a+b,pooled)['rmse_m']>6
    assert module.residuals(a,module.affine_fit(a))['rmse_m']<1e-9
    assert module.residuals(b,module.affine_fit(b))['rmse_m']<1e-9
