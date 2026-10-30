"""Small synthetic checks only: no network or traffic/media inputs."""
import importlib.util
from pathlib import Path
import struct

path=Path(__file__).resolve().parents[1]/'scripts/audit_stage_0_5_round2_task7_2_resources.py'
spec=importlib.util.spec_from_file_location('task72',path)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

def central_record(name):
    raw=name.encode('utf-8')
    return struct.pack('<4s6H3I5H2I',bytes([80,75,1,2]),20,20,2048,8,0,0,0x12345678,100,500,len(raw),0,0,0,0,0,0)+raw

def test_range_must_be_exact206_before_any_body_read():
    headers={'Content-Range':'bytes 78-99/100','Content-Length':'22'}
    assert module.range_header_valid(206,headers,78,99,100)
    assert not module.range_header_valid(200,headers,78,99,100)
    assert not module.range_header_valid(206,headers,77,99,100)

def test_flat_directory_matches_raw_basename_and_keeps_crc_distinct_from_sha():
    body=central_record('NGSIM US-101 Videos/sb-camera7-0750am-0805am.avi')
    body+=central_record('NGSIM US-101 Videos/sb-camera7-0750am-0805am-processed.avi')
    rows=module.parse_directory(body)
    assert len(rows)==1 and rows[0]['compressed_bytes']==100 and rows[0]['uncompressed_bytes']==500
    assert rows[0]['crc32']=='12345678' and rows[0]['sha256'] is None

def test_multiple_exact_candidates_are_preserved_for_ambiguity_audit():
    rows=module.parse_directory(central_record('a/sb-camera8-0805am-0820am.avi')+central_record('b/sb-camera8-0805am-0820am.avi'))
    assert len(rows)==2
