from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,subprocess,sys,time,traceback
folder=Path(sys.argv[1]);folder.mkdir(exist_ok=False)
command=sys.argv[2:];started=time.monotonic();out=b'';err=b'';code=None
try:
    p=subprocess.run(command,capture_output=True,timeout=1800)
    out,err,code=p.stdout,p.stderr,p.returncode
except BaseException:
    err=traceback.format_exc().encode('utf-8');code=99
for name,data in [('stdout',out),('stderr',err)]:
    (folder/name).open('xb').write(data)
record=dict(argv=command,cwd=str(Path.cwd()),verified_at=datetime.now(timezone.utc).isoformat(),elapsed_s=time.monotonic()-started,exit_code=code,stdout_sha256=hashlib.sha256(out).hexdigest(),stderr_sha256=hashlib.sha256(err).hexdigest())
(folder/'command.json').open('xb').write(json.dumps(record,ensure_ascii=False,sort_keys=True).encode('utf-8')+bytes([10]))
print(json.dumps(record,ensure_ascii=True));print(out[-3500:].decode('utf-8',errors='backslashreplace').encode('ascii',errors='backslashreplace').decode());print(err[-3500:].decode('utf-8',errors='backslashreplace').encode('ascii',errors='backslashreplace').decode());sys.exit(code)
