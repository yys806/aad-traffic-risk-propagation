"""Task7.2: bounded directory metadata and old-control spatial diagnostics.

Default mode is offline. --probe-official uses the Task7.2-authorized HEAD and
exact metadata ranges only. It never extracts ZIP members or reads video streams.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import struct

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'local_research/literature-work/task7_2_20261030'
PRIOR = ROOT / 'evidence/results/RES-STAGE-0.5-ROUND2-TASK7.1-VIDEO-METADATA-AND-MAPPING-FEASIBILITY-20261030'
RANGE_LIMIT = 8 * 1024 * 1024
FT = 1200 / 3937
TARGETS = tuple(f'raw-video/sb-camera{c}-{p}.avi' for p in ('0750am-0805am','0805am-0820am') for c in (7,8))
DOWNLOAD = 'https://data.transportation.gov/download/4qzi-thur/application/x-zip-compressed'


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + chr(10), encoding='utf-8', newline=chr(10))


def range_header_valid(status, headers, start, end, total):
    """Fail closed before reading any response body when Range is ignored."""
    expected = f'bytes {start}-{end}/{total}'
    return (status == 206 and headers.get('Content-Range') == expected
            and headers.get('Content-Encoding', 'identity').lower() == 'identity'
            and int(headers.get('Content-Length', end-start+1)) == end-start+1)


def parse_directory(data):
    """Read central records only; no local-file headers or member payloads."""
    rows = []; pos = 0
    while pos < len(data):
        if data[pos:pos+4] != b'PK\x01\x02':
            raise ValueError('Unexpected central-directory signature')
        h = struct.unpack_from('<4s6H3I5H2I', data, pos)
        name_len, extra_len, comment_len = h[10:13]
        name = data[pos+46:pos+46+name_len].decode('utf-8' if h[3] & 0x800 else 'cp437')
        extra = data[pos+46+name_len:pos+46+name_len+extra_len]
        sizes = [h[9], h[8], h[16]]  # uncompressed, compressed, local offset
        at = 0
        while at+4 <= len(extra):
            tag, length = struct.unpack_from('<HH', extra, at); block = extra[at+4:at+4+length]; at += 4+length
            if tag == 1:
                j = 0
                for k in range(3):
                    if sizes[k] == 0xffffffff:
                        sizes[k] = struct.unpack_from('<Q', block, j)[0]; j += 8
        for target in TARGETS:
            # Current official ZIP is flat under "NGSIM US-101 Videos/";
            # the older metadata documents raw-video/ as a logical directory.
            # Return all exact basename matches; the caller must assess uniqueness.
            if name.rsplit('/', 1)[-1] == target.rsplit('/', 1)[-1]:
                rows.append(dict(requested_member=target, actual_member=name, compressed_bytes=sizes[1],
                                 uncompressed_bytes=sizes[0], crc32=f'{h[7]:08x}', sha256=None,
                                 compression_method=h[4], encrypted=bool(h[3] & 1),
                                 zip_dos_modified_literal=f'{1980+(h[6]>>9):04d}-{(h[6]>>5)&15:02d}-{h[6]&31:02d}T{h[5]>>11:02d}:{(h[5]>>5)&63:02d}:{(h[5]&31)*2:02d}',
                                 zip_modified_is_not_capture_time=True))
        pos += 46+name_len+extra_len+comment_len
    return rows


def probe_official():
    import requests
    WORK.mkdir(parents=True, exist_ok=True)
    record_path = WORK / 'http_probe_record.json'
    if record_path.exists():
        raise RuntimeError('Probe already recorded; reuse it, do not reset the range budget')
    records=[]; consumed=0
    session=requests.Session(); session.headers.update({'Accept-Encoding':'identity','User-Agent':'AAD-Task7.2-metadata-audit'})
    def metadata(url, name):
        with session.get(url,stream=True,timeout=(15,40)) as response:
            response.raise_for_status(); chunks=[]; size=0
            for chunk in response.iter_content(65536):
                size+=len(chunk)
                if size>2*1024*1024:raise ValueError('Metadata exceeded2MiB cap')
                chunks.append(chunk)
            body=b''.join(chunks);(WORK/name).write_bytes(body)
            records.append(dict(kind='metadata',url=url,resolved_url=response.url,status=response.status_code,bytes_read=size,sha256=hashlib.sha256(body).hexdigest(),headers=dict(response.headers)))
            return body
    def exact_range(start,end,total):
        nonlocal consumed
        length=end-start+1
        if length<=0 or consumed+length>RANGE_LIMIT:raise ValueError('Range budget exceeded')
        with session.get(DOWNLOAD,headers={'Range':f'bytes={start}-{end}'},stream=True,timeout=(15,40)) as response:
            item=dict(kind='zip_metadata_range',url=DOWNLOAD,resolved_url=response.url,status=response.status_code,
                      requested_start=start,requested_end=end,headers=dict(response.headers),bytes_read=0)
            records.append(item)
            if not range_header_valid(response.status_code,response.headers,start,end,total):
                item['stop_reason']='Range not honored exactly; closed without reading body'
                raise ValueError(item['stop_reason'])
            body=response.raw.read(length,decode_content=False); consumed+=len(body);item['bytes_read']=len(body)
            if len(body)!=length:raise ValueError('Short metadata range')
            item['sha256']=hashlib.sha256(body).hexdigest()
            return body
    result={'range_limit_bytes':RANGE_LIMIT,'videos_acquired':0,'member_payloads_read':0,'records':records}
    try:
        video=json.loads(metadata('https://data.transportation.gov/api/views/4qzi-thur.json','video_view.json'))
        metadata('https://catalog.data.gov/dataset/next-generation-simulation-ngsim-program-us-101-videos','video_catalog.html')
        metadata('https://data.transportation.gov/api/views/8ect-6jqj.json','trajectory_view.json')
        total=int(video['blobFileSize'])
        try:
            with session.head(DOWNLOAD,allow_redirects=True,timeout=(15,40)) as response:
                records.append(dict(kind='zip_head',url=DOWNLOAD,resolved_url=response.url,status=response.status_code,headers=dict(response.headers),bytes_read=0))
                response.raise_for_status(); head_total=int(response.headers.get('Content-Length',total))
                if head_total!=total:raise ValueError('HEAD length differs from current catalog; do not proceed')
        except requests.RequestException as exc:
            records.append(dict(kind='head_failure',error=str(exc),bytes_read=0,
                                continuation='Use official catalog size; every GET must independently prove exact206 Content-Range'))
        # Read22-byte EOCD, optionally20-byte ZIP64 locator/56-byte ZIP64 record,
        # then the exact central directory. No leading/trailing video data range.
        eocd_offset=total-22; tail=exact_range(eocd_offset,total-1,total)
        h=struct.unpack('<4s4H2IH',tail)
        if h[0]!=b'PK\x05\x06' or h[7]!=0:raise ValueError('EOCD not exactly last22bytes; stop rather than read video-adjacent data')
        count,size,offset=h[4],h[5],h[6]
        if count==0xffff or size==0xffffffff or offset==0xffffffff:
            locator=struct.unpack('<4sIQI',exact_range(eocd_offset-20,eocd_offset-1,total))
            if locator[0]!=b'PK\x06\x07' or locator[3]!=1:raise ValueError('Unsupported ZIP64 locator')
            z=struct.unpack('<4sQ2H2I4Q',exact_range(locator[2],locator[2]+55,total))
            if z[0]!=b'PK\x06\x06':raise ValueError('Invalid ZIP64 EOCD')
            count,size,offset=z[7],z[8],z[9]
        directory=exact_range(offset,offset+size-1,total)
        (WORK/'central_directory.bin').write_bytes(directory)
        result.update(status='CENTRAL_DIRECTORY_READ',archive_bytes=total,central_directory_offset=offset,central_directory_bytes=size,
                      archive_entry_count=count,target_records=parse_directory(directory))
    except Exception as exc:
        result.update(status='BOUNDED_PROBE_STOPPED',stop_reason=f'{type(exc).__name__}: {exc}')
    finally:
        result['range_body_bytes_read']=consumed
        write(record_path,result)
    print(json.dumps({k:v for k,v in result.items() if k!='records'},ensure_ascii=False,indent=2))


def spatial_diagnostic():
    """Use only Task7.1's130 ID-free controls; no new traffic data reads."""
    WORK.mkdir(parents=True,exist_ok=True)
    with (PRIOR/'spatial_control_points.csv').open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    groups=[[x for x in rows if x['period']==p] for p in ('0750am-0805am','0805am-0820am')]
    designs=[np.array([[1,float(x['Local_X']),float(x['Local_Y'])] for x in g]) for g in groups]
    outputs=[np.array([[float(x['Global_X']),float(x['Global_Y'])] for x in g]) for g in groups]
    fits=[np.linalg.lstsq(a,b,rcond=None)[0] for a,b in zip(designs,outputs)]
    delta=fits[1]-fits[0]
    def summary(v):
        lengths=np.linalg.norm(v,axis=1)
        return dict(mean_xy_m=v.mean(axis=0).tolist(),length_min_m=float(lengths.min()),length_max_m=float(lengths.max()),
                    length_mean_m=float(lengths.mean()),component_sd_m=v.std(axis=0).tolist())
    all_design=np.vstack(designs);difference=all_design@delta*FT
    center=all_design[:,1:].mean(axis=0);center_delta=np.r_[1,center]@delta*FT
    centered=(all_design[:,1:]-center)@delta[1:]*FT
    lanes=[]
    for index,(g,a,b,fit) in enumerate(zip(groups,designs,outputs,fits)):
        errors=(a@fit-b)*FT
        for lane in range(1,6):
            e=errors[[int(x['lane'])==lane for x in g]]
            lanes.append(dict(period_index=index,lane=lane,n=len(e),mean_xy_m=e.mean(axis=0).tolist(),rmse_m=float(np.sqrt(np.mean(np.sum(e*e,axis=1))))))
    sensitivity=[]
    for label, selectors in [
        ('alternating_even',[np.arange(len(a))%2==0 for a in designs]),
        ('alternating_odd',[np.arange(len(a))%2==1 for a in designs]),
        ('source_only_y_lt150',[a[:,2]*0.3048<150 for a in designs]),
        ('downstream_y_ge150',[a[:,2]*0.3048>=150 for a in designs]),
    ]:
        subfits=[np.linalg.lstsq(a[sel],b[sel],rcond=None)[0] for a,b,sel in zip(designs,outputs,selectors)]
        shift=np.r_[1,center]@(subfits[1]-subfits[0])*FT
        source_pivot=np.array([1,31,75/0.3048])
        source_delta=source_pivot@(subfits[1]-subfits[0])*FT
        sensitivity.append(dict(selection=label,n=[int(s.sum()) for s in selectors],center_delta_xy_m=shift.tolist(),center_delta_norm_m=float(np.linalg.norm(shift)),
                                source_pivot_local_x_ft=31,source_pivot_local_y_m=75,source_pivot_delta_xy_m=source_delta.tolist(),
                                source_pivot_delta_norm_m=float(np.linalg.norm(source_delta)),
                                extrapolation_note='source-only fit evaluated at all-control center is extrapolation; downstream-only fit at75m is extrapolation'))
    relation=np.linalg.solve(fits[0][1:],fits[1][1:])
    u,singular,vh=np.linalg.svd(relation);rotation=u@vh
    output=dict(schema='aad.task7_2.spatial-shift.v1',controls=len(rows),additional_controls=0,
        coefficients=fits[0].tolist(),coefficients0805=fits[1].tolist(),delta_coefficients=delta.tolist(),
        constant_delta_at_local_origin_m=(delta[0]*FT).tolist(),linear_difference=delta[1:].tolist(),
        road_position_deltas=[dict(local_x_ft=x,local_y_m=y,delta_xy_m=(np.array([1,x,y/0.3048])@delta*FT).tolist()) for x in [7,31,53] for y in [0,75,150,350,650]],
        control_support_delta=summary(difference),center_local_xy_ft=center.tolist(),center_delta_xy_m=center_delta.tolist(),
        centered_linear_variation=summary(centered),lane_residuals=lanes,selection_sensitivity=sensitivity,
        relative_linear_map=relation.tolist(),relative_singular_values=singular.tolist(),relative_polar_rotation_deg=float(np.degrees(np.arctan2(rotation[1,0],rotation[0,0]))),
        physical_cause='Unknown; correspondence difference is not verified physical displacement',
        decomposition_convention='Row-vector affine fits; polar rotation sign follows right-multiplication matrix, not camera yaw',
        sensitivity_limit='Early spatially selected controls only; subset comparisons are descriptive and not independent temporal validation',
        data_modified=False,formal_p2_recomputed=False)
    write(WORK/'spatial_shift_diagnostic.json',output)
    print(json.dumps({k:output[k] for k in ['controls','constant_delta_at_local_origin_m','control_support_delta','centered_linear_variation','selection_sensitivity','relative_singular_values','relative_polar_rotation_deg']},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--probe-official',action='store_true');args=parser.parse_args()
    probe_official() if args.probe_official else spatial_diagnostic()
