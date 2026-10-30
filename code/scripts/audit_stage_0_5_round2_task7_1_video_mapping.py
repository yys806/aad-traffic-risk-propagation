"""Bounded spatial metadata audit; no risk/event extraction or network access."""
from __future__ import annotations
import csv
import hashlib
import io
import json
from pathlib import Path
import zipfile
import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import LineString, Polygon

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'local_research/literature-work/task7_1_20261030'
PRIOR = ROOT / 'evidence/results/RES-STAGE-0.5-ROUND2-TASK7-INDEPENDENT-PHYSICAL-QUALITY-REVIEW-20261030'
PERIODS = ('0750am-0805am', '0805am-0820am')
FT_M = 0.3048  # frozen canonical Local_X/Y conversion, not geodetic survey-foot

def affine_fit(rows):
    a = np.array([[1, r['Local_X'], r['Local_Y']] for r in rows])
    b = np.array([[r['Global_X'], r['Global_Y']] for r in rows])
    return np.linalg.lstsq(a, b, rcond=None)[0]

def residuals(rows, coef):
    a = np.array([[1, r['Local_X'], r['Local_Y']] for r in rows])
    b = np.array([[r['Global_X'], r['Global_Y']] for r in rows])
    d = np.linalg.norm(a @ coef - b, axis=1) * (1200 / 3937)
    return {'n': len(rows), 'rmse_m': float(np.sqrt(np.mean(d*d))), 'max_m': float(d.max())}

def controls(outer):
    result, reads = [], {}
    with zipfile.ZipFile(io.BytesIO(outer.read('us-101-vehicle-trajectory-data.zip'))) as z:
        for period in PERIODS:
            name = f'vehicle-trajectory-data/{period}/trajectories-{period}.csv'
            chosen = {}
            with z.open(name) as f:
                for ordinal, row in enumerate(csv.DictReader(io.TextIOWrapper(f)), 1):
                    lane = int(row['Lane_ID']); y = float(row['Local_Y']) * FT_M
                    if lane in range(1,6) and 0 <= y < 650:
                        key = (lane, int(y//50))
                        if key not in chosen:
                            chosen[key] = dict(period=period, original_row_number=ordinal, lane=lane, **{k:float(row[k]) for k in ['Local_X','Local_Y','Global_X','Global_Y']})
                    if len(chosen) == 65 or ordinal == 50000:
                        break
            result.extend(chosen[k] for k in sorted(chosen))
            reads[period] = {'rows_scanned_until_stop':ordinal, 'spatial_controls':len(chosen), 'member':name, 'selection':'first original row in each lane 1..5 x 50m y bin [0,650); cap 50000 scanned rows; no risk fields used'}
    return result, reads

def crop_ortho(outer, geometries):
    with zipfile.ZipFile(io.BytesIO(outer.read('us-101-aerial-ortho-photos.zip'))) as z:
        tfw = z.read('aerial-ortho-photos/LA-UniversalStudios.tfw')
        a,d,b,e,c,f = map(float,tfw.split())
        assert b == d == 0 and a > 0 and e < 0
        pts=np.array([p for g in geometries for p in g['points']])
        c0=int((pts[:,0].min()-c)/a)-160; c1=int((pts[:,0].max()-c)/a)+160
        r0=int((pts[:,1].max()-f)/e)-160; r1=int((pts[:,1].min()-f)/e)+160
        with z.open('aerial-ortho-photos/LA-UniversalStudios.tif') as s:
            Image.MAX_IMAGE_PIXELS = None
            im=Image.open(s); tags=im.tag_v2
            assert tags[259] == 1 and tags[278] == 1 and im.mode == 'RGB'
            offsets=tags[273]; stride=tags[279][0]
            s.seek(offsets[r0])
            rows=[]
            for r in range(r0,r1+1):
                raw=s.read(stride);rows.append(raw[c0*3:(c1+1)*3])
            crop=Image.frombytes('RGB',(c1-c0+1,r1-r0+1),b''.join(rows))
        def pixel(x,y):return ((x-c)/a-c0,(y-f)/e-r0)
        out={'tfw_values':[a,d,b,e,c,f], 'tfw_sha256':hashlib.sha256(tfw).hexdigest(), 'actual_pixel_size_native_ft':a, 'tiff_size':im.size, 'native_units':'US survey feet per official ortho metadata', 'crop_pixel_bounds':[c0,r0,c1,r1], 'geotiff_crs_tags_present':False}
        return crop, pixel, out

def main():
    WORK.mkdir(parents=True,exist_ok=True)
    geometries=json.loads((PRIOR/'camera_coverage_audit.json').read_text())['geometry']
    with zipfile.ZipFile(ROOT/'dataset/NGSIM/US-101-LosAngeles-CA.zip') as outer:
        rows,read_audit=controls(outer)
        crop,pixel,ortho=crop_ortho(outer,geometries)
    coef=affine_fit(rows)
    a=[r for r in rows if r['period']==PERIODS[0]];b=[r for r in rows if r['period']==PERIODS[1]]
    fit={'coefficients_rows_intercept_localx_localy_cols_globalx_globaly':coef.tolist(), 'all':residuals(rows,coef), 'train0750_test0805':residuals(b,affine_fit(a)), 'train0805_test0750':residuals(a,affine_fit(b))}
    draw=ImageDraw.Draw(crop);coverage=[]
    pooled_fit=fit
    per_window_fit={}
    for period in PERIODS:
      controls_period=[r for r in rows if r['period']==period]
      coef=affine_fit(controls_period)
      per_window_fit[period]={'coefficients':coef.tolist(), 'residuals':residuals(controls_period,coef), 'alternating_holdout':residuals(controls_period[1::2],affine_fit(controls_period[::2]))}
      inverse=np.linalg.inv(coef[1:,:])
      for g in geometries:
          poly=Polygon(g['points']);assert poly.is_valid
          lane_spans=[]
          for lane in range(1,6):
              xs=[r['Local_X'] for r in controls_period if r['lane']==lane];x=float(np.median(xs))
              line=LineString((np.array([[1,x,-100],[1,x,2400]])@coef).tolist())
              inter=poly.intersection(line)
              if inter.is_empty:continue
              parts=list(inter.geoms) if hasattr(inter,'geoms') else [inter]
              ys=[float(((np.array(p)-coef[0,:])@inverse)[1])*FT_M for part in parts for p in part.coords]
              lane_spans.append({'lane':lane,'representative_local_x_ft':x,'local_y_min_m':min(ys),'local_y_max_m':max(ys)})
          lo=min(x['local_y_min_m'] for x in lane_spans);hi=max(x['local_y_max_m'] for x in lane_spans)
          closure=float(np.linalg.norm(np.array(g['points'][0])-np.array(g['points'][-1]))*(1200/3937))
          coverage.append({'period':period,'camera_id':g['camera_id'],'local_y_min_m':lo,'local_y_max_m':hi,'intersects_source':bool(hi>0 and lo<150),'closure_edge_m':closure,'lane_spans':lane_spans,'interpretation':'implicitly close four-corner footprint; camera8 close near-coincident endpoints; geographic footprint is not certified visibility'})
          xy=[pixel(*p) for p in g['points']];draw.line(xy+[xy[0]],fill='yellow',width=4);draw.text(xy[1],f'C{g["camera_id"]}',fill='red',stroke_width=1)
    for r in rows:
        x,y=pixel(r['Global_X'],r['Global_Y']);draw.ellipse([x-4,y-4,x+4,y+4],fill='cyan')
    for period, color in zip(PERIODS, ['red', 'lime']):
        window_coef = np.array(per_window_fit[period]['coefficients'])
        for y in [0, 150]:
            edge = np.array([[1, 0, y/FT_M], [1, 65, y/FT_M]]) @ window_coef
            draw.line([pixel(*p) for p in edge], fill=color, width=7)
            draw.text(pixel(*edge[0]), f'{period[:4]} LocalY={y}m', fill=color, stroke_width=1)
    crop.save(WORK/'camera_source_ortho_overlay.png')
    with (WORK/'spatial_controls.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    result = {
        'control_selection': read_audit,
        'rejected_pooled_fit': pooled_fit,
        'per_window_fit': per_window_fit,
        'ortho': ortho,
        'coverage': coverage,
        'geographic_candidate_camera_set': sorted({
            g['camera_id'] for g in coverage if g['intersects_source']
        }),
        'minimum_camera_set': None,
        'minimum_camera_set_reason': (
            'Geographic footprints and approximate lane lines do not verify full '
            'source visibility, video occlusion, or usable synchronized frames.'
        ),
    }
    (WORK/'spatial_computation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='coverage'},indent=2));print(json.dumps(coverage,indent=2))

if __name__=='__main__':main()
