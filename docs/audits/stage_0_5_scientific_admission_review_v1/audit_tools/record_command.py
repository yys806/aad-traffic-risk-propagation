"""Record review-only commands, preserving bytes before terminal display.

This task helper is not part of the production source closure. No simulation,
authorization, admission preparation, or ledger entry point is invoked here.
"""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--id', required=True)
    parser.add_argument('--cwd', default='.')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    if not args.id.replace('-', '').replace('_', '').isalnum():
        raise ValueError('unsafe_record_id')
    out = Path(__file__).resolve().parents[1] / 'validation' / args.id
    out.mkdir(parents=True, exist_ok=False)
    start = datetime.datetime.now(datetime.timezone.utc).isoformat()
    try:
        result = subprocess.run(command, cwd=args.cwd, capture_output=True, timeout=300)
        code, stdout, stderr = result.returncode, result.stdout, result.stderr
    except Exception as exc:
        code, stdout, stderr = -1, b'', repr(exc).encode('utf-8')
    for name, data in [('stdout', stdout), ('stderr', stderr)]:
        with (out / (name + '.log')).open('xb') as handle:
            handle.write(data)
    record = dict(schema='aad.scientific-review-command.v1', command=command,
                  cwd=str(Path(args.cwd).resolve()), started_utc=start,
                  completed_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  exit_code=code, stdout_sha256=hashlib.sha256(stdout).hexdigest(),
                  stderr_sha256=hashlib.sha256(stderr).hexdigest())
    with (out / 'record.json').open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(record, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write('\n')
    sys.stdout.buffer.write(json.dumps(record, ensure_ascii=True).encode() + b'\n')
    sys.stdout.buffer.write(stdout.decode('utf-8', 'backslashreplace').encode('ascii', 'backslashreplace'))
    sys.stderr.buffer.write(stderr.decode('utf-8', 'backslashreplace').encode('ascii', 'backslashreplace'))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
