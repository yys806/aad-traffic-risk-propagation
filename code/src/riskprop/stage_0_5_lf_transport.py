"""Pinned TraCI1.26 read-only batching. No cache, setter or time advance.

Uses official packing/value decoders but checks each interleaved status/value
pair independently. Connection._sendExact cannot parse queued GET payloads.
Only parameters, route edges and remaining stops are allowed here.
"""
from __future__ import annotations
import struct
import time
from .stage_0_5_positive_worker import DEVICES

ALLOWED=frozenset([0x7e,0x54,0x74])

def encode_get(var,obj,packed):
    if var not in ALLOWED or not isinstance(obj,str) or not obj:raise ValueError('unapproved_read_request')
    name=obj.encode('utf-8');body=bytes([0xa4,var])+struct.pack('!i',len(name))+name+packed
    length=len(body)+1
    return bytes([length])+body if length<=255 else b'\0'+struct.pack('!i',length+4)+body


def _frames(raw):
    cursor=0
    while cursor<len(raw):
        start=cursor;n=raw[cursor];cursor+=1
        if n==0:
            if cursor+4>len(raw):raise ValueError('truncated_frame_length')
            n=struct.unpack('!i',raw[cursor:cursor+4])[0];cursor+=4
        if n<=cursor-start or start+n>len(raw):raise ValueError('invalid_frame_length')
        yield raw[cursor:start+n];cursor=start+n


def _string(raw,offset):
    if offset+4>len(raw):raise ValueError('missing_string_length')
    n=struct.unpack('!i',raw[offset:offset+4])[0];offset+=4
    if n<0 or offset+n>len(raw):raise ValueError('bad_string_length')
    return raw[offset:offset+n].decode('utf-8'),offset+n


def parse_replies(raw,requests,decode):
    frames=list(_frames(raw))
    if len(frames)!=2*len(requests):raise ValueError('reply_count')
    result=[]
    for i,(var,obj) in enumerate(requests):
        status=frames[2*i]
        if len(status)<6:raise ValueError('short_status')
        error,end=_string(status,2)
        if status[0]!=0xa4 or status[1]!=0 or error or end!=len(status):raise ValueError('read_status_failure')
        value=frames[2*i+1]
        if len(value)<7 or value[0]!=0xb4 or value[1]!=var:raise ValueError('variable_response_identity')
        name,offset=_string(value,2)
        if name!=obj:raise ValueError('object_response_identity')
        result.append(decode(var,value[offset:]))
    return result


class VehicleReader:
    """Read the SAME11 getters for EVERY vehicle at EVERY internal step."""
    def __init__(self,conn,mode):
        if mode not in ['sequential','batch']:raise ValueError('unknown_reader_mode')
        self.conn=conn;self.mode=mode;self.requests=0;self.round_trips=0;self.wall_s=0.;self.frames=0

    def collect(self,ids):
        begin=time.perf_counter();result={};self.frames+=1
        if self.mode=='sequential':
            for vid in ids:
                result[vid]=dict(devices={d:self.conn.vehicle.getParameter(vid,'has.'+d+'.device') for d in DEVICES},
                                 route=list(self.conn.vehicle.getRoute(vid)),stops=self.conn.vehicle.getStops(vid,0))
            self.requests+=11*len(ids);self.round_trips+=11*len(ids)
        else:
            import traci.domain as domain
            from traci.storage import Storage
            requests=[];metadata=[]
            for vid in ids:
                for d in DEVICES:
                    requests.append((0x7e,vid,self.conn._pack('s','has.'+d+'.device')));metadata.append((vid,'device',d))
                requests.append((0x54,vid,b''));metadata.append((vid,'route',None))
                requests.append((0x74,vid,self.conn._pack('i',0)));metadata.append((vid,'stops',None))
                result[vid]=dict(devices={})
            def decode(var,raw):
                storage=Storage(raw);value=domain._parse(self.conn.vehicle._retValFunc,var,storage)
                if storage.ready():raise ValueError('unconsumed_value_payload')
                return value
            with self.conn._lock:
                if self.conn._string or self.conn._queue:raise ValueError('pending_connection_command')
                for offset in range(0,len(requests),512):
                    chunk=requests[offset:offset+512];payload=b''.join(encode_get(*r) for r in chunk)
                    self.conn._socket.sendall(struct.pack('!i',len(payload)+4)+payload)
                    response=self.conn._recvExact()
                    if response is None:raise ValueError('closed_batch_connection')
                    values=parse_replies(response._content,[(v,o) for v,o,_ in chunk],decode)
                    for (vid,key,d),value in zip(metadata[offset:offset+512],values):
                        if key=='device':result[vid]['devices'][d]=value
                        else:result[vid][key]=list(value)
                    self.requests+=len(chunk);self.round_trips+=1
        self.wall_s+=time.perf_counter()-begin
        return result

    def summary(self):return dict(mode=self.mode,getter_requests=self.requests,socket_round_trips=self.round_trips,read_wall_s=self.wall_s,internal_frames=self.frames,
        caching_used=False,variables_per_vehicle=11,no_simulation_step_between_reads=True,installed_traci_modified=False)
