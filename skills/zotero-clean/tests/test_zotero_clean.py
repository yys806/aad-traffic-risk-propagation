"""Offline behavior checks; never read credentials or connect to Zotero."""
from __future__ import annotations

import copy
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import zotero_clean as clean


def item(key, collections, **kwargs):
    return {"key": key, "version": 1, "itemType": "journalArticle",
            "title": key, "collections": collections, "date": "2026",
            "publicationTitle": "Test journal", "creators": [], **kwargs}


class FakeClient:
    def __init__(self):
        self.collection_rows = [
            {"key": "ROOT", "name": "Project", "parentCollection": False},
            {"key": "TOPIC", "name": "Topic", "parentCollection": "ROOT"},
            {"key": "NEST", "name": "Nested", "parentCollection": "TOPIC"},
            {"key": "INBOX", "name": "Inbox", "parentCollection": "ROOT"},
            {"key": "OTHER", "name": "Other project", "parentCollection": False},
        ]
        self.items = {
            "A": item("A", ["ROOT"]),
            "B": item("B", ["TOPIC", "NEST"]),
            "C": item("C", ["INBOX", "OTHER"], tags=[{"tag": "keep"}]),
            "D": item("D", ["NEST"]),
            "E": item("E", ["OTHER"]),
            "PDF": item("PDF", ["ROOT"], itemType="attachment", parentItem="A"),
        }
        self.writes = []

    def collections(self):
        return copy.deepcopy(self.collection_rows)

    def collection_items(self, key):
        return [copy.deepcopy(row) for row in self.items.values() if key in row["collections"]]

    def item(self, key):
        return copy.deepcopy(self.items[key])

    def patch_membership(self, row, collections):
        self.writes.append(row["key"])
        self.items[row["key"]]["collections"] = sorted(collections)


class ZoteroCleanTests(unittest.TestCase):
    def test_pagination_reads_every_page_with_server_cap(self):
        client = object.__new__(clean.ZoteroLocal)
        starts = []
        def request(method, path):
            start = int(parse_qs(urlsplit(path).query)["start"][0])
            starts.append(start)
            return [{"data": {"key": str(i)}} for i in range(start, min(start + 37, 205))]
        client.request = request
        self.assertEqual(len(client.collections()), 205)
        self.assertEqual(starts, [0, 37, 74, 111, 148, 185, 205])

    def test_repeated_pages_fail_instead_of_silent_truncation(self):
        client = object.__new__(clean.ZoteroLocal)
        client.request = lambda method, path: [{"data": {"key": "SAME"}}]
        with self.assertRaisesRegex(ValueError, "repeated keys"):
            client.collections()

    def test_inventory_includes_root_nested_and_inbox_only_items(self):
        _, memberships, records, keys = clean.project_inventory(FakeClient(), "ROOT", "INBOX")
        self.assertEqual(set(records), {"A", "B", "C", "D"})
        self.assertEqual(memberships["B"], {"TOPIC", "NEST"})
        self.assertNotIn("OTHER", keys)
        with self.assertRaises(ValueError):
            clean.project_inventory(FakeClient(), "MISSING")
        with self.assertRaises(ValueError):
            clean.project_inventory(FakeClient(), "ROOT", "OTHER")

    def test_export_uses_project_and_stamp_without_omitting_items(self):
        with tempfile.TemporaryDirectory() as temp:
            md, csv_path = clean.export_index(FakeClient(), "ROOT", Path(temp), "Another project", "INBOX", "20261101")
            self.assertEqual(md.name, "Another_project_ZOTERO_INDEX_20261101.md")
            with csv_path.open(encoding="utf-8-sig", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual({row["item_key"] for row in rows}, {"A", "B", "C", "D"})
            self.assertEqual(next(row for row in rows if row["item_key"] == "C")["collections"], "Inbox")

    def test_audit_covers_complete_project_and_checks_inbox_name(self):
        with tempfile.TemporaryDirectory() as temp:
            _, audit = clean.audit_project(FakeClient(), "ROOT", Path(temp), inbox_name="Inbox")
            report = json.loads(audit.read_text(encoding="utf-8"))
            self.assertEqual(report["top_level_item_count"], 4)
            self.assertEqual(report["topic_collection_count"], 2)
            self.assertEqual(report["root_only_item_keys"], ["A"])
            self.assertEqual(report["inbox_item_keys"], ["C"])
            with self.assertRaises(ValueError):
                clean.audit_project(FakeClient(), "ROOT", Path(temp), inbox_name="Absent")

    def test_apply_preserves_other_memberships_and_is_idempotent(self):
        client = FakeClient()
        original = client.item("C")
        plan = {"root_collection_key": "ROOT", "inbox_collection_key": "INBOX",
                "project_name": "Another project",
                "items": [{"item_key": "C", "destination_collection_keys": ["TOPIC"]}]}
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "execution.json"
            clean.apply_plan(client, plan, manifest, dry_run=True)
            self.assertEqual(client.item("C"), original)
            clean.apply_plan(client, plan, manifest, dry_run=False)
            self.assertEqual(set(client.items["C"]["collections"]), {"OTHER", "TOPIC"})
            self.assertEqual(client.items["C"]["tags"], original["tags"])
            self.assertEqual(json.loads(manifest.read_text())["project_name"], "Another project")
            clean.apply_plan(client, plan, manifest, dry_run=False)
            self.assertEqual(client.writes, ["C"])


if __name__ == "__main__":
    unittest.main()
