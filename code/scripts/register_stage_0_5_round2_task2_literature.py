"""Idempotently register the Round2 Task2 measurement-contract references in Zotero.

This script writes metadata only.  It never creates a local PDF directory and it
does not download attachments.  Attachments are recorded separately in the task
evidence ledger so an unavailable/blocked download cannot be mistaken for a full
text acquisition.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, r"D:\hermes\scripts")
import zotero_project_lib as L  # noqa: E402


COLLECTIONS = {
    "risk": "NXNARCWW",
    "trajectory": "PWZDPXEE",
    "validation": "2BMKNCD3",
}


def creator(last: str, first: str = "") -> dict[str, str]:
    return {"creatorType": "author", "lastName": last, "firstName": first}


REFERENCES = [
    {
        "id": "pu_joshi_2008_ssam_manual",
        "itemType": "report",
        "title": "Surrogate Safety Assessment Model (SSAM)—Software User Manual",
        "creators": [creator("Pu", "Lili"), creator("Joshi", "Amit")],
        "date": "2008-07",
        "reportNumber": "FHWA-HRT-08-050",
        "url": "https://www.fhwa.dot.gov/publications/research/safety/08050/",
        "collection": "risk",
        "extra": "Report number: FHWA-HRT-08-050\n影响因子: 无（报告无期刊指标）\n5年影响因子: 无（报告无期刊指标）\nJCR分区: 无（报告无期刊指标）\n中科院分区基础版: 无（报告无期刊指标）\n中科院分区升级版: 无（报告无期刊指标）\nCCF: 无（不在 CCF 目录）\nPDF状态: 未获取（当前执行环境网络套接字受限；官方 PDF URL 已核验）",
    },
    {
        "id": "gettman_pu_sayed_shelby_2008_ssam_validation",
        "itemType": "report",
        "title": "Surrogate Safety Assessment Model and Validation: Final Report",
        "creators": [creator("Gettman", "Douglas"), creator("Pu", "Lili"), creator("Sayed", "Tarek"), creator("Shelby", "Steve")],
        "date": "2008-06",
        "reportNumber": "FHWA-HRT-08-051",
        "url": "https://www.fhwa.dot.gov/publications/research/safety/08051/08051.pdf",
        "collection": "risk",
        "extra": "Report number: FHWA-HRT-08-051\n影响因子: 无（报告无期刊指标）\n5年影响因子: 无（报告无期刊指标）\nJCR分区: 无（报告无期刊指标）\n中科院分区基础版: 无（报告无期刊指标）\n中科院分区升级版: 无（报告无期刊指标）\nCCF: 无（不在 CCF 目录）\nPDF状态: 未获取（当前执行环境网络套接字受限；官方 PDF URL 已核验）",
    },
    {
        "id": "gettman_head_2003_surrogate_measures",
        "itemType": "report",
        "title": "Surrogate Safety Measures From Traffic Simulation Models",
        "creators": [creator("Gettman", "Douglas"), creator("Head", "L." )],
        "date": "2003",
        "reportNumber": "FHWA-RD-03-050",
        "url": "https://www.fhwa.dot.gov/publications/research/safety/03050/",
        "collection": "risk",
        "extra": "Report number: FHWA-RD-03-050\n影响因子: 无（报告无期刊指标）\n5年影响因子: 无（报告无期刊指标）\nJCR分区: 无（报告无期刊指标）\n中科院分区基础版: 无（报告无期刊指标）\n中科院分区升级版: 无（报告无期刊指标）\nCCF: 无（不在 CCF 目录）\nPDF状态: 未获取（当前执行环境网络套接字受限；官方 PDF URL 已核验）",
    },
    {
        "id": "arun_2021_systematic_conflict_review",
        "itemType": "journalArticle",
        "title": "A systematic review of traffic conflict-based safety measures with a focus on application context",
        "creators": [creator("Arun", "Ashutosh"), creator("Haque", "Md. Mazharul"), creator("Washington", "Simon"), creator("Sayed", "Tarek"), creator("Mannering", "Fred L.")],
        "date": "2021",
        "publicationTitle": "Analytic Methods in Accident Research",
        "journalAbbreviation": "Anal. Methods Accid. Res.",
        "DOI": "10.1016/j.amar.2021.100185",
        "url": "https://doi.org/10.1016/j.amar.2021.100185",
        "collection": "risk",
        "extra": "影响因子: 待 easyScholar 核验\n5年影响因子: 待 easyScholar 核验\nJCR分区: 待 easyScholar 核验\n中科院分区基础版: 待 easyScholar 核验\n中科院分区升级版: 待 easyScholar 核验\nCCF: 无（不在 CCF 目录）\nPDF状态: 未获取（出版商页面需外部下载；DOI 已核验）",
    },
    {
        "id": "lu_2021_smos_naturalistic",
        "itemType": "journalArticle",
        "title": "Performance evaluation of surrogate measures of safety with naturalistic driving data",
        "creators": [creator("Lu", "Chang"), creator("He", "Xiaolin"), creator("van Lint", "Hans"), creator("Tu", "Huizhao"), creator("Happee", "Riender"), creator("Wang", "Meng")],
        "date": "2021-11",
        "publicationTitle": "Accident Analysis & Prevention",
        "journalAbbreviation": "Accid. Anal. Prev.",
        "volume": "162",
        "pages": "106403",
        "DOI": "10.1016/j.aap.2021.106403",
        "url": "https://doi.org/10.1016/j.aap.2021.106403",
        "collection": "risk",
        "extra": "影响因子: 待 easyScholar 核验\n5年影响因子: 待 easyScholar 核验\nJCR分区: 待 easyScholar 核验\n中科院分区基础版: 待 easyScholar 核验\n中科院分区升级版: 待 easyScholar 核验\nCCF: 无（不在 CCF 目录）\nPDF状态: 未获取（合法开放全文 URL 已核验，当前执行环境无法下载附件）",
    },
    {
        "id": "hu_2022_conflict_risk_copula",
        "itemType": "journalArticle",
        "title": "Modeling conflict risk with real-time traffic data for road safety assessment: a copula-based joint approach",
        "creators": [creator("Hu", "Yuping"), creator("Li", "Ye"), creator("Yuan", "Chen"), creator("Huang", "Helai")],
        "date": "2022",
        "publicationTitle": "Transportation Safety and Environment",
        "journalAbbreviation": "Transp. Saf. Environ.",
        "volume": "4",
        "issue": "3",
        "pages": "tdac017",
        "DOI": "10.1093/tse/tdac017",
        "url": "https://doi.org/10.1093/tse/tdac017",
        "collection": "risk",
        "extra": "影响因子: 待 easyScholar 核验\n5年影响因子: 待 easyScholar 核验\nJCR分区: 待 easyScholar 核验\n中科院分区基础版: 待 easyScholar 核验\n中科院分区升级版: 待 easyScholar 核验\nCCF: 无（不在 CCF 目录）\nPDF状态: 未获取（CityU Scholars 合法全文 URL 已核验，当前执行环境无法下载附件）",
    },
    {
        "id": "tang_2026_ettc_conflicts",
        "itemType": "journalArticle",
        "title": "Two-dimensional ETTC-labeled longitudinal and lateral conflicts for interpretable real-time crash risk prediction in freeway interchange diverging areas",
        "creators": [creator("Tang", "Feng"), creator("Wu", "Rui"), creator("Liu", "Zhizhen")],
        "date": "2026-04-29",
        "publicationTitle": "PLOS ONE",
        "journalAbbreviation": "PLoS One",
        "volume": "21",
        "issue": "4",
        "pages": "e0344623",
        "DOI": "10.1371/journal.pone.0344623",
        "url": "https://doi.org/10.1371/journal.pone.0344623",
        "collection": "risk",
        "extra": "影响因子: 待 easyScholar 核验\n5年影响因子: 待 easyScholar 核验\nJCR分区: 待 easyScholar 核验\n中科院分区基础版: 待 easyScholar 核验\n中科院分区升级版: 待 easyScholar 核验\nCCF: 无（不在 CCF 目录）\nPDF状态: 未获取（PLOS/PMC 合法开放全文 URL 已核验，当前执行环境无法下载附件）",
    },
    {
        "id": "hale_2021_trajectory_calibration",
        "itemType": "report",
        "title": "Trajectory Investigation for Enhanced Calibration of Microsimulation Models",
        "creators": [creator("Hale", "David K."), creator("Li", "Xiaopeng"), creator("Ghiasi", "Amir"), creator("Zhao", "Dongfang"), creator("Khalighi", "Farnoush"), creator("Aycin", "Murat"), creator("James", "Rachel")],
        "date": "2021-08",
        "reportNumber": "FHWA-HRT-21-071",
        "url": "https://www.fhwa.dot.gov/publications/research/operations/21071/21071.pdf",
        "DOI": "10.21949/1521658",
        "collection": "trajectory",
        "extra": "Report number: FHWA-HRT-21-071\n影响因子: 无（报告无期刊指标）\n5年影响因子: 无（报告无期刊指标）\nJCR分区: 无（报告无期刊指标）\n中科院分区基础版: 无（报告无期刊指标）\n中科院分区升级版: 无（报告无期刊指标）\nCCF: 无（不在 CCF 目录）\nPDF状态: 未获取（官方 PDF URL 已核验，当前执行环境网络套接字受限）",
    },
]


def norm(s: str) -> str:
    return L.norm(s)


def main() -> int:
    L.load_key()
    all_items = []
    for col in L.collections():
        all_items.extend(x["data"] for x in L.collection_items(col["data"]["key"]))
    by_doi = {norm(x.get("DOI", "")): x for x in all_items if x.get("DOI")}
    by_title = {norm(x.get("title", "")): x for x in all_items if x.get("title")}
    results = []
    for ref in REFERENCES:
        key = by_doi.get(norm(ref.get("DOI", ""))) or by_title.get(norm(ref["title"]))
        action = "existing"
        if key is None:
            payload = {k: v for k, v in ref.items() if k not in {"id", "collection", "extra"}}
            payload["collections"] = [COLLECTIONS[ref["collection"]]]
            payload["tags"] = [{"tag": "AAD"}, {"tag": "AAD/Stage0.5"}, {"tag": "AAD/Task2-measurement-contract"}]
            payload["extra"] = ref["extra"]
            response = L.zapi("POST", "/items", json=[payload])
            if response.status_code != 200:
                raise RuntimeError(f"create failed {ref['id']}: {response.status_code} {response.text[:200]}")
            key = response.json()["successful"]["0"]["data"]
            key = key["key"]
            action = "created"
        results.append({"id": ref["id"], "title": ref["title"], "doi": ref.get("DOI"),
                        "item_key": key["key"] if isinstance(key, dict) else key,
                        "collection_key": COLLECTIONS[ref["collection"]], "action": action,
                        "pdf_status": "not_acquired"})
    out = Path(r"evidence/results/RES-STAGE-0.5-ROUND2-TASK2-MEASUREMENT-CONTRACT-20261029")
    out.mkdir(parents=True, exist_ok=True)
    (out / "zotero_registration_result.json").write_text(json.dumps({"schema_version": "aad.zotero-registration.v1", "results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
