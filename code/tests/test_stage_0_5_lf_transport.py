"""Independent literal-wire cases; no SUMO/traci installation or data required."""
import struct
import pytest
from riskprop.stage_0_5_lf_transport import encode_get,parse_replies

def string(s):
    raw=s.encode();return struct.pack('!i',len(raw))+raw
def packet(body):return bytes([len(body)+1])+body
def reply(obj='v',var=0x7e,value='false',command=0xa4,status=0):
    return packet(bytes([command,status])+string(''))+packet(bytes([0xb4,var])+string(obj)+bytes([0x0c])+string(value))
def decode(var,raw):
    assert var==0x7e and raw[0]==0x0c
    n=struct.unpack('!i',raw[1:5])[0]
    assert len(raw)==n+5
    return raw[5:].decode()

def test_request_is_only_vehicle_get_literal_wire():
    assert encode_get(0x7e,'v',bytes.fromhex('0c0000000178'))==bytes.fromhex('0e a4 7e 00000001 76 0c0000000178')

def test_two_separate_status_and_value_pairs():
    r=parse_replies(reply()+reply('w',value='true'),[(0x7e,'v'),(0x7e,'w')],decode)
    assert r==['false','true']

@pytest.mark.parametrize('raw',[reply(obj='wrong'),reply(var=0x54),reply(command=0xc4),reply(status=1),reply()[:-1],reply()+b'x'])
def test_reply_identity_error_truncation_or_trailer_fails_closed(raw):
    with pytest.raises((ValueError,AssertionError)):parse_replies(raw,[(0x7e,'v')],decode)

def test_long_object_uses_official_extended_length():
    raw=encode_get(0x7e,'x'*300,b'')
    assert raw[0]==0 and struct.unpack('!i',raw[1:5])[0]==len(raw) and raw[5:7]==bytes([0xa4,0x7e])

@pytest.mark.parametrize('var',[0x40,0x72,0xff,None])
def test_unapproved_or_control_variable_rejected(var):
    with pytest.raises(ValueError):encode_get(var,'v',b'')
