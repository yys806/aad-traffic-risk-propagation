"""Single bounded engineering continuation; never retry an attempted SUMO unit."""
from pathlib import Path
import argparse
import shutil
import time
import numpy as np
import p2_task8_support_experiment as s

def main():
    p=argparse.ArgumentParser();p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--round',type=int,choices=[1,2],required=True);args=p.parse_args()
    out=args.output_dir.resolve()
    if out.parent!=s.ROOT/'code/outputs/calibration' or not out.name.startswith('p2_task8_'):raise ValueError('isolated Task8 output only')
    base=s.load(out/'manifest.json');manifest=base if args.round==1 else s.load(out/'round2_manifest.json');units=manifest['units']
    for rel,digest in base['source_hashes'].items():
        if s.m.sha(s.ROOT/rel)!=digest:raise RuntimeError('Frozen source drift '+rel)
    marker=out/'audit'/f'round{args.round}_serial_manifest.json'
    if marker.exists():raise FileExistsError('Only one serial execution per round')
    selected=[]
    for unit in units:
        path=out/'audit'/f'{unit["unit_id"]}.json'
        if not path.exists():
            if args.round!=2:raise RuntimeError('R1 assignments must already have stop stubs')
            selected.append(unit)
        elif s.load(path)['status']=='NOT_EXECUTED_STOP':selected.append(unit)
        elif args.round==2:raise RuntimeError('Do not repeat attempted R2')
    archive=out/'audit'/f'round{args.round}_pre_serial_stop'
    archive.mkdir(exist_ok=False)
    for name in [f'round{args.round}_truth_freeze.json',f'round{args.round}_completion.json']:
        if (out/'audit'/name).exists():shutil.copy2(out/'audit'/name,archive/name)
    s.dump(marker,{'frozen_utc':s.utc(),'units':selected,'source_hash':s.m.sha(Path(__file__)),'workers':1,
        'same_prelisted_seeds_and_conditions':True,'attempted_failed_seeds_retried':0,
        'original_partial_freeze_preserved':str(archive.relative_to(out)),
        'reason':'One owned SUMO orphan had no listening sockets; exact root cause unverified. Serial startup is a bounded engineering mitigation, not a new source design or seed replacement.'})
    started=time.time();results=[]
    for unit in selected:
        s.budget(out,estimated_s=30,estimated_bytes=3_000_000);uid=unit['unit_id'];folder=out/'raw'/uid
        if folder.exists():
            audit=s.load(out/'audit'/f'{uid}.json')
            assert audit['status']=='NOT_EXECUTED_STOP' and audit['rows']==0
            assert set(p.name for p in folder.iterdir())=={'trajectory.npz'}
            assert len(np.load(folder/'trajectory.npz')['t'])==0
            saved=archive/uid;saved.mkdir()
            # Reversible, exact task-owned zero-frame placeholders only.
            for source in [folder,out/'audit'/f'{uid}.json',out/'truth'/f'{uid}.json']:
                assert source.resolve().is_relative_to(out)
                shutil.move(str(source),str(saved/source.name))
        result=s.one(unit,str(out),base['binary']);results.append(result);print(s.json.dumps(result),flush=True)
        if result['status']!='COMPLETE':
            s.dump(out/'audit'/f'round{args.round}_serial_FAILED_STOP.json',result);break
    # Preserve any never-attempted R2 assignment as Unknown if this bounded attempt stops.
    for unit in units:
        uid=unit['unit_id']
        if (out/'audit'/f'{uid}.json').exists():continue
        folder=out/'raw'/uid;folder.mkdir();np.savez_compressed(folder/'trajectory.npz',t=np.array([]))
        s.dump(out/'audit'/f'{uid}.json',{**unit,'status':'NOT_EXECUTED_STOP','rows':0,'native_target_setters':0,'collisions':0,'teleports':0,'elapsed_s':0})
        s.dump(out/'truth'/f'{uid}.json',s.hash_labels(s.failed_labels(unit,'not executed after serial hard stop')))
    s.seal_round(out,units,args.round)
    s.dump(out/'audit'/f'round{args.round}_serial_completion.json',{'results':results,'elapsed_s':time.time()-started,'resources':s.budget(out),'no_retry_or_replacement':True})

if __name__=='__main__':main()
