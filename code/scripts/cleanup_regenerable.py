"""Clean up regenerable artifacts in the AAD repo, with a hard whitelist for evidence.

Decision rule (per the owner's standing archive rule): can this be regenerated?
  - YES -> keep only what the paper/records cite, delete the rest
  - NO  -> keep everything

Hard protection: anything under docs/, evidence/, AI_CONTEXT/ is git-tracked records and is
never touched. Any output file that docs/evidence actually reference by path is also kept,
because deleting it would break the evidence chain.

Never touched: git-tracked files, docs/, evidence/, AI_CONTEXT/, the .git dir, node_modules
(it is a symlink to an external runtime cache, not repo content), and any *summary*/report*/
ledger*/manifest*/index* json.

Usage:
  python scripts/cleanup_regenerable.py --dry-run     # default: report only
  python scripts/cleanup_regenerable.py --execute     # actually delete
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(r"D:\shen\TJU\AAD")

REGEN_EXTS = {".xml", ".parquet", ".pyc", ".pyo"}
REGEN_DIRNAMES = {"__pycache__", "runtime_cache", ".pytest_cache", "node_modules"}

# Names that carry conclusions; never delete even if the extension looks regenerable.
KEEP_NAME_HINTS = ("summary", "report", "ledger", "manifest", "index", "closure",
                   "decision", "audit", "result", "final", "provenance", "sha256sums")

PROTECTED_PREFIXES = ("docs/", "evidence/", "AI_CONTEXT/", "doc/", "skills/", ".git/")


def referenced_paths() -> set[str]:
    """Every repo-relative path that records under docs/evidence/AI_CONTEXT mention."""
    refs: set[str] = set()
    for base in ("docs", "evidence", "AI_CONTEXT"):
        b = ROOT / base
        if not b.exists():
            continue
        for dp, _dn, fn in os.walk(b):
            for f in fn:
                if not f.lower().endswith((".md", ".txt", ".json", ".jsonl", ".csv", ".yaml", ".yml")):
                    continue
                p = os.path.join(dp, f)
                try:
                    txt = Path(p).read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                for m in re.finditer(r"(?:code/)?outputs/[A-Za-z0-9_./-]+", txt):
                    refs.add("code/" + m.group(0) if not m.group(0).startswith("code/") else m.group(0))
    return refs


def tracked_files() -> set[str]:
    r = subprocess.run(["git", "ls-files"], cwd=str(ROOT), capture_output=True, text=True)
    return {line.strip().replace("\\", "/") for line in r.stdout.splitlines() if line.strip()}


def archive_tmp_sources(ct: Path, tracked: set[str], outdir: Path) -> str:
    """Pack every source/record file under code/tmp into one tarball before deletion.

    code/tmp holds ~26k historical scripts and ~32k notes from earlier phases. They cannot be
    regenerated, so they are archived rather than silently dropped. Only text-ish source and
    record extensions are packed; binaries and generated output are not.
    """
    import tarfile

    keep_ext = {".py", ".md", ".txt", ".json", ".jsonl", ".csv", ".sh", ".yaml", ".yml",
                ".toml", ".cfg", ".ini", ".sumocfg", ".rou.xml", ".net.xml", ".html"}
    outdir.mkdir(parents=True, exist_ok=True)
    tar_path = outdir / "code_tmp_sources_archive.tar.gz"
    n = 0
    with tarfile.open(tar_path, "w:gz") as tf:
        for dp, dn, fn in os.walk(ct):
            dn[:] = [d for d in dn if d not in ("__pycache__", ".git", "node_modules")]
            for f in fn:
                p = os.path.join(dp, f)
                ext = os.path.splitext(f)[1].lower()
                is_rou = f.endswith(".rou.xml") or f.endswith(".net.xml")
                if ext not in keep_ext and not is_rou:
                    continue
                rel = os.path.relpath(p, ROOT).replace("\\", "/")
                if rel in tracked:
                    continue
                try:
                    tf.add(p, arcname=rel)
                    n += 1
                except OSError:
                    pass
    print(f"已归档 code/tmp 源码与记录: {n} 个文件 -> {tar_path} "
          f"({tar_path.stat().st_size/1e6:.1f} MB)")
    return str(tar_path)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--execute", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default="code/outputs/analysis/cleanup_20261116")
    args = ap.parse_args()
    execute = args.execute and not args.dry_run

    outdir = ROOT / args.out
    outdir.mkdir(parents=True, exist_ok=True)

    refs = referenced_paths()
    tracked = tracked_files()
    print(f"记录文件中引用的 outputs 路径: {len(refs)} 条")
    print(f"git 跟踪文件: {len(tracked)} 个")
    print(f"模式: {'执行删除' if execute else '仅报告'}\n")

    targets: list[tuple[int, str, str]] = []   # (bytes, relpath, reason)
    skipped_ref: list[tuple[int, str]] = []

    # --- 1) dataset/.tmp_downloads: original archives, re-downloadable by sha256
    tmpdl = ROOT / "dataset/.tmp_downloads"
    if tmpdl.exists():
        for dp, _dn, fn in os.walk(tmpdl):
            for f in fn:
                if not f.endswith((".tar.gz", ".zip")):
                    continue
                p = os.path.join(dp, f)
                rel = os.path.relpath(p, ROOT).replace("\\", "/")
                if rel in tracked:
                    continue
                try:
                    targets.append((os.path.getsize(p), rel, "原始下载包，有 sha256 可重下"))
                except OSError:
                    pass

    # --- 2) regenerable artifacts under code/outputs
    for dp, dn, fn in os.walk(ROOT / "code/outputs"):
        dn[:] = [d for d in dn if d not in ("__pycache__", "runtime_cache", ".pytest_cache")]
        for f in fn:
            p = os.path.join(dp, f)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            if rel in tracked or any(rel.startswith(x) for x in PROTECTED_PREFIXES):
                continue
            ext = os.path.splitext(f)[1].lower()
            low = f.lower()
            if any(h in low for h in KEEP_NAME_HINTS):
                continue
            if ext not in REGEN_EXTS:
                continue
            try:
                sz = os.path.getsize(p)
            except OSError:
                continue
            if rel in refs:
                skipped_ref.append((sz, rel))
                continue
            reason = "SUMO fcd 转储" if ext == ".xml" else ("状态快照" if ext == ".parquet" else "字节码")
            targets.append((sz, rel, reason))

    # --- 3) code/tmp: archive sources and notes first, then delete the rest.
    # 31 万个文件里含 2.6 万个历史脚本和 3.2 万个记录文档；这些删了不可再生，必须先打包。
    ct = ROOT / "code/tmp"
    archive_note = None
    if ct.exists():
        if execute:
            archive_note = archive_tmp_sources(ct, tracked, outdir)
        for dp, dn, fn in os.walk(ct):
            dn[:] = [d for d in dn if d not in ("__pycache__",)]
            for f in fn:
                p = os.path.join(dp, f)
                rel = os.path.relpath(p, ROOT).replace("\\", "/")
                if rel in tracked:
                    continue
                try:
                    targets.append((os.path.getsize(p), rel, "临时工作目录产物（源码已归档）"))
                except OSError:
                    pass

    # --- 4) __pycache__ anywhere except protected trees
    for dp, dn, fn in os.walk(ROOT):
        rel_dir = os.path.relpath(dp, ROOT).replace("\\", "/")
        if any(rel_dir.startswith(x) for x in PROTECTED_PREFIXES) or rel_dir == ".":
            continue
        if os.path.basename(dp) == "__pycache__":
            for f in fn:
                p = os.path.join(dp, f)
                rel = os.path.relpath(p, ROOT).replace("\\", "/")
                if rel in tracked:
                    continue
                try:
                    targets.append((os.path.getsize(p), rel, "字节码缓存"))
                except OSError:
                    pass

    by_reason = defaultdict(lambda: [0, 0])
    for sz, _rel, reason in targets:
        by_reason[reason][0] += sz
        by_reason[reason][1] += 1
    total = sum(s for s, _, _ in targets)

    print(f"{'类别':<34}{'可释放':>12}{'文件数':>10}")
    print("-" * 58)
    for reason, (sz, cnt) in sorted(by_reason.items(), key=lambda kv: -kv[1][0]):
        print(f"{reason:<34}{sz/1e9:>9.2f} GB{cnt:>10}")
    print("-" * 58)
    print(f"{'合计可释放':<34}{total/1e9:>9.2f} GB{len(targets):>10}")
    print(f"\n因被记录引用而保留: {len(skipped_ref)} 个文件, "
          f"{sum(s for s, _ in skipped_ref)/1e9:.2f} GB")

    (outdir / "cleanup_plan.json").write_text(json.dumps({
        "total_bytes": total, "file_count": len(targets),
        "by_reason": {k: {"bytes": v[0], "files": v[1]} for k, v in by_reason.items()},
        "skipped_referenced": {"count": len(skipped_ref),
                               "bytes": sum(s for s, _ in skipped_ref)},
        "targets": [{"path": r, "bytes": s, "reason": why} for s, r, why in targets],
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"清单: {outdir/'cleanup_plan.json'}")

    if not execute:
        print("\n未删除任何文件（仅报告）。加 --execute 才真正删除。")
        return 0

    deleted = failed = 0
    freed = 0
    for sz, rel, _reason in targets:
        p = ROOT / rel
        try:
            p.unlink()
            deleted += 1
            freed += sz
        except OSError:
            failed += 1
    # remove now-empty directories, deepest first
    empty = 0
    for dp, dn, fn in os.walk(ROOT, topdown=False):
        rel_dir = os.path.relpath(dp, ROOT).replace("\\", "/")
        if any(rel_dir.startswith(x) for x in PROTECTED_PREFIXES) or rel_dir == ".":
            continue
        try:
            if not os.listdir(dp):
                os.rmdir(dp)
                empty += 1
        except OSError:
            pass

    print(f"\n已删除 {deleted} 个文件, 释放 {freed/1e9:.2f} GB, 失败 {failed}")
    print(f"清理空目录 {empty} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())