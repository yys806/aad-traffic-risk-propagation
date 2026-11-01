---
name: zotero-clean
description: Maintain any research project's Zotero library by classifying inbox items, auditing duplicates and conflicts, and applying approved taxonomy or retirement plans with an auditable index.
metadata:
  short-description: Clean and index Zotero project collections
---

# Zotero clean

Use this skill for any research project's Zotero library. It supports four levels: classifying new inbox items, auditing an entire project, restructuring the project taxonomy, and resolving duplicates or retired/invalid literature under an explicit plan.

## Toolchain and boundary

- Use the Zotero local HTTP API with the existing local authorization key. The default key file is `D:\\hermes\\cache\\zotero-local-key.json`; override it with `ZOTERO_LOCAL_KEY_PATH` when needed. Set `ZOTERO_LOCAL_BASE` or pass `--base` for the target library; do not assume a user/library ID from another project.
- Resolve script and reference paths from the directory containing this `SKILL.md`. The global installation works from any project directory; a repository-local copy is not required.
- Do not use Computer Use, desktop UI automation, direct database access, or Zotero storage-file edits.
- If the local key is missing or expired, stop and report the credential problem; ask the researcher to refresh it through the approved non-UI authorization workflow rather than opening Zotero through Computer Use.
- Read the project facts and the current collection/item state before proposing a move. The project source of truth is the current repository and the live Zotero item metadata.
- Preserve item keys, attachments, notes, tags, metadata, and existing topic memberships. This workflow only adds confirmed destination collections and removes the inbox membership after classification.
- Do not merge, delete, rename, or rewrite items unless the user separately asks for that operation and the affected item keys are listed in an approved plan.
- An old paper is not automatically invalid. Retire a paper only with evidence such as a retraction, a superseding version, a broken or wrong DOI, a confirmed duplicate, or a documented scope decision.

## Operating levels

### Level 1 — inbox classification

Use for `补充文献-未分类` or another named inbox. Read each item, assign one or more existing topic collections, preserve any valid existing memberships, remove only the inbox membership, and export a before/after manifest plus a full project index. This is the default level for routine additions.

### Level 2 — project audit

Inventory all top-level items under the project root and report:

- exact DOI duplicates after case, URL-prefix, and whitespace normalization;
- exact title/author/year matches without a DOI;
- near-duplicate candidates from title, first author, year, and venue;
- metadata conflicts (DOI points to a different title, creator/date disagreement, missing core fields, or publisher record mismatch);
- invalid/retired candidates supported by an explicit source or project decision;
- orphan attachments, notes, and items outside the project scope.

Level 2 is read-only. It produces a candidate report and a proposed action plan; it does not merge, delete, or move records.

The helper audits exact matches and missing-field/status-keyword candidates across the root and all nested collections, including root-only and inbox-only items. Near matches, publisher metadata, retraction evidence, and orphan attachment/note checks require additional read-only API inspection; do not present the helper output as those checks having passed.

### Level 3 — taxonomy refactor

Use when the current topic collections no longer match the live project state. Freeze a versioned taxonomy rule first: collection name, inclusion/exclusion rule, cross-cutting membership rule, and examples. Classify all project items against that rule, show before/after memberships and count changes, then apply only the approved moves. Keep an inbox collection for future additions. Never silently reinterpret a scientific role from a title alone when the project context is ambiguous; mark it `Unverified` and leave it in the review queue.

### Level 4 — duplicate and retirement cleanup

Use only with explicit approval for the listed candidates. For an exact duplicate, choose a canonical item by evidence (complete DOI metadata, stable key, attachments/notes, and project ownership), record both keys, and merge only when the user has authorized merge semantics. The same paper appearing in two project collections is not a reason to delete either record. For a conflict, preserve the conflicting values in the report, prefer the publisher/DOI record only after verification, and do not overwrite an uncertain field. For a retired/invalid candidate, move it to a named review/archive collection or delete it only when the plan explicitly says so; retain the reason, source, item key, and attachment disposition.

## Workflow

1. Inspect the project state and list the target root collection, its topic collections, and the inbox collection.
2. Select the operating level. For Level 2 or deeper, create a read-only audit before any write.
3. Fetch every candidate item by key and classify it from the current project role and the item's title, abstract, DOI metadata, and existing memberships. Keep the classification decision explicit and record a short reason and evidence status.
4. Write a plan JSON containing the root/inbox keys, destination keys, item keys, titles, reasons, duplicate/conflict links, invalidity evidence, and requested action. A Level 1 plan must have at least one destination collection per item.
5. Run `scripts/zotero_clean.py --apply` with a plan. The script uses versioned PATCH requests, removes only the inbox key for Level 1, and stops on a version conflict. Deeper mutation modes must use a separate approved plan and should be implemented as a distinct, reviewable operation.
6. Verify item keys, memberships, collection counts, and attachment/parent relationships. The inbox collection itself remains in place for future arrivals.
7. Export a Markdown/CSV index mapping every project item key to its current project collections, including nested, root-only and inbox-only memberships. Save the before/after manifest and audit reports beside the index in the project's literature-notes directory. List reads are paginated; an invalid root or repeated page is an error, not an empty/complete inventory.

## Classification guidance

Prefer the project's existing topic vocabulary. A paper may have multiple topic memberships when the current project deliberately uses cross-cutting themes; do not collapse those memberships during inbox cleanup. Treat a duplicate item as a separate preserved record during Level 1: place it with the canonical topic and record the duplicate tag/key, without merging or deleting it. Use the deeper duplicate workflow only when the user explicitly authorizes it.

## Reuse

Use the script with a project-specific plan file:

```powershell
$zoteroSkillHome = if ($env:CODEX_HOME) { $env:CODEX_HOME } else { Join-Path $env:USERPROFILE ".codex" }
$zoteroCleanScript = Join-Path $zoteroSkillHome "skills/zotero-clean/scripts/zotero_clean.py"
python $zoteroCleanScript --base "$env:ZOTERO_LOCAL_BASE" --plan path/to/plan.json --apply --manifest path/to/execution.json
python $zoteroCleanScript --base "$env:ZOTERO_LOCAL_BASE" --plan path/to/plan.json --verify
python $zoteroCleanScript --base "$env:ZOTERO_LOCAL_BASE" --export-index --root-key ROOT --inbox-key INBOX --project-name PROJECT --output-dir path/to/literature-notes
python $zoteroCleanScript --base "$env:ZOTERO_LOCAL_BASE" --audit --root-key ROOT --inbox-key INBOX --project-name PROJECT --output-dir path/to/literature-notes
```

The script never prints the local API key and never writes it to a repository file.

For audit and taxonomy decisions, read [references/cleaning-modes.md](references/cleaning-modes.md) before preparing a deeper plan.
