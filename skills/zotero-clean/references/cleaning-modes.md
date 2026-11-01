# Cleaning modes and decision records

## Duplicate candidates

Normalize DOI values by trimming whitespace, removing `https://doi.org/`, `http://dx.doi.org/`, and case-folding. An exact normalized DOI match is an exact-duplicate candidate, but it is not automatically safe to merge: the same paper can have intentional records in different project collections. Without a DOI, use normalized title + first author + year as an exact-title candidate. Title similarity alone is only a near-duplicate candidate.

For every candidate record `candidate_key`, `canonical_key` (if known), match basis, metadata comparison, collection memberships, attachment/note counts, and action (`preserve`, `merge`, `archive`, `delete`, or `review`). Level 1 uses `preserve` and writes the canonical topic membership only.

## Conflicting metadata

Do not silently select one value when DOI, title, creator, date, venue, or publisher records disagree. Record the field, both values, the evidence source, and a status (`Verified`, `Unverified`, or `Awaiting Researcher Decision`). A DOI/publisher lookup can resolve a bibliographic field; it cannot by itself decide the research role or whether two project records should be merged.

## Retired or invalid literature

Create a candidate only when there is objective evidence: retraction/withdrawal notice, superseded version explicitly identified by the publisher, wrong or unresolvable DOI, an exact duplicate with a canonical record, or a documented project-scope decision. Do not use age, venue prestige, citation count, or lack of a local PDF as an invalidity rule. Keep the record and attachments until an approved archive/delete action is completed.

## Taxonomy refactor

A taxonomy rule file should contain `version`, `project_context_sources`, `collections` (key/name/inclusion rule/exclusion rule), `cross_cutting_policy`, `inbox_collection_key`, and `decision_status`. A refactor report should include old/new collection membership per item, items that fit multiple themes, items with no safe theme, count deltas, and unresolved decisions. New or ambiguous items stay in the inbox/review queue.

## Required evidence fields

Every mutation row should include `item_key`, `title`, `before_collections`, `after_collections`, `reason`, `evidence`, `action`, `operator_level`, and `timestamp`. For merge/archive/delete, also include canonical/target key, attachment disposition, and approval reference. Never put the local API key in any of these files.
