"""Create the AAD Stage 0.5 method references in Zotero via the local API.

All bibliographic fields below were verified against Crossref (DOI records) or the
publisher/official landing page; nothing is filled in from memory. Run once.
"""
from __future__ import annotations

import json
import urllib.request

CACHE = json.load(open("D:/hermes/cache/zotero-local-key.json", encoding="utf-8"))
KEY = CACHE["key"]
SID = CACHE["server_id"]
BASE = "http://127.0.0.1:23119/api/users/18841865"
HEAD = {"Zotero-API-Version": "3", "Zotero-API-Key": KEY, "Zotero-Server-ID": SID, "Content-Type": "application/json"}
C07 = "PWZDPXEE"  # 07_微观跟驰校准与轨迹重放
C08 = "LHV4VHW7"  # 08_拥堵状态识别与时空传播
C09 = "2BMKNCD3"  # 09_仿真校准规范与验证
STAGE = "AAD/Stage0.5"


def tags(*names):
    return [{"tag": name} for name in (STAGE, *names)]


def author(family, given):
    return {"creatorType": "author", "lastName": family, "firstName": given}


ITEMS = [
    {
        "itemType": "journalArticle",
        "title": "Calibration and Validation of Microscopic Traffic Flow Models",
        "creators": [author("Brockfeld", "Elmar"), author("Kühne", "Reinhart D."), author("Wagner", "Peter")],
        "publicationTitle": "Transportation Research Record: Journal of the Transportation Research Board",
        "volume": "1876", "issue": "1", "pages": "62-70", "date": "2004",
        "DOI": "10.3141/1876-07", "libraryCatalog": "Crossref",
        "url": "https://doi.org/10.3141/1876-07",
        "extra": "Verified against Crossref on 2026-10-20. Open full text: https://elib.dlr.de/6652/1/TRB2004-001743.pdf (method and Eq. 2 read in full).",
        "collections": [C07],
        "tags": tags("AAD/Method/leader-replay", "AAD/Role/primary-method"),
    },
    {
        "itemType": "journalArticle",
        "title": "Calibrating Car-Following Models by Using Trajectory Data: Methodological Study",
        "creators": [author("Kesting", "Arne"), author("Treiber", "Martin")],
        "publicationTitle": "Transportation Research Record: Journal of the Transportation Research Board",
        "volume": "2088", "issue": "1", "pages": "148-156", "date": "2008",
        "DOI": "10.3141/2088-16", "libraryCatalog": "Crossref",
        "url": "https://doi.org/10.3141/2088-16",
        "extra": "Metadata verified against Crossref on 2026-10-20; full text not obtained in this task (publisher paywall), so only bibliographic facts are recorded here, not formulas.",
        "collections": [C07],
        "tags": tags("AAD/Method/trajectory-calibration", "AAD/Role/primary-method"),
    },
    {
        "itemType": "journalArticle",
        "title": "Can Results of Car-Following Model Calibration Based on Trajectory Data be Trusted?",
        "creators": [author("Punzo", "Vincenzo"), author("Ciuffo", "Biagio"), author("Montanino", "Marcello")],
        "publicationTitle": "Transportation Research Record: Journal of the Transportation Research Board",
        "volume": "2315", "issue": "1", "pages": "11-24", "date": "2012",
        "DOI": "10.3141/2315-02", "libraryCatalog": "Crossref",
        "url": "https://doi.org/10.3141/2315-02",
        "extra": "Metadata verified against Crossref on 2026-10-20. The NRMSE (spacing, velocity, acceleration) metric used in this project is cited via Schrader et al. (2024) Eqs. 5-6, which attribute it to Punzo et al.; the original was not read directly.",
        "collections": [C07],
        "tags": tags("AAD/Method/trajectory-calibration", "AAD/Method/validation", "AAD/Role/primary-method"),
    },
    {
        "itemType": "journalArticle",
        "title": "Metastable states in a microscopic model of traffic flow",
        "creators": [author("Krauss", "S."), author("Wagner", "P."), author("Gawron", "C.")],
        "publicationTitle": "Physical Review E",
        "volume": "55", "issue": "5", "pages": "5597-5602", "date": "1997-05-01",
        "DOI": "10.1103/PhysRevE.55.5597", "libraryCatalog": "Crossref",
        "url": "https://doi.org/10.1103/PhysRevE.55.5597",
        "extra": "Metadata verified against Crossref on 2026-10-20; full text not obtained in this task.",
        "collections": [C07],
        "tags": tags("AAD/Role/contextual"),
    },
    {
        "itemType": "thesis",
        "title": "Microscopic Modeling of Traffic Flow: Investigation of Collision Free Vehicle Dynamics",
        "creators": [author("Krauß", "Stefan")],
        "thesisType": "PhD dissertation",
        "university": "Universität zu Köln",
        "date": "1998",
        "numPages": "115",
        "language": "en",
        "url": "https://eclipse.dev/sumo/documents/KraussDiss.pdf",
        "extra": "DLR-Forschungsbericht 98-08. Verified on 2026-10-20 via DLR elib record https://elib.dlr.de/8380/ and the SUMO-hosted full text; bibliographic facts only, full method text not read in this task.",
        "collections": [C07],
        "tags": tags("AAD/Role/contextual"),
    },
    {
        "itemType": "journalArticle",
        "title": "Is more always better? The impact of vehicular trajectory completeness on car-following model calibration and validation",
        "creators": [author("Sharma", "Anshuman"), author("Zheng", "Zuduo"), author("Bhaskar", "Ashish")],
        "publicationTitle": "Transportation Research Part B: Methodological",
        "volume": "120", "pages": "49-75", "date": "2019-02",
        "DOI": "10.1016/j.trb.2018.12.016", "libraryCatalog": "Crossref",
        "url": "https://doi.org/10.1016/j.trb.2018.12.016",
        "extra": "Metadata verified against Crossref on 2026-10-20; full text not obtained in this task.",
        "collections": [C07],
        "tags": tags("AAD/Method/trajectory-calibration", "AAD/Method/validation", "AAD/Role/contextual"),
    },
    {
        "itemType": "journalArticle",
        "title": "Calibrating Car-Following Models Using SUMO-in-the-Loop and Vehicle Trajectories From Roadside Radar",
        "creators": [author("Schrader", "Maxwell"), author("Karnik", "Arya"), author("Hainen", "Alexander"), author("Bittle", "Joshua")],
        "publicationTitle": "SUMO Conference Proceedings",
        "volume": "5", "pages": "209-233", "date": "2024-07-17",
        "DOI": "10.52825/scp.v5i.1127", "libraryCatalog": "Crossref",
        "url": "https://doi.org/10.52825/scp.v5i.1127",
        "extra": "Metadata verified against Crossref on 2026-10-20. Open full text read in full: sections 3.3.1 (TraCI leader control), 3.3.2 (NRMSE(s,v,a), Eqs. 5-6), and the 0-10 s headway filtering rule.",
        "collections": [C07],
        "tags": tags("AAD/Method/trajectory-calibration", "AAD/Role/primary-method"),
    },
]


def post_items(items):
    body = json.dumps(items).encode("utf-8")
    request = urllib.request.Request(BASE + "/items", data=body, method="POST", headers=HEAD)
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)


def patch_item(key, payload):
    request = urllib.request.Request(BASE + "/items/" + key, data=json.dumps(payload).encode("utf-8"), method="PATCH", headers=HEAD)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.status


def main():
    created = {}
    for chunk_start in range(0, len(ITEMS), 4):
        chunk = ITEMS[chunk_start:chunk_start + 4]
        result = post_items(chunk)
        for index, info in (result.get("successful") or {}).items():
            created[chunk[int(index)]["title"][:50]] = info["key"]
        for index, error in (result.get("failed") or {}).items():
            print("FAILED", chunk[int(index)]["title"][:50], error)
    print(json.dumps(created, ensure_ascii=False, indent=1))

    # existing items: add the propagation-topic collection and method tags without
    # creating duplicate records
    existing = {
        "5DE6L9RS": ["AAD/Method/space-time-propagation", "AAD/Role/primary-method"],
        "YA2ACMZV": ["AAD/Method/space-time-propagation", "AAD/Method/null-model", "AAD/Role/primary-method"],
    }
    for key, extra_tags in existing.items():
        request = urllib.request.Request(BASE + "/items/" + key, headers=HEAD)
        with urllib.request.urlopen(request, timeout=30) as response:
            item = json.load(response)["data"]
        current_tags = {tag["tag"] for tag in item.get("tags", [])}
        collections = set(item.get("collections", []))
        collections.add(C08)
        payload = {
            "key": key,
            "version": item["version"],
            "collections": sorted(collections),
            "tags": [{"tag": name} for name in sorted(current_tags | set(extra_tags) | {STAGE})],
        }
        print(key, "patched ->", patch_item(key, payload))
    return created


if __name__ == "__main__":
    main()
