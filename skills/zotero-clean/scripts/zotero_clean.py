"""Plan/apply auditable Zotero collection cleanup through the local HTTP API.

This script intentionally performs collection-membership changes only. It never
touches the Zotero database files and never emits the local API credential.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_KEY_PATH = Path(r"D:\hermes\cache\zotero-local-key.json")
DEFAULT_BASE = "http://127.0.0.1:23119/api/users/18841865"


class ZoteroLocal:
    def __init__(self, key_path: Path | None = None, base: str = DEFAULT_BASE) -> None:
        cache_path = key_path or Path(os.environ.get("ZOTERO_LOCAL_KEY_PATH", DEFAULT_KEY_PATH))
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
        self.base = base.rstrip("/")
        self.headers = {
            "Zotero-API-Version": "3",
            "Zotero-API-Key": cache["key"],
            "Zotero-Server-ID": cache["server_id"],
            "Content-Type": "application/json",
        }

    def request(self, method: str, path: str, payload: Any | None = None) -> Any:
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(self.base + path, data=data, method=method, headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=60) as response:
                raw = response.read()
                return json.loads(raw.decode("utf-8")) if raw else {"status": response.status}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Zotero API {method} {path} failed: HTTP {exc.code}: {body[:500]}") from exc

    def item(self, key: str) -> dict[str, Any]:
        return self.request("GET", f"/items/{urllib.parse.quote(key)}")["data"]

    def collections(self) -> list[dict[str, Any]]:
        response = self.request("GET", "/collections?limit=1000")
        rows = response if isinstance(response, list) else response.get("collections", [])
        return [row.get("data", row) for row in rows]

    def collection_items(self, key: str) -> list[dict[str, Any]]:
        response = self.request("GET", f"/collections/{urllib.parse.quote(key)}/items?limit=1000")
        rows = response if isinstance(response, list) else response.get("items", [])
        return [row.get("data", row) for row in rows]

    def patch_membership(self, item: dict[str, Any], collections: set[str]) -> Any:
        payload = {"key": item["key"], "version": item["version"], "collections": sorted(collections)}
        return self.request("PATCH", f"/items/{urllib.parse.quote(item['key'])}", payload)


def load_plan(path: Path) -> dict[str, Any]:
    plan = json.loads(path.read_text(encoding="utf-8"))
    if not plan.get("root_collection_key") or not plan.get("inbox_collection_key"):
        raise ValueError("plan must include root_collection_key and inbox_collection_key")
    if not plan.get("items"):
        raise ValueError("plan must include a non-empty items list")
    for row in plan["items"]:
        if not row.get("item_key") or not row.get("destination_collection_keys"):
            raise ValueError("each plan item needs item_key and destination_collection_keys")
    return plan


def apply_plan(client: ZoteroLocal, plan: dict[str, Any], manifest_path: Path, dry_run: bool) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    rows: list[dict[str, Any]] = []
    for planned in plan["items"]:
        item = client.item(planned["item_key"])
        before = sorted(set(item.get("collections", [])))
        destinations = set(planned["destination_collection_keys"])
        if plan["inbox_collection_key"] in destinations:
            raise ValueError(f"destination list contains inbox for {item['key']}")
        after = sorted((set(before) | destinations) - {plan["inbox_collection_key"]})
        changed = before != after
        if changed and not dry_run:
            client.patch_membership(item, set(after))
            verified = client.item(item["key"])
            verified_collections = sorted(set(verified.get("collections", [])))
            if verified_collections != after:
                raise RuntimeError(f"post-write membership mismatch for {item['key']}: {verified_collections} != {after}")
        else:
            verified_collections = after
        rows.append(
            {
                "item_key": item["key"],
                "title": item.get("title", ""),
                "reason": planned.get("reason", ""),
                "before_collections": before,
                "after_collections": verified_collections,
                "changed": changed,
                "dry_run": dry_run,
            }
        )
    manifest = {
        "schema_version": "zotero-clean.execution.v1",
        "executed_utc": started,
        "toolchain": "Zotero local HTTP API; Computer Use disabled",
        "root_collection_key": plan["root_collection_key"],
        "inbox_collection_key": plan["inbox_collection_key"],
        "plan_source": str(plan.get("plan_source", "")),
        "items": rows,
        "dry_run": dry_run,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return manifest


def export_index(client: ZoteroLocal, root_key: str, output_dir: Path) -> tuple[Path, Path]:
    collections = {row["key"]: row for row in client.collections()}
    topic = [row for row in collections.values() if row.get("parentCollection") == root_key]
    membership: dict[str, list[str]] = {}
    titles: dict[str, str] = {}
    for collection in topic:
        for brief in client.collection_items(collection["key"]):
            if brief.get("itemType") in {"attachment", "note"} or brief.get("parentItem"):
                continue
            key = brief["key"]
            membership.setdefault(key, []).append(collection["key"])
            titles[key] = brief.get("title", "")
    rows = []
    for key in sorted(membership, key=lambda k: titles.get(k, "").casefold()):
        names = [collections[c]["name"] for c in sorted(membership[key], key=lambda c: collections[c]["name"])]
        rows.append({"item_key": key, "title": titles[key], "collections": names})
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "AAD_ZOTERO_INDEX_2026-11-01.csv"
    md_path = output_dir / "AAD_ZOTERO_INDEX_2026-11-01.md"
    with csv_path.open("w", newline="", encoding="utf-8-sig") as fh:
        writer = csv.DictWriter(fh, fieldnames=["item_key", "title", "collections"])
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "collections": " | ".join(row["collections"])})
    lines = [
        "# AAD Zotero 文献索引（2026-11-01）",
        "",
        "> 来源：Zotero `TJU → AAD` 实时集合；索引由 Zotero 本机 HTTP API 生成。`补充文献-未分类` 保留为收件箱，不作为主题集合计入。",
        "",
        f"共 {len(rows)} 个唯一 item key。",
        "",
        "| item key | 题名 | 所属主题集合 |",
        "|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| `{row['item_key']}` | {row['title'].replace('|', '\\|')} | {'；'.join(row['collections']).replace('|', '\\|')} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path, csv_path


def _norm_text(value: str) -> str:
    value = unicodedata.normalize("NFKC", value or "").casefold()
    return re.sub(r"[^\w]+", " ", value, flags=re.UNICODE).strip()


def _norm_doi(value: str) -> str:
    value = (value or "").strip().casefold()
    value = re.sub(r"^https?://(dx\.)?doi\.org/", "", value)
    return value.rstrip(" .;,")


def _year(value: str) -> str:
    match = re.search(r"\b(19|20)\d{2}\b", value or "")
    return match.group(0) if match else ""


def audit_project(client: ZoteroLocal, root_key: str, output_dir: Path) -> tuple[Path, Path]:
    collections = {row["key"]: row for row in client.collections()}
    children = [row for row in collections.values() if row.get("parentCollection") == root_key]
    topic_children = [row for row in children if row.get("name") != "补充文献-未分类"]
    memberships: dict[str, set[str]] = {}
    brief: dict[str, dict[str, Any]] = {}
    for collection in topic_children:
        for row in client.collection_items(collection["key"]):
            if row.get("itemType") in {"attachment", "note"} or row.get("parentItem"):
                continue
            key = row["key"]
            memberships.setdefault(key, set()).add(collection["key"])
            brief[key] = row
    records: list[dict[str, Any]] = []
    for key in sorted(memberships):
        item = client.item(key)
        data = {
            "item_key": key,
            "title": item.get("title", ""),
            "doi": item.get("DOI", ""),
            "creators": item.get("creators", []),
            "date": item.get("date", ""),
            "publication_title": item.get("publicationTitle", ""),
            "item_type": item.get("itemType", ""),
            "collections": sorted(memberships[key]),
            "collection_names": sorted(collections[c]["name"] for c in memberships[key]),
            "tags": [tag.get("tag", "") for tag in item.get("tags", [])],
            "num_children": brief[key].get("numChildren", 0),
        }
        data["doi_norm"] = _norm_doi(data["doi"])
        first = next((c for c in data["creators"] if c.get("creatorType") == "author"), {})
        data["identity_norm"] = "|".join((_norm_text(data["title"]), _norm_text(first.get("lastName", "")), _year(data["date"])))
        records.append(data)

    def groups_by(field: str) -> list[dict[str, Any]]:
        groups: dict[str, list[dict[str, Any]]] = {}
        for record in records:
            value = record.get(field, "")
            if value:
                groups.setdefault(value, []).append(record)
        return [
            {"basis": field, "value": value, "items": [{"item_key": r["item_key"], "title": r["title"], "collections": r["collection_names"]} for r in rows]}
            for value, rows in sorted(groups.items())
            if len(rows) > 1
        ]

    exact_doi = groups_by("doi_norm")
    exact_identity = groups_by("identity_norm")
    conflicts = []
    for group in exact_doi:
        rows = [next(r for r in records if r["item_key"] == i["item_key"]) for i in group["items"]]
        fields = {}
        for field in ("title", "publication_title", "date"):
            values = sorted({_norm_text(r[field]) for r in rows if r[field]})
            if len(values) > 1:
                fields[field] = values
        if fields:
            conflicts.append({"doi": group["value"], "item_keys": [r["item_key"] for r in rows], "fields": fields})

    invalid_candidates = []
    keywords = ("retracted", "retraction", "withdrawn", "withdrawal", "superseded")
    for record in records:
        missing = [field for field in ("title", "date", "publication_title") if not record[field]]
        joined = " ".join([record["title"], *record["tags"]]).casefold()
        flags = [word for word in keywords if word in joined]
        if missing or flags:
            invalid_candidates.append({"item_key": record["item_key"], "title": record["title"], "missing_core_fields": missing, "status_keywords": flags, "action": "review"})

    inbox_keys = {row["key"] for row in client.collection_items(next((c["key"] for c in children if c["name"] == "补充文献-未分类"), "__missing__")) if row.get("itemType") not in {"attachment", "note"} and not row.get("parentItem")} if any(c["name"] == "补充文献-未分类" for c in children) else set()
    report = {
        "schema_version": "zotero-clean.audit.v1",
        "toolchain": "Zotero local HTTP API; Computer Use disabled",
        "root_collection_key": root_key,
        "topic_collection_count": len(topic_children),
        "inbox_collection_present": any(c.get("name") == "补充文献-未分类" for c in children),
        "top_level_item_count": len(records),
        "inbox_item_keys": sorted(inbox_keys),
        "exact_doi_duplicate_candidates": exact_doi,
        "exact_title_author_year_candidates": exact_identity,
        "metadata_conflicts": conflicts,
        "invalid_or_metadata_review_candidates": invalid_candidates,
        "records": records,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
    json_path = output_dir / f"zotero_clean_audit_{stamp}.json"
    md_path = output_dir / f"zotero_clean_audit_{stamp}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        f"# Zotero 项目审计（{stamp}）",
        "",
        "> 只读审计；重复、冲突和失效候选不会自动合并、删除或退役。",
        "",
        f"- 顶层条目：{len(records)}",
        f"- 主题集合：{len(topic_children)}",
        f"- 收件箱条目：{len(inbox_keys)}",
        f"- DOI 重复候选：{len(exact_doi)}",
        f"- 无 DOI 的题名/作者/年份候选：{len(exact_identity)}",
        f"- 元数据冲突：{len(conflicts)}",
        f"- 失效或元数据复核候选：{len(invalid_candidates)}",
        "",
        "## Exact DOI duplicate candidates",
        "",
    ]
    if exact_doi:
        for group in exact_doi:
            lines.append(f"- `{group['value']}`: " + ", ".join(f"`{i['item_key']}` {i['title']}" for i in group["items"]))
    else:
        lines.append("None")
    lines.extend(["", "## Metadata conflicts", ""])
    if conflicts:
        for conflict in conflicts:
            lines.append(f"- `{conflict['doi']}`: {', '.join(conflict['item_keys'])}; fields={json.dumps(conflict['fields'], ensure_ascii=False)}")
    else:
        lines.append("None")
    lines.extend(["", "## Invalid or metadata review candidates", ""])
    if invalid_candidates:
        for candidate in invalid_candidates:
            lines.append(f"- `{candidate['item_key']}` {candidate['title']} — missing={candidate['missing_core_fields']}; keywords={candidate['status_keywords']}; action=review")
    else:
        lines.append("None")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return md_path, json_path


def verify_plan(client: ZoteroLocal, plan: dict[str, Any]) -> dict[str, Any]:
    planned_keys = {row["item_key"] for row in plan["items"]}
    rows = []
    for planned in plan["items"]:
        item = client.item(planned["item_key"])
        current = set(item.get("collections", []))
        destinations = set(planned["destination_collection_keys"])
        rows.append(
            {
                "item_key": item["key"],
                "title": item.get("title", ""),
                "inbox_absent": plan["inbox_collection_key"] not in current,
                "destinations_present": destinations.issubset(current),
                "collections": sorted(current),
            }
        )
    inbox_keys = {row["key"] for row in client.collection_items(plan["inbox_collection_key"])}
    result = {
        "schema_version": "zotero-clean.verification.v1",
        "toolchain": "Zotero local HTTP API; Computer Use disabled",
        "planned_items": len(rows),
        "all_items_present_and_classified": all(row["inbox_absent"] and row["destinations_present"] for row in rows),
        "inbox_contains_planned_items": sorted(inbox_keys & planned_keys),
        "items": rows,
    }
    if not result["all_items_present_and_classified"] or result["inbox_contains_planned_items"]:
        raise RuntimeError(json.dumps(result, ensure_ascii=False))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--export-index", action="store_true")
    parser.add_argument("--audit", action="store_true")
    parser.add_argument("--verify", action="store_true")
    parser.add_argument("--root-key")
    parser.add_argument("--output-dir", type=Path)
    args = parser.parse_args(argv)
    client = ZoteroLocal()
    if args.export_index:
        if not args.root_key or not args.output_dir:
            parser.error("--export-index requires --root-key and --output-dir")
        md, csv_path = export_index(client, args.root_key, args.output_dir)
        print(json.dumps({"markdown": str(md), "csv": str(csv_path)}, ensure_ascii=False))
        return 0
    if args.audit:
        if not args.root_key or not args.output_dir:
            parser.error("--audit requires --root-key and --output-dir")
        md, json_path = audit_project(client, args.root_key, args.output_dir)
        print(json.dumps({"markdown": str(md), "json": str(json_path)}, ensure_ascii=False))
        return 0
    if args.verify:
        if not args.plan:
            parser.error("--verify requires --plan")
        result = verify_plan(client, load_plan(args.plan))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    if not args.plan or not args.manifest:
        parser.error("apply/dry-run requires --plan and --manifest")
    if not args.apply and not args.dry_run:
        parser.error("choose --apply or --dry-run")
    plan = load_plan(args.plan)
    plan["plan_source"] = str(args.plan)
    apply_plan(client, plan, args.manifest, dry_run=not args.apply)
    print(str(args.manifest))
    return 0


if __name__ == "__main__":
    sys.exit(main())
