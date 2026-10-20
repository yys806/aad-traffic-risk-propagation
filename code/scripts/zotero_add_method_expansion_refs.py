"""Add the Stage 0.5 method-expansion references to Zotero with open-access PDFs.

Metadata comes from Crossref DOI records (verified 2026-10-20). Only lawfully
open PDFs are attached; nothing is fabricated and nothing is deduplicated by
overwriting an existing item.
"""
from __future__ import annotations

import json
import urllib.request
from pathlib import Path

CACHE = json.load(open("D:/hermes/cache/zotero-local-key.json", encoding="utf-8"))
KEY, SID = CACHE["key"], CACHE["server_id"]
BASE = "http://127.0.0.1:23119/api/users/18841865"
HEAD = {"Zotero-API-Version": "3", "Zotero-API-Key": KEY, "Zotero-Server-ID": SID,
        "Content-Type": "application/json"}
PDF_DIR = Path(__file__).resolve().parents[2] / "local_research/litpdf"
C07 = "PWZDPXEE"
C08 = "LHV4VHW7"
C09 = "2BMKNCD3"
STAGE = "AAD/Stage0.5"


def author(first, last):
    return {"creatorType": "author", "firstName": first, "lastName": last}


def tags(*names):
    return [{"tag": name} for name in (STAGE, *names)]


ITEMS = [
    {
        "itemType": "journalArticle",
        "title": "Identifiability of car-following dynamics",
        "creators": [author("Yanbing", "Wang"), author("Maria Laura Delle", "Monache"), author("Daniel B.", "Work")],
        "publicationTitle": "Physica D: Nonlinear Phenomena",
        "volume": "430", "pages": "133090", "date": "2022-02",
        "DOI": "10.1016/j.physd.2021.133090", "libraryCatalog": "Crossref",
        "url": "https://doi.org/10.1016/j.physd.2021.133090",
        "extra": ("Metadata verified against Crossref on 2026-10-20. Open full text read in full: structural identifiability via "
                  "differential geometry (Definitions 1-2); practical identifiability via a numerical direct test; all tested models "
                  "are structurally locally identifiable, CTH-RV and FTL are not identifiable for a specific setup, and all models "
                  "are not practically identifiable when measurement error is present."),
        "collections": [C07],
        "tags": tags("AAD/Method/identifiability", "AAD/Role/primary-method"),
        "_pdf": "wang2022_identifiability.pdf",
    },
    {
        "itemType": "journalArticle",
        "title": "Calibration of nonlinear car-following laws for traffic oscillation prediction",
        "creators": [author("Christine", "Rhoades"), author("Xin", "Wang"), author("Yanfeng", "Ouyang")],
        "publicationTitle": "Transportation Research Part C: Emerging Technologies",
        "volume": "69", "pages": "1-23", "date": "2016-08",
        "DOI": "10.1016/j.trc.2016.05.018", "libraryCatalog": "Crossref",
        "url": "https://doi.org/10.1016/j.trc.2016.05.018",
        "extra": ("Metadata verified against Crossref on 2026-10-20. Full text not obtained in this task (paywalled); the open "
                  "conference version is Transportation Research Procedia 9 (2015) 21-35, DOI 10.1016/j.trpro.2015.07.002. Only "
                  "bibliographic facts are recorded here, no formulas."),
        "collections": [C07],
        "tags": tags("AAD/Method/oscillation-propagation", "AAD/Role/contextual"),
    },
    {
        "itemType": "journalArticle",
        "title": "A simplified car-following theory: a lower order model",
        "creators": [author("G. F.", "Newell")],
        "publicationTitle": "Transportation Research Part B: Methodological",
        "volume": "36", "issue": "3", "pages": "195-205", "date": "2002-03",
        "DOI": "10.1016/S0191-2615(00)00044-8", "libraryCatalog": "Crossref",
        "url": "https://doi.org/10.1016/S0191-2615(00)00044-8",
        "extra": ("Metadata verified against Crossref on 2026-10-20. Full text not obtained in this task (paywalled). The Newell "
                  "prototype implemented in AAD-0.5-METHOD-EXPANSION states its own discretisation explicitly and is not presented "
                  "as this paper's equation."),
        "collections": [C07],
        "tags": tags("AAD/Method/leader-replay", "AAD/Role/contextual"),
    },
]


def post(path, payload, method="POST"):
    request = urllib.request.Request(BASE + path, data=json.dumps(payload).encode("utf-8"), method=method, headers=HEAD)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def upload_file(item_key: str, pdf: Path) -> bool:
    request = urllib.request.Request(
        BASE + f"/items/{item_key}/file",
        data=pdf.read_bytes(),
        method="POST",
        headers={"Zotero-API-Version": "3", "Zotero-API-Key": KEY, "Zotero-Server-ID": SID,
                 "Content-Type": "application/pdf", "If-None-Match": "*"},
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            return response.status in (200, 201)
    except Exception as error:  # noqa: BLE001
        print("  upload failed:", error)
        return False


def main():
    created = {}
    for item in ITEMS:
        payload = {k: v for k, v in item.items() if not k.startswith("_")}
        result = post("/items", [payload])
        if result.get("failed"):
            print("FAILED", payload["title"][:50], result["failed"])
            continue
        key = list(result["successful"].values())[0]["key"]
        created[payload["title"][:45]] = key
        print("created", key, payload["title"][:55])
        pdf_name = item.get("_pdf")
        if pdf_name:
            pdf = PDF_DIR / pdf_name
            if pdf.is_file():
                attachment = {
                    "itemType": "attachment", "linkMode": "imported_url", "parentItem": key,
                    "title": "Full Text PDF", "url": item["url"], "contentType": "application/pdf",
                    "note": "open-access copy attached by AAD-0.5-METHOD-EXPANSION",
                }
                uploaded = post("/items", [attachment])
                if uploaded.get("successful"):
                    attachment_key = list(uploaded["successful"].values())[0]["key"]
                    ok = upload_file(attachment_key, pdf)
                    print("   attachment", attachment_key, "uploaded" if ok else "FAILED")
                else:
                    print("   attachment item failed", uploaded.get("failed"))
    print(json.dumps(created, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
